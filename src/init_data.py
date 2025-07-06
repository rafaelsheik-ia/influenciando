"""
Script para inicializar dados padrão no sistema
"""
from src.models.user import db, User, Setting

def init_default_data():
    """Inicializa dados padrão do sistema"""
    
    # Cria usuário admin padrão se não existir
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        print("✓ Usuário admin criado (admin/admin123)")
    
    # Cria usuário de teste se não existir
    test_user = User.query.filter_by(username='user').first()
    if not test_user:
        test_user = User(username='user', role='user')
        test_user.set_password('user123')
        db.session.add(test_user)
        print("✓ Usuário de teste criado (user/user123)")
    
    # Configurações padrão
    default_settings = [
        ('barato_sociais_api_key', '9e0da2b1a6087d34075c123940e7fab5'),
        ('mp_public_key', 'APP_USR-25688d4e-0983-41b0-b4e8-bb5c5c13737d'),
        ('mp_access_token', 'APP_USR-4278668979689090-070320-0c429f571f0cc84734fbf354e55a26fe-1766003359'),
        ('mp_client_id', '4278668979689090'),
        ('mp_client_secret', 'ZjgOAqTY8QUXT4pOpa8erXTOnv2Qc6SO'),
        ('default_profit_margin', '0.2'),
        ('site_name', 'INFLUENCIANDO'),
        ('support_email', 'suporte@influenciando.com'),
        ('webhook_url', '')
    ]
    
    for key, value in default_settings:
        setting = Setting.query.filter_by(key=key).first()
        if not setting:
            setting = Setting(key=key, value=value)
            db.session.add(setting)
            print(f"✓ Configuração criada: {key}")
    
    try:
        db.session.commit()
        print("✓ Dados padrão inicializados com sucesso!")
        return True
    except Exception as e:
        db.session.rollback()
        print(f"✗ Erro ao inicializar dados: {str(e)}")
        return False

if __name__ == '__main__':
    from src.main import app
    with app.app_context():
        init_default_data()

