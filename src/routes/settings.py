from flask import Blueprint, request, jsonify
from src.models.user import db, Setting
from src.routes.auth import admin_required

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/settings', methods=['GET'])
@admin_required
def get_settings():
    """Obtém todas as configurações"""
    try:
        settings = Setting.query.all()
        settings_dict = {}
        
        for setting in settings:
            # Oculta valores sensíveis (chaves API)
            if 'key' in setting.key.lower() or 'token' in setting.key.lower():
                settings_dict[setting.key] = '***' if setting.value else ''
            else:
                settings_dict[setting.key] = setting.value
        
        return jsonify({'settings': settings_dict}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/settings', methods=['POST'])
@admin_required
def update_settings():
    """Atualiza múltiplas configurações"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        updated_count = 0
        
        for key, value in data.items():
            # Ignora valores mascarados
            if value == '***':
                continue
                
            setting = Setting.query.filter_by(key=key).first()
            
            if setting:
                setting.value = str(value)
            else:
                setting = Setting(key=key, value=str(value))
                db.session.add(setting)
            
            updated_count += 1
        
        db.session.commit()
        
        return jsonify({
            'message': 'Settings updated successfully',
            'updated_count': updated_count
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/settings/<string:key>', methods=['GET'])
@admin_required
def get_setting(key):
    """Obtém uma configuração específica"""
    try:
        setting = Setting.query.filter_by(key=key).first()
        
        if not setting:
            return jsonify({'error': 'Setting not found'}), 404
        
        # Oculta valores sensíveis
        value = setting.value
        if 'key' in key.lower() or 'token' in key.lower():
            value = '***' if value else ''
        
        return jsonify({
            'key': setting.key,
            'value': value
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/settings/<string:key>', methods=['PUT'])
@admin_required
def update_setting(key):
    """Atualiza uma configuração específica"""
    try:
        data = request.get_json()
        value = data.get('value')
        
        if value is None:
            return jsonify({'error': 'Value is required'}), 400
        
        # Ignora valores mascarados
        if value == '***':
            return jsonify({'message': 'Setting not changed (masked value)'}), 200
        
        setting = Setting.query.filter_by(key=key).first()
        
        if setting:
            setting.value = str(value)
        else:
            setting = Setting(key=key, value=str(value))
            db.session.add(setting)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Setting updated successfully',
            'setting': setting.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/settings/<string:key>', methods=['DELETE'])
@admin_required
def delete_setting(key):
    """Remove uma configuração"""
    try:
        setting = Setting.query.filter_by(key=key).first()
        
        if not setting:
            return jsonify({'error': 'Setting not found'}), 404
        
        db.session.delete(setting)
        db.session.commit()
        
        return jsonify({'message': 'Setting deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/settings/test-apis', methods=['POST'])
@admin_required
def test_apis():
    """Testa as configurações das APIs"""
    try:
        from src.services.barato_sociais_api import BaratoSociaisAPI
        from src.services.mercado_pago_api import MercadoPagoAPI
        
        results = {}
        
        # Testa API do Barato Sociais
        barato_key = Setting.query.filter_by(key='barato_sociais_api_key').first()
        if barato_key and barato_key.value:
            try:
                api = BaratoSociaisAPI(barato_key.value)
                balance_response = api.get_balance()
                
                if 'error' in balance_response:
                    results['barato_sociais'] = {'status': 'error', 'message': balance_response['error']}
                else:
                    results['barato_sociais'] = {
                        'status': 'success', 
                        'balance': balance_response.get('balance', 'N/A'),
                        'currency': balance_response.get('currency', 'N/A')
                    }
            except Exception as e:
                results['barato_sociais'] = {'status': 'error', 'message': str(e)}
        else:
            results['barato_sociais'] = {'status': 'not_configured', 'message': 'API key not set'}
        
        # Testa API do Mercado Pago
        mp_token = Setting.query.filter_by(key='mp_access_token').first()
        if mp_token and mp_token.value:
            try:
                # Para testar o MP, tentamos criar uma preferência de teste
                mp_api = MercadoPagoAPI(mp_token.value)
                test_preference = mp_api.create_payment_preference(
                    title="Teste de Configuração",
                    price=1.0,
                    external_reference="test"
                )
                
                if 'error' in test_preference:
                    results['mercado_pago'] = {'status': 'error', 'message': test_preference['error']}
                else:
                    results['mercado_pago'] = {'status': 'success', 'message': 'API configured correctly'}
            except Exception as e:
                results['mercado_pago'] = {'status': 'error', 'message': str(e)}
        else:
            results['mercado_pago'] = {'status': 'not_configured', 'message': 'Access token not set'}
        
        return jsonify({'test_results': results}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

