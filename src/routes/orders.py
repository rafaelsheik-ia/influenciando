from flask import Blueprint, request, jsonify, session
from src.models.user import db, Order, Service, User
from src.routes.auth import admin_required, login_required
from src.services.barato_sociais_api import BaratoSociaisAPI
from src.services.mercado_pago_api import MercadoPagoAPI
from src.models.user import Setting
from datetime import datetime

orders_bp = Blueprint('orders', __name__)

def get_barato_sociais_api():
    """Obtém uma instância da API do Barato Sociais"""
    api_key_setting = Setting.query.filter_by(key='barato_sociais_api_key').first()
    if not api_key_setting:
        return None
    return BaratoSociaisAPI(api_key_setting.value)

def get_mercado_pago_api():
    """Obtém uma instância da API do Mercado Pago"""
    access_token_setting = Setting.query.filter_by(key='mp_access_token').first()
    if not access_token_setting:
        return None
    return MercadoPagoAPI(access_token_setting.value)

@orders_bp.route('/orders', methods=['GET'])
@login_required
def get_orders():
    """Obtém a lista de pedidos"""
    try:
        user_id = session.get('user_id')
        user = User.query.get(user_id)
        
        if user.role == 'admin':
            # Admin vê todos os pedidos
            orders = Order.query.order_by(Order.created_at.desc()).all()
        else:
            # Usuário comum vê apenas seus pedidos
            orders = Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc()).all()
        
        return jsonify({
            'orders': [order.to_dict() for order in orders]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orders_bp.route('/orders', methods=['POST'])
@login_required
def create_order():
    """Cria um novo pedido"""
    try:
        data = request.get_json()
        service_id = data.get('service_id')
        link = data.get('link')
        quantity = data.get('quantity')
        
        if not all([service_id, link, quantity]):
            return jsonify({'error': 'service_id, link and quantity are required'}), 400
        
        # Verifica se o serviço existe
        service = Service.query.get(service_id)
        if not service:
            return jsonify({'error': 'Service not found'}), 404
        
        # Calcula os preços
        cost_to_us = service.rate * quantity
        price_paid = service.get_final_price() * quantity
        
        # Cria o pedido no banco de dados (inicialmente sem order_id_barato_sociais)
        order = Order(
            user_id=session['user_id'],
            service_id=service_id,
            link=link,
            quantity=quantity,
            price_paid=price_paid,
            cost_to_us=cost_to_us,
            status='Pending Payment'
        )
        
        db.session.add(order)
        db.session.commit()
        
        # Cria a preferência de pagamento no Mercado Pago
        mp_api = get_mercado_pago_api()
        if not mp_api:
            return jsonify({'error': 'Mercado Pago not configured'}), 400
        
        payment_preference = mp_api.create_payment_preference(
            title=f"{service.name} - {quantity} unidades",
            price=price_paid,
            external_reference=str(order.id)
        )
        
        if 'error' in payment_preference:
            return jsonify({'error': payment_preference['error']}), 400
        
        return jsonify({
            'message': 'Order created successfully',
            'order': order.to_dict(),
            'payment_url': payment_preference.get('init_point'),
            'preference_id': payment_preference.get('id')
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@orders_bp.route('/orders/<int:order_id>/process', methods=['POST'])
@admin_required
def process_order(order_id):
    """Processa um pedido (envia para o Barato Sociais)"""
    try:
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        if order.status != 'Paid':
            return jsonify({'error': 'Order must be paid before processing'}), 400
        
        # Obtém a API do Barato Sociais
        api = get_barato_sociais_api()
        if not api:
            return jsonify({'error': 'Barato Sociais API not configured'}), 400
        
        # Cria o pedido no Barato Sociais
        response = api.create_order(
            service_id=order.service.service_id_barato_sociais,
            link=order.link,
            quantity=order.quantity
        )
        
        if 'error' in response:
            return jsonify({'error': response['error']}), 400
        
        # Atualiza o pedido com o ID do Barato Sociais
        order.order_id_barato_sociais = response.get('order')
        order.status = 'Processing'
        order.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Order processed successfully',
            'order': order.to_dict(),
            'barato_sociais_response': response
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@orders_bp.route('/orders/<int:order_id>/status', methods=['GET'])
@login_required
def get_order_status(order_id):
    """Obtém o status atualizado de um pedido"""
    try:
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        # Verifica se o usuário tem permissão para ver este pedido
        user_id = session.get('user_id')
        user = User.query.get(user_id)
        
        if user.role != 'admin' and order.user_id != user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        # Se o pedido tem ID do Barato Sociais, consulta o status
        if order.order_id_barato_sociais:
            api = get_barato_sociais_api()
            if api:
                status_response = api.get_order_status(order.order_id_barato_sociais)
                
                if 'error' not in status_response:
                    # Atualiza o status no banco de dados
                    order.status = status_response.get('status', order.status)
                    order.start_count = status_response.get('start_count', order.start_count)
                    order.remains = status_response.get('remains', order.remains)
                    order.updated_at = datetime.utcnow()
                    
                    db.session.commit()
        
        return jsonify({'order': order.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orders_bp.route('/orders/sync-status', methods=['POST'])
@admin_required
def sync_orders_status():
    """Sincroniza o status de todos os pedidos ativos"""
    try:
        api = get_barato_sociais_api()
        if not api:
            return jsonify({'error': 'Barato Sociais API not configured'}), 400
        
        # Obtém pedidos que têm ID do Barato Sociais e não estão finalizados
        active_orders = Order.query.filter(
            Order.order_id_barato_sociais.isnot(None),
            Order.status.notin_(['Completed', 'Canceled', 'Refunded'])
        ).all()
        
        if not active_orders:
            return jsonify({'message': 'No active orders to sync'}), 200
        
        # Obtém os IDs para consulta em lote
        order_ids = [order.order_id_barato_sociais for order in active_orders]
        
        # Consulta o status em lote
        status_response = api.get_multiple_order_status(order_ids)
        
        if 'error' in status_response:
            return jsonify({'error': status_response['error']}), 400
        
        updated_count = 0
        
        # Atualiza cada pedido
        for order in active_orders:
            order_status = status_response.get(str(order.order_id_barato_sociais))
            if order_status:
                order.status = order_status.get('status', order.status)
                order.start_count = order_status.get('start_count', order.start_count)
                order.remains = order_status.get('remains', order.remains)
                order.updated_at = datetime.utcnow()
                updated_count += 1
        
        db.session.commit()
        
        return jsonify({
            'message': 'Orders status synchronized successfully',
            'updated_count': updated_count
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

