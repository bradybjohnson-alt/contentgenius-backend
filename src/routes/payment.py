from flask import Blueprint, jsonify, request
from src.models.user import db
from src.models.order import Order
from src.models.payment import Payment
from src.routes.auth import token_required
from datetime import datetime
import uuid

payment_bp = Blueprint('payment', __name__)

@payment_bp.route('/create-payment-intent', methods=['POST'])
@token_required
def create_payment_intent(current_user):
    """Create a payment intent for an order"""
    try:
        data = request.get_json()
        order_id = data.get('order_id')
        
        if not order_id:
            return jsonify({'message': 'Order ID is required'}), 400
        
        order = Order.query.get_or_404(order_id)
        
        # Check if user owns the order
        if order.user_id != current_user.id:
            return jsonify({'message': 'Access denied'}), 403
        
        # Check if order already has a payment
        existing_payment = Payment.query.filter_by(order_id=order_id, status='completed').first()
        if existing_payment:
            return jsonify({'message': 'Order already paid'}), 400
        
        # For demo purposes, we'll simulate Stripe payment intent creation
        # In a real application, you would use Stripe's API here
        payment_intent_id = f"pi_demo_{uuid.uuid4().hex[:16]}"
        
        # Create a pending payment record
        payment = Payment(
            user_id=current_user.id,
            order_id=order_id,
            amount=order.price,
            currency='USD',
            payment_method='card',
            stripe_payment_id=payment_intent_id,
            status='pending'
        )
        
        db.session.add(payment)
        db.session.commit()
        
        return jsonify({
            'payment_intent_id': payment_intent_id,
            'client_secret': f"{payment_intent_id}_secret_demo",
            'amount': order.price,
            'currency': 'USD',
            'payment_id': payment.id
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to create payment intent', 'error': str(e)}), 500

@payment_bp.route('/confirm-payment', methods=['POST'])
@token_required
def confirm_payment(current_user):
    """Confirm a payment (simulate Stripe webhook)"""
    try:
        data = request.get_json()
        payment_intent_id = data.get('payment_intent_id')
        
        if not payment_intent_id:
            return jsonify({'message': 'Payment intent ID is required'}), 400
        
        # Find the payment record
        payment = Payment.query.filter_by(stripe_payment_id=payment_intent_id).first()
        if not payment:
            return jsonify({'message': 'Payment not found'}), 404
        
        # Check if user owns the payment
        if payment.user_id != current_user.id:
            return jsonify({'message': 'Access denied'}), 403
        
        # For demo purposes, we'll always simulate successful payment
        # In a real application, you would verify the payment with Stripe
        payment.status = 'completed'
        payment.updated_at = datetime.utcnow()
        
        # Update the order status to trigger content generation
        order = payment.order
        if order.status == 'pending':
            order.status = 'in_progress'
            order.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Trigger content generation (in a real app, this would be async)
        from src.services.content_generator import ContentGenerator
        content_generator = ContentGenerator()
        
        # Generate content automatically after payment
        generation_result = content_generator.generate_content(order.id)
        
        return jsonify({
            'message': 'Payment confirmed successfully',
            'payment': payment.to_dict(),
            'order': order.to_dict(),
            'content_generated': generation_result['success']
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to confirm payment', 'error': str(e)}), 500

@payment_bp.route('/payment-history', methods=['GET'])
@token_required
def get_payment_history(current_user):
    """Get payment history for the current user"""
    try:
        payments = Payment.query.filter_by(user_id=current_user.id).order_by(Payment.created_at.desc()).all()
        
        return jsonify({
            'payments': [payment.to_dict() for payment in payments]
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch payment history', 'error': str(e)}), 500

@payment_bp.route('/payment/<int:payment_id>', methods=['GET'])
@token_required
def get_payment(current_user, payment_id):
    """Get details of a specific payment"""
    try:
        payment = Payment.query.get_or_404(payment_id)
        
        # Check if user owns the payment or is admin
        if payment.user_id != current_user.id and not current_user.is_admin:
            return jsonify({'message': 'Access denied'}), 403
        
        return jsonify({
            'payment': payment.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch payment', 'error': str(e)}), 500

@payment_bp.route('/refund/<int:payment_id>', methods=['POST'])
@token_required
def request_refund(current_user, payment_id):
    """Request a refund for a payment"""
    try:
        payment = Payment.query.get_or_404(payment_id)
        
        # Check if user owns the payment
        if payment.user_id != current_user.id:
            return jsonify({'message': 'Access denied'}), 403
        
        # Check if payment can be refunded
        if payment.status != 'completed':
            return jsonify({'message': 'Only completed payments can be refunded'}), 400
        
        # For demo purposes, we'll simulate refund processing
        # In a real application, you would use Stripe's refund API
        payment.status = 'refunded'
        payment.updated_at = datetime.utcnow()
        
        # Update order status
        order = payment.order
        order.status = 'cancelled'
        order.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Refund processed successfully',
            'payment': payment.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to process refund', 'error': str(e)}), 500

@payment_bp.route('/admin/payments', methods=['GET'])
@token_required
def admin_get_all_payments(current_user):
    """Admin endpoint to get all payments"""
    if not current_user.is_admin:
        return jsonify({'message': 'Admin access required'}), 403
    
    try:
        payments = Payment.query.order_by(Payment.created_at.desc()).all()
        
        return jsonify({
            'payments': [payment.to_dict() for payment in payments]
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch payments', 'error': str(e)}), 500

