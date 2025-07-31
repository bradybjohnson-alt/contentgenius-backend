from flask import Blueprint, jsonify, request
from src.models.user import db
from src.models.order import Order
from src.models.content import Content
from src.models.content_template import ContentTemplate
from src.routes.auth import token_required, admin_required
from datetime import datetime

order_bp = Blueprint('order', __name__)

@order_bp.route('/orders', methods=['GET'])
@token_required
def get_orders(current_user):
    try:
        if current_user.is_admin:
            orders = Order.query.all()
        else:
            orders = Order.query.filter_by(user_id=current_user.id).all()
        
        return jsonify({
            'orders': [order.to_dict() for order in orders]
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch orders', 'error': str(e)}), 500

@order_bp.route('/orders', methods=['POST'])
@token_required
def create_order(current_user):
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['content_type', 'title']
        for field in required_fields:
            if field not in data:
                return jsonify({'message': f'{field} is required'}), 400
        
        # Get content template for pricing
        template = ContentTemplate.query.filter_by(
            content_type=data['content_type'],
            is_active=True
        ).first()
        
        if not template:
            return jsonify({'message': 'Invalid content type'}), 400
        
        # Calculate price based on word count
        word_count = data.get('word_count', template.default_word_count)
        price = template.base_price * (word_count / template.default_word_count)
        
        # Create new order
        order = Order(
            user_id=current_user.id,
            content_type=data['content_type'],
            title=data['title'],
            description=data.get('description', ''),
            word_count=word_count,
            price=round(price, 2),
            priority=data.get('priority', 'medium')
        )
        
        if data.get('requirements'):
            order.set_requirements(data['requirements'])
        
        db.session.add(order)
        db.session.commit()
        
        return jsonify({
            'message': 'Order created successfully',
            'order': order.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'message': 'Failed to create order', 'error': str(e)}), 500

@order_bp.route('/orders/<int:order_id>', methods=['GET'])
@token_required
def get_order(current_user, order_id):
    try:
        order = Order.query.get_or_404(order_id)
        
        # Check if user owns the order or is admin
        if order.user_id != current_user.id and not current_user.is_admin:
            return jsonify({'message': 'Access denied'}), 403
        
        order_data = order.to_dict()
        
        # Include content if available
        if order.content:
            order_data['content'] = order.content.to_dict()
        
        return jsonify({'order': order_data}), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch order', 'error': str(e)}), 500

@order_bp.route('/orders/<int:order_id>', methods=['PUT'])
@token_required
def update_order(current_user, order_id):
    try:
        order = Order.query.get_or_404(order_id)
        
        # Check if user owns the order or is admin
        if order.user_id != current_user.id and not current_user.is_admin:
            return jsonify({'message': 'Access denied'}), 403
        
        data = request.get_json()
        
        # Update allowed fields
        if 'title' in data:
            order.title = data['title']
        if 'description' in data:
            order.description = data['description']
        if 'requirements' in data:
            order.set_requirements(data['requirements'])
        if 'priority' in data and current_user.is_admin:
            order.priority = data['priority']
        if 'status' in data and current_user.is_admin:
            order.status = data['status']
            if data['status'] == 'completed':
                order.completed_at = datetime.utcnow()
        
        order.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Order updated successfully',
            'order': order.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to update order', 'error': str(e)}), 500

@order_bp.route('/orders/<int:order_id>', methods=['DELETE'])
@token_required
def delete_order(current_user, order_id):
    try:
        order = Order.query.get_or_404(order_id)
        
        # Check if user owns the order or is admin
        if order.user_id != current_user.id and not current_user.is_admin:
            return jsonify({'message': 'Access denied'}), 403
        
        # Only allow deletion if order is pending
        if order.status != 'pending':
            return jsonify({'message': 'Cannot delete order that is not pending'}), 400
        
        db.session.delete(order)
        db.session.commit()
        
        return jsonify({'message': 'Order deleted successfully'}), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to delete order', 'error': str(e)}), 500

@order_bp.route('/content-templates', methods=['GET'])
def get_content_templates():
    try:
        templates = ContentTemplate.query.filter_by(is_active=True).all()
        return jsonify({
            'templates': [template.to_dict() for template in templates]
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch templates', 'error': str(e)}), 500

