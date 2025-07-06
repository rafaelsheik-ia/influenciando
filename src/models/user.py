from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_id_barato_sociais = db.Column(db.Integer, unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    rate = db.Column(db.Float, nullable=False)
    min = db.Column(db.Integer)
    max = db.Column(db.Integer)
    type = db.Column(db.String(50))
    category = db.Column(db.String(100))
    profit_margin = db.Column(db.Float, nullable=False, default=0.2)  # 20% por padrão

    def get_final_price(self):
        return self.rate * (1 + self.profit_margin)

    def to_dict(self):
        return {
            'id': self.id,
            'service_id_barato_sociais': self.service_id_barato_sociais,
            'name': self.name,
            'description': self.description,
            'rate': self.rate,
            'min': self.min,
            'max': self.max,
            'type': self.type,
            'category': self.category,
            'profit_margin': self.profit_margin,
            'final_price': self.get_final_price()
        }

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id_barato_sociais = db.Column(db.Integer, unique=True, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    link = db.Column(db.String(500), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price_paid = db.Column(db.Float, nullable=False)
    cost_to_us = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='Pending')
    start_count = db.Column(db.Integer)
    remains = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos
    user = db.relationship('User', backref=db.backref('orders', lazy=True))
    service = db.relationship('Service', backref=db.backref('orders', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'order_id_barato_sociais': self.order_id_barato_sociais,
            'user_id': self.user_id,
            'service_id': self.service_id,
            'link': self.link,
            'quantity': self.quantity,
            'price_paid': self.price_paid,
            'cost_to_us': self.cost_to_us,
            'status': self.status,
            'start_count': self.start_count,
            'remains': self.remains,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'user': self.user.to_dict() if self.user else None,
            'service': self.service.to_dict() if self.service else None
        }

class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'key': self.key,
            'value': self.value
        }

