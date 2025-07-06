from flask import Blueprint, jsonify
from src.models.user import db, Order, Service, User
from src.routes.auth import admin_required
from sqlalchemy import func, desc
from datetime import datetime, timedelta

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard/stats', methods=['GET'])
@admin_required
def get_dashboard_stats():
    """Obtém estatísticas gerais para o dashboard"""
    try:
        # Estatísticas básicas
        total_orders = Order.query.count()
        total_users = User.query.count()
        total_services = Service.query.count()
        
        # Receita total
        total_revenue = db.session.query(func.sum(Order.price_paid)).filter(
            Order.status.in_(['Paid', 'Processing', 'Completed'])
        ).scalar() or 0
        
        # Custo total
        total_cost = db.session.query(func.sum(Order.cost_to_us)).filter(
            Order.status.in_(['Paid', 'Processing', 'Completed'])
        ).scalar() or 0
        
        # Lucro total
        total_profit = total_revenue - total_cost
        
        # Pedidos por status
        orders_by_status = db.session.query(
            Order.status,
            func.count(Order.id)
        ).group_by(Order.status).all()
        
        status_stats = {status: count for status, count in orders_by_status}
        
        # Pedidos dos últimos 30 dias
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_orders = Order.query.filter(
            Order.created_at >= thirty_days_ago
        ).count()
        
        # Receita dos últimos 30 dias
        recent_revenue = db.session.query(func.sum(Order.price_paid)).filter(
            Order.created_at >= thirty_days_ago,
            Order.status.in_(['Paid', 'Processing', 'Completed'])
        ).scalar() or 0
        
        return jsonify({
            'total_orders': total_orders,
            'total_users': total_users,
            'total_services': total_services,
            'total_revenue': round(total_revenue, 2),
            'total_cost': round(total_cost, 2),
            'total_profit': round(total_profit, 2),
            'orders_by_status': status_stats,
            'recent_orders_30d': recent_orders,
            'recent_revenue_30d': round(recent_revenue, 2)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/dashboard/sales-chart', methods=['GET'])
@admin_required
def get_sales_chart():
    """Obtém dados para gráfico de vendas dos últimos 30 dias"""
    try:
        # Últimos 30 dias
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        # Vendas por dia
        daily_sales = db.session.query(
            func.date(Order.created_at).label('date'),
            func.count(Order.id).label('orders'),
            func.sum(Order.price_paid).label('revenue')
        ).filter(
            Order.created_at >= thirty_days_ago,
            Order.status.in_(['Paid', 'Processing', 'Completed'])
        ).group_by(func.date(Order.created_at)).order_by('date').all()
        
        chart_data = []
        for sale in daily_sales:
            chart_data.append({
                'date': sale.date.isoformat(),
                'orders': sale.orders,
                'revenue': round(float(sale.revenue or 0), 2)
            })
        
        return jsonify({'sales_chart': chart_data}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/dashboard/top-services', methods=['GET'])
@admin_required
def get_top_services():
    """Obtém os serviços mais vendidos"""
    try:
        top_services = db.session.query(
            Service.name,
            func.count(Order.id).label('order_count'),
            func.sum(Order.price_paid).label('total_revenue')
        ).join(Order).filter(
            Order.status.in_(['Paid', 'Processing', 'Completed'])
        ).group_by(Service.id, Service.name).order_by(
            desc('order_count')
        ).limit(10).all()
        
        services_data = []
        for service in top_services:
            services_data.append({
                'name': service.name,
                'order_count': service.order_count,
                'total_revenue': round(float(service.total_revenue or 0), 2)
            })
        
        return jsonify({'top_services': services_data}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/dashboard/recent-orders', methods=['GET'])
@admin_required
def get_recent_orders():
    """Obtém os pedidos mais recentes"""
    try:
        recent_orders = Order.query.order_by(
            desc(Order.created_at)
        ).limit(10).all()
        
        orders_data = []
        for order in recent_orders:
            orders_data.append({
                'id': order.id,
                'service_name': order.service.name if order.service else 'N/A',
                'user_name': order.user.username if order.user else 'N/A',
                'price_paid': round(order.price_paid, 2),
                'status': order.status,
                'created_at': order.created_at.isoformat() if order.created_at else None
            })
        
        return jsonify({'recent_orders': orders_data}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

