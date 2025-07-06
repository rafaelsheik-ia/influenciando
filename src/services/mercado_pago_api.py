import requests
import json
from datetime import datetime, timedelta

class MercadoPagoAPI:
    def __init__(self, access_token):
        self.access_token = access_token
        self.base_url = 'https://api.mercadopago.com'

    def create_payment_preference(self, title, price, quantity=1, external_reference=None):
        """Cria uma preferência de pagamento no Mercado Pago"""
        url = f"{self.base_url}/checkout/preferences"
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        # Calcula data de expiração (7 dias a partir de agora)
        expiration_date = datetime.now() + timedelta(days=7)
        
        data = {
            "items": [
                {
                    "title": title,
                    "quantity": quantity,
                    "unit_price": float(price),
                    "currency_id": "BRL"
                }
            ],
            "payment_methods": {
                "excluded_payment_types": [],
                "installments": 12
            },
            "back_urls": {
                "success": "https://seu-site.com/success",
                "failure": "https://seu-site.com/failure",
                "pending": "https://seu-site.com/pending"
            },
            "auto_return": "approved",
            "notification_url": "https://seu-site.com/webhook/mercadopago",
            "expires": True,
            "expiration_date_from": datetime.now().isoformat(),
            "expiration_date_to": expiration_date.isoformat()
        }
        
        if external_reference:
            data["external_reference"] = str(external_reference)
        
        try:
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 201:
                return response.json()
            else:
                return {'error': f'HTTP {response.status_code}: {response.text}'}
                
        except requests.exceptions.RequestException as e:
            return {'error': f'Request failed: {str(e)}'}

    def get_payment_info(self, payment_id):
        """Obtém informações de um pagamento específico"""
        url = f"{self.base_url}/v1/payments/{payment_id}"
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {'error': f'HTTP {response.status_code}: {response.text}'}
                
        except requests.exceptions.RequestException as e:
            return {'error': f'Request failed: {str(e)}'}

    def get_preference_info(self, preference_id):
        """Obtém informações de uma preferência específica"""
        url = f"{self.base_url}/checkout/preferences/{preference_id}"
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {'error': f'HTTP {response.status_code}: {response.text}'}
                
        except requests.exceptions.RequestException as e:
            return {'error': f'Request failed: {str(e)}'}

    def process_webhook_notification(self, notification_data):
        """Processa uma notificação de webhook do Mercado Pago"""
        try:
            # Verifica se é uma notificação de pagamento
            if notification_data.get('type') == 'payment':
                payment_id = notification_data.get('data', {}).get('id')
                if payment_id:
                    return self.get_payment_info(payment_id)
            
            return {'error': 'Invalid notification type'}
            
        except Exception as e:
            return {'error': f'Webhook processing failed: {str(e)}'}

