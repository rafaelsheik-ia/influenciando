from flask import Blueprint, request, jsonify
from src.models.user import db, Order, Setting
from src.services.mercado_pago_api import MercadoPagoAPI
from datetime import datetime

webhooks_bp = Blueprint('webhooks', __name__)

def get_mercado_pago_api():
    """Obtém uma instância da API do Mercado Pago"""
    access_token_setting = Setting.query.filter_by(key='mp_access_token').first()
    if not access_token_setting:
        return None
    return MercadoPagoAPI(access_token_setting.value)

@webhooks_bp.route('/mercadopago', methods=['POST'])
def mercadopago_webhook():
    """Webhook para receber notificações do Mercado Pago"""
    try:
        # Obtém os dados da notificação
        notification_data = request.get_json()
        
        if not notification_data:
            return jsonify({'error': 'No data received'}), 400
        
        # Verifica se é uma notificação de pagamento
        if notification_data.get('type') != 'payment':
            return jsonify({'message': 'Notification type not handled'}), 200
        
        # Obtém o ID do pagamento
        payment_id = notification_data.get('data', {}).get('id')
        if not payment_id:
            return jsonify({'error': 'Payment ID not found'}), 400
        
        # Obtém a API do Mercado Pago
        mp_api = get_mercado_pago_api()
        if not mp_api:
            return jsonify({'error': 'Mercado Pago API not configured'}), 500
        
        # Consulta as informações do pagamento
        payment_info = mp_api.get_payment_info(payment_id)
        
        if 'error' in payment_info:
            return jsonify({'error': payment_info['error']}), 400
        
        # Obtém a referência externa (ID do pedido)
        external_reference = payment_info.get('external_reference')
        if not external_reference:
            return jsonify({'error': 'External reference not found'}), 400
        
        # Busca o pedido no banco de dados
        order = Order.query.get(int(external_reference))
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        # Atualiza o status do pedido baseado no status do pagamento
        payment_status = payment_info.get('status')
        
        if payment_status == 'approved':
            order.status = 'Paid'
        elif payment_status == 'rejected':
            order.status = 'Payment Rejected'
        elif payment_status == 'cancelled':
            order.status = 'Payment Cancelled'
        elif payment_status == 'pending':
            order.status = 'Pending Payment'
        elif payment_status == 'in_process':
            order.status = 'Payment Processing'
        elif payment_status == 'refunded':
            order.status = 'Refunded'
        else:
            order.status = f'Payment {payment_status}'
        
        order.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Webhook processed successfully',
            'order_id': order.id,
            'new_status': order.status
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@webhooks_bp.route('/test-webhook', methods=['POST'])
def test_webhook():
    """Endpoint para testar o webhook (apenas para desenvolvimento)"""
    try:
        data = request.get_json()
        
        return jsonify({
            'message': 'Test webhook received',
            'data': data
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

