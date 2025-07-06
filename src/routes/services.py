from flask import Blueprint, request, jsonify
from src.models.user import db, Service, Setting
from src.routes.auth import admin_required, login_required
from src.services.barato_sociais_api import BaratoSociaisAPI

services_bp = Blueprint('services', __name__)

def get_barato_sociais_api():
    """Obtém uma instância da API do Barato Sociais com a chave configurada"""
    api_key_setting = Setting.query.filter_by(key='barato_sociais_api_key').first()
    if not api_key_setting:
        return None
    return BaratoSociaisAPI(api_key_setting.value)

@services_bp.route('/services', methods=['GET'])
@login_required
def get_services():
    """Obtém a lista de serviços disponíveis"""
    try:
        services = Service.query.all()
        return jsonify({
            'services': [service.to_dict() for service in services]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@services_bp.route('/services/sync', methods=['POST'])
@admin_required
def sync_services():
    """Sincroniza os serviços com a API do Barato Sociais"""
    try:
        api = get_barato_sociais_api()
        if not api:
            return jsonify({'error': 'Barato Sociais API key not configured'}), 400
        
        # Obtém os serviços da API
        response = api.get_services()
        
        if 'error' in response:
            return jsonify({'error': response['error']}), 400
        
        # Atualiza ou cria serviços no banco de dados
        updated_count = 0
        created_count = 0
        
        for service_data in response:
            service_id = service_data.get('service')
            
            # Verifica se o serviço já existe
            existing_service = Service.query.filter_by(
                service_id_barato_sociais=service_id
            ).first()
            
            if existing_service:
                # Atualiza serviço existente
                existing_service.name = service_data.get('name', '')
                existing_service.description = service_data.get('description', '')
                existing_service.rate = float(service_data.get('rate', 0))
                existing_service.min = service_data.get('min')
                existing_service.max = service_data.get('max')
                existing_service.type = service_data.get('type', '')
                existing_service.category = service_data.get('category', '')
                updated_count += 1
            else:
                # Cria novo serviço
                new_service = Service(
                    service_id_barato_sociais=service_id,
                    name=service_data.get('name', ''),
                    description=service_data.get('description', ''),
                    rate=float(service_data.get('rate', 0)),
                    min=service_data.get('min'),
                    max=service_data.get('max'),
                    type=service_data.get('type', ''),
                    category=service_data.get('category', ''),
                    profit_margin=0.2  # 20% de margem padrão
                )
                db.session.add(new_service)
                created_count += 1
        
        db.session.commit()
        
        return jsonify({
            'message': 'Services synchronized successfully',
            'created': created_count,
            'updated': updated_count
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@services_bp.route('/services/<int:service_id>', methods=['PUT'])
@admin_required
def update_service(service_id):
    """Atualiza um serviço específico (principalmente a margem de lucro)"""
    try:
        service = Service.query.get(service_id)
        if not service:
            return jsonify({'error': 'Service not found'}), 404
        
        data = request.get_json()
        
        # Atualiza apenas campos permitidos
        if 'profit_margin' in data:
            service.profit_margin = float(data['profit_margin'])
        
        if 'name' in data:
            service.name = data['name']
        
        if 'description' in data:
            service.description = data['description']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Service updated successfully',
            'service': service.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@services_bp.route('/services/<int:service_id>', methods=['GET'])
@login_required
def get_service(service_id):
    """Obtém um serviço específico"""
    try:
        service = Service.query.get(service_id)
        if not service:
            return jsonify({'error': 'Service not found'}), 404
        
        return jsonify({'service': service.to_dict()}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@services_bp.route('/services/categories', methods=['GET'])
@login_required
def get_categories():
    """Obtém as categorias de serviços disponíveis"""
    try:
        categories = db.session.query(Service.category).distinct().all()
        category_list = [cat[0] for cat in categories if cat[0]]
        
        return jsonify({'categories': category_list}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

