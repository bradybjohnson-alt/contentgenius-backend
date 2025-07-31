from flask import Blueprint, jsonify, request
from src.models.user import db
from src.models.order import Order
from src.models.content import Content
from src.routes.auth import token_required, admin_required
from src.services.content_generator import ContentGenerator
import threading

content_bp = Blueprint('content', __name__)
content_generator = ContentGenerator()

@content_bp.route('/generate/<int:order_id>', methods=['POST'])
@token_required
def generate_content(current_user, order_id):
    """Generate content for a specific order"""
    try:
        # Get the order
        order = Order.query.get_or_404(order_id)
        
        # Check if user owns the order or is admin
        if order.user_id != current_user.id and not current_user.is_admin:
            return jsonify({'message': 'Access denied'}), 403
        
        # Check if order is in correct status
        if order.status not in ['pending', 'in_progress']:
            return jsonify({'message': 'Order cannot be processed in current status'}), 400
        
        # Update order status to in_progress
        order.status = 'in_progress'
        db.session.commit()
        
        # Generate content in background (for demo, we'll do it synchronously)
        result = content_generator.generate_content(order_id)
        
        if result['success']:
            return jsonify({
                'message': 'Content generated successfully',
                'content': result['content'],
                'order': result['order']
            }), 200
        else:
            # Revert order status on failure
            order.status = 'pending'
            db.session.commit()
            return jsonify({
                'message': 'Content generation failed',
                'error': result['error']
            }), 500
            
    except Exception as e:
        return jsonify({'message': 'Content generation failed', 'error': str(e)}), 500

@content_bp.route('/preview', methods=['POST'])
@token_required
def preview_content(current_user):
    """Generate a preview of content without creating an order"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['content_type', 'title']
        for field in required_fields:
            if field not in data:
                return jsonify({'message': f'{field} is required'}), 400
        
        result = content_generator.preview_content(
            content_type=data['content_type'],
            title=data['title'],
            description=data.get('description', ''),
            requirements=data.get('requirements', {})
        )
        
        if result['success']:
            return jsonify({
                'message': 'Preview generated successfully',
                'preview': result['preview']
            }), 200
        else:
            return jsonify({
                'message': 'Preview generation failed',
                'error': result['error']
            }), 500
            
    except Exception as e:
        return jsonify({'message': 'Preview generation failed', 'error': str(e)}), 500

@content_bp.route('/content/<int:order_id>', methods=['GET'])
@token_required
def get_content(current_user, order_id):
    """Get generated content for an order"""
    try:
        order = Order.query.get_or_404(order_id)
        
        # Check if user owns the order or is admin
        if order.user_id != current_user.id and not current_user.is_admin:
            return jsonify({'message': 'Access denied'}), 403
        
        if not order.content:
            return jsonify({'message': 'No content found for this order'}), 404
        
        return jsonify({
            'content': order.content.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch content', 'error': str(e)}), 500

@content_bp.route('/content/<int:content_id>/approve', methods=['POST'])
@token_required
def approve_content(current_user, content_id):
    """Approve generated content"""
    try:
        content = Content.query.get_or_404(content_id)
        order = content.order
        
        # Check if user owns the order or is admin
        if order.user_id != current_user.id and not current_user.is_admin:
            return jsonify({'message': 'Access denied'}), 403
        
        content.is_approved = True
        db.session.commit()
        
        return jsonify({
            'message': 'Content approved successfully',
            'content': content.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to approve content', 'error': str(e)}), 500

@content_bp.route('/content/<int:content_id>/revise', methods=['POST'])
@token_required
def request_revision(current_user, content_id):
    """Request revision for generated content"""
    try:
        content = Content.query.get_or_404(content_id)
        order = content.order
        
        # Check if user owns the order or is admin
        if order.user_id != current_user.id and not current_user.is_admin:
            return jsonify({'message': 'Access denied'}), 403
        
        data = request.get_json()
        revision_notes = data.get('revision_notes', '')
        
        # Increment revision count
        content.revision_count += 1
        content.is_approved = False
        
        # Update order status back to in_progress
        order.status = 'in_progress'
        
        # Add revision notes to order requirements
        requirements = order.get_requirements()
        requirements['revision_notes'] = revision_notes
        order.set_requirements(requirements)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Revision requested successfully',
            'content': content.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to request revision', 'error': str(e)}), 500

@content_bp.route('/admin/regenerate/<int:order_id>', methods=['POST'])
@token_required
@admin_required
def admin_regenerate_content(current_user, order_id):
    """Admin endpoint to regenerate content for any order"""
    try:
        order = Order.query.get_or_404(order_id)
        
        # Delete existing content if any
        if order.content:
            db.session.delete(order.content)
        
        # Reset order status
        order.status = 'in_progress'
        db.session.commit()
        
        # Generate new content
        result = content_generator.generate_content(order_id)
        
        if result['success']:
            return jsonify({
                'message': 'Content regenerated successfully',
                'content': result['content'],
                'order': result['order']
            }), 200
        else:
            return jsonify({
                'message': 'Content regeneration failed',
                'error': result['error']
            }), 500
            
    except Exception as e:
        return jsonify({'message': 'Content regeneration failed', 'error': str(e)}), 500

