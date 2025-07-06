import requests
import json
from urllib.parse import urlencode

class BaratoSociaisAPI:
    def __init__(self, api_key):
        self.api_url = 'https://baratosociais.com/api/v2'
        self.api_key = api_key

    def _make_request(self, data):
        """Faz uma requisição para a API do Barato Sociais"""
        try:
            # Adiciona a chave da API aos dados
            data['key'] = self.api_key
            
            # Converte os dados para formato URL encoded
            encoded_data = urlencode(data)
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'User-Agent': 'Mozilla/4.0 (compatible; MSIE 5.01; Windows NT 5.0)'
            }
            
            response = requests.post(
                self.api_url,
                data=encoded_data,
                headers=headers,
                verify=False,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {'error': f'HTTP {response.status_code}: {response.text}'}
                
        except requests.exceptions.RequestException as e:
            return {'error': f'Request failed: {str(e)}'}
        except json.JSONDecodeError as e:
            return {'error': f'Invalid JSON response: {str(e)}'}

    def get_services(self):
        """Obtém a lista de serviços disponíveis"""
        data = {'action': 'services'}
        return self._make_request(data)

    def get_balance(self):
        """Obtém o saldo da conta"""
        data = {'action': 'balance'}
        return self._make_request(data)

    def create_order(self, service_id, link, quantity, **kwargs):
        """Cria um novo pedido"""
        data = {
            'action': 'add',
            'service': service_id,
            'link': link,
            'quantity': quantity
        }
        
        # Adiciona parâmetros opcionais se fornecidos
        optional_params = ['runs', 'interval', 'comments', 'username', 'min', 'max', 
                          'posts', 'delay', 'expiry', 'old_posts', 'answer_number']
        
        for param in optional_params:
            if param in kwargs:
                data[param] = kwargs[param]
        
        return self._make_request(data)

    def get_order_status(self, order_id):
        """Obtém o status de um pedido específico"""
        data = {
            'action': 'status',
            'order': order_id
        }
        return self._make_request(data)

    def get_multiple_order_status(self, order_ids):
        """Obtém o status de múltiplos pedidos"""
        data = {
            'action': 'status',
            'orders': ','.join(map(str, order_ids))
        }
        return self._make_request(data)

    def refill_order(self, order_id):
        """Solicita reposição de um pedido"""
        data = {
            'action': 'refill',
            'order': order_id
        }
        return self._make_request(data)

    def refill_multiple_orders(self, order_ids):
        """Solicita reposição de múltiplos pedidos"""
        data = {
            'action': 'refill',
            'orders': ','.join(map(str, order_ids))
        }
        return self._make_request(data)

    def get_refill_status(self, refill_id):
        """Obtém o status de uma reposição"""
        data = {
            'action': 'refill_status',
            'refill': refill_id
        }
        return self._make_request(data)

    def get_multiple_refill_status(self, refill_ids):
        """Obtém o status de múltiplas reposições"""
        data = {
            'action': 'refill_status',
            'refills': ','.join(map(str, refill_ids))
        }
        return self._make_request(data)

    def cancel_orders(self, order_ids):
        """Cancela múltiplos pedidos"""
        data = {
            'action': 'cancel',
            'orders': ','.join(map(str, order_ids))
        }
        return self._make_request(data)

