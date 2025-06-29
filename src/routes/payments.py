"""
Stripe payment and subscription management for the SaaS application.

This module handles subscription creation, management, and webhook processing
to ensure users have active subscriptions to access the platform.
"""

import stripe
from flask import Blueprint, request, jsonify, current_app, url_for
from flask_login import login_required, current_user
from src.models.user import User, db
from datetime import datetime, timedelta
import logging
import hmac
import hashlib

logger = logging.getLogger(__name__)

payments_bp = Blueprint('payments', __name__)

def init_stripe():
    """Initialize Stripe with API keys."""
    stripe.api_key = current_app.config.get('STRIPE_SECRET_KEY')

@payments_bp.route('/subscription-plans', methods=['GET'])
def get_subscription_plans():
    """Get available subscription plans."""
    plans = [
        {
            'id': 'basic_monthly',
            'name': 'Basic Monthly',
            'description': 'Full access to crypto analysis and trading tools',
            'price': current_app.config.get('SUBSCRIPTION_PRICE', 2999),  # $29.99
            'currency': current_app.config.get('SUBSCRIPTION_CURRENCY', 'usd'),
            'interval': 'month',
            'features': [
                'AI-powered market analysis',
                'Real-time crypto data',
                'Portfolio optimization',
                'Technical indicators',
                'Risk management tools',
                'API key vault',
                'Email support'
            ]
        },
        {
            'id': 'basic_yearly',
            'name': 'Basic Yearly',
            'description': 'Full access with 2 months free',
            'price': int(current_app.config.get('SUBSCRIPTION_PRICE', 2999) * 10),  # 10 months price
            'currency': current_app.config.get('SUBSCRIPTION_CURRENCY', 'usd'),
            'interval': 'year',
            'features': [
                'All Basic Monthly features',
                '2 months free',
                'Priority support',
                'Advanced analytics'
            ]
        }
    ]
    
    return jsonify({'plans': plans}), 200

@payments_bp.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    """Create Stripe checkout session for subscription."""
    try:
        init_stripe()
        
        data = request.get_json()
        plan_id = data.get('plan_id', 'basic_monthly')
        
        # Determine price based on plan
        if plan_id == 'basic_yearly':
            price = int(current_app.config.get('SUBSCRIPTION_PRICE', 2999) * 10)
            interval = 'year'
        else:
            price = current_app.config.get('SUBSCRIPTION_PRICE', 2999)
            interval = 'month'
        
        # Create or get Stripe customer
        stripe_customer = get_or_create_stripe_customer(current_user)
        
        # Create checkout session
        checkout_session = stripe.checkout.Session.create(
            customer=stripe_customer.id,
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': current_app.config.get('SUBSCRIPTION_CURRENCY', 'usd'),
                    'product_data': {
                        'name': f'Crypto Trading SaaS - {interval.title()}ly',
                        'description': 'AI-powered cryptocurrency trading and analysis platform'
                    },
                    'unit_amount': price,
                    'recurring': {
                        'interval': interval
                    }
                },
                'quantity': 1,
            }],
            mode='subscription',
            success_url=url_for('payments.subscription_success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=url_for('payments.subscription_cancel', _external=True),
            metadata={
                'user_id': current_user.id,
                'plan_id': plan_id
            }
        )
        
        return jsonify({
            'checkout_url': checkout_session.url,
            'session_id': checkout_session.id
        }), 200
        
    except Exception as e:
        logger.error(f"Create checkout session error for user {current_user.id}: {str(e)}")
        return jsonify({'error': 'Failed to create checkout session'}), 500

@payments_bp.route('/subscription-success')
def subscription_success():
    """Handle successful subscription."""
    try:
        session_id = request.args.get('session_id')
        if not session_id:
            return jsonify({'error': 'Session ID required'}), 400
        
        init_stripe()
        
        # Retrieve the checkout session
        session = stripe.checkout.Session.retrieve(session_id)
        
        if session.payment_status == 'paid':
            # Get user from metadata
            user_id = session.metadata.get('user_id')
            user = User.query.get(user_id)
            
            if user:
                # Update user subscription status
                subscription = stripe.Subscription.retrieve(session.subscription)
                
                user.subscription_status = 'active'
                user.subscription_id = subscription.id
                user.subscription_start = datetime.fromtimestamp(subscription.current_period_start)
                user.subscription_end = datetime.fromtimestamp(subscription.current_period_end)
                
                db.session.commit()
                
                logger.info(f"Subscription activated for user {user_id}")
                
                return jsonify({
                    'message': 'Subscription activated successfully!',
                    'subscription_status': 'active',
                    'subscription_end': user.subscription_end.isoformat()
                }), 200
        
        return jsonify({'error': 'Payment not completed'}), 400
        
    except Exception as e:
        logger.error(f"Subscription success error: {str(e)}")
        return jsonify({'error': 'Failed to process subscription'}), 500

@payments_bp.route('/subscription-cancel')
def subscription_cancel():
    """Handle cancelled subscription."""
    return jsonify({
        'message': 'Subscription cancelled',
        'redirect_url': '/pricing'
    }), 200

@payments_bp.route('/subscription-status', methods=['GET'])
@login_required
def get_subscription_status():
    """Get current user's subscription status."""
    try:
        subscription_info = {
            'status': current_user.subscription_status,
            'has_active_subscription': current_user.has_active_subscription(),
            'subscription_start': current_user.subscription_start.isoformat() if current_user.subscription_start else None,
            'subscription_end': current_user.subscription_end.isoformat() if current_user.subscription_end else None,
            'stripe_customer_id': current_user.stripe_customer_id
        }
        
        # Get detailed Stripe subscription info if available
        if current_user.subscription_id:
            try:
                init_stripe()
                subscription = stripe.Subscription.retrieve(current_user.subscription_id)
                subscription_info.update({
                    'stripe_status': subscription.status,
                    'current_period_end': datetime.fromtimestamp(subscription.current_period_end).isoformat(),
                    'cancel_at_period_end': subscription.cancel_at_period_end
                })
            except Exception as stripe_error:
                logger.warning(f"Failed to get Stripe subscription details: {str(stripe_error)}")
        
        return jsonify(subscription_info), 200
        
    except Exception as e:
        logger.error(f"Get subscription status error for user {current_user.id}: {str(e)}")
        return jsonify({'error': 'Failed to get subscription status'}), 500

@payments_bp.route('/cancel-subscription', methods=['POST'])
@login_required
def cancel_subscription():
    """Cancel user's subscription."""
    try:
        if not current_user.subscription_id:
            return jsonify({'error': 'No active subscription found'}), 404
        
        init_stripe()
        
        # Cancel subscription at period end
        subscription = stripe.Subscription.modify(
            current_user.subscription_id,
            cancel_at_period_end=True
        )
        
        logger.info(f"Subscription cancelled for user {current_user.id}")
        
        return jsonify({
            'message': 'Subscription will be cancelled at the end of the current billing period',
            'cancel_at_period_end': subscription.cancel_at_period_end,
            'current_period_end': datetime.fromtimestamp(subscription.current_period_end).isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Cancel subscription error for user {current_user.id}: {str(e)}")
        return jsonify({'error': 'Failed to cancel subscription'}), 500

@payments_bp.route('/reactivate-subscription', methods=['POST'])
@login_required
def reactivate_subscription():
    """Reactivate a cancelled subscription."""
    try:
        if not current_user.subscription_id:
            return jsonify({'error': 'No subscription found'}), 404
        
        init_stripe()
        
        # Reactivate subscription
        subscription = stripe.Subscription.modify(
            current_user.subscription_id,
            cancel_at_period_end=False
        )
        
        logger.info(f"Subscription reactivated for user {current_user.id}")
        
        return jsonify({
            'message': 'Subscription reactivated successfully',
            'cancel_at_period_end': subscription.cancel_at_period_end
        }), 200
        
    except Exception as e:
        logger.error(f"Reactivate subscription error for user {current_user.id}: {str(e)}")
        return jsonify({'error': 'Failed to reactivate subscription'}), 500

@payments_bp.route('/customer-portal', methods=['POST'])
@login_required
def create_customer_portal():
    """Create Stripe customer portal session."""
    try:
        if not current_user.stripe_customer_id:
            return jsonify({'error': 'No customer account found'}), 404
        
        init_stripe()
        
        # Create customer portal session
        portal_session = stripe.billing_portal.Session.create(
            customer=current_user.stripe_customer_id,
            return_url=url_for('payments.get_subscription_status', _external=True)
        )
        
        return jsonify({
            'portal_url': portal_session.url
        }), 200
        
    except Exception as e:
        logger.error(f"Create customer portal error for user {current_user.id}: {str(e)}")
        return jsonify({'error': 'Failed to create customer portal'}), 500

@payments_bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhooks."""
    try:
        payload = request.get_data()
        sig_header = request.headers.get('Stripe-Signature')
        webhook_secret = current_app.config.get('STRIPE_WEBHOOK_SECRET')
        
        if not webhook_secret:
            logger.error("Stripe webhook secret not configured")
            return jsonify({'error': 'Webhook secret not configured'}), 500
        
        # Verify webhook signature
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        except ValueError:
            logger.error("Invalid payload in webhook")
            return jsonify({'error': 'Invalid payload'}), 400
        except stripe.error.SignatureVerificationError:
            logger.error("Invalid signature in webhook")
            return jsonify({'error': 'Invalid signature'}), 400
        
        # Handle the event
        if event['type'] == 'customer.subscription.created':
            handle_subscription_created(event['data']['object'])
        elif event['type'] == 'customer.subscription.updated':
            handle_subscription_updated(event['data']['object'])
        elif event['type'] == 'customer.subscription.deleted':
            handle_subscription_deleted(event['data']['object'])
        elif event['type'] == 'invoice.payment_succeeded':
            handle_payment_succeeded(event['data']['object'])
        elif event['type'] == 'invoice.payment_failed':
            handle_payment_failed(event['data']['object'])
        else:
            logger.info(f"Unhandled webhook event type: {event['type']}")
        
        return jsonify({'status': 'success'}), 200
        
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return jsonify({'error': 'Webhook processing failed'}), 500

def get_or_create_stripe_customer(user):
    """Get or create Stripe customer for user."""
    if user.stripe_customer_id:
        try:
            return stripe.Customer.retrieve(user.stripe_customer_id)
        except stripe.error.InvalidRequestError:
            # Customer doesn't exist, create new one
            pass
    
    # Create new customer
    customer = stripe.Customer.create(
        email=user.email,
        name=user.get_full_name(),
        metadata={
            'user_id': user.id
        }
    )
    
    # Update user with customer ID
    user.stripe_customer_id = customer.id
    db.session.commit()
    
    return customer

def handle_subscription_created(subscription):
    """Handle subscription created webhook."""
    try:
        customer_id = subscription['customer']
        user = User.query.filter_by(stripe_customer_id=customer_id).first()
        
        if user:
            user.subscription_status = 'active'
            user.subscription_id = subscription['id']
            user.subscription_start = datetime.fromtimestamp(subscription['current_period_start'])
            user.subscription_end = datetime.fromtimestamp(subscription['current_period_end'])
            db.session.commit()
            
            logger.info(f"Subscription created for user {user.id}")
    except Exception as e:
        logger.error(f"Handle subscription created error: {str(e)}")

def handle_subscription_updated(subscription):
    """Handle subscription updated webhook."""
    try:
        customer_id = subscription['customer']
        user = User.query.filter_by(stripe_customer_id=customer_id).first()
        
        if user:
            user.subscription_status = subscription['status']
            user.subscription_end = datetime.fromtimestamp(subscription['current_period_end'])
            db.session.commit()
            
            logger.info(f"Subscription updated for user {user.id}: {subscription['status']}")
    except Exception as e:
        logger.error(f"Handle subscription updated error: {str(e)}")

def handle_subscription_deleted(subscription):
    """Handle subscription deleted webhook."""
    try:
        customer_id = subscription['customer']
        user = User.query.filter_by(stripe_customer_id=customer_id).first()
        
        if user:
            user.subscription_status = 'cancelled'
            db.session.commit()
            
            logger.info(f"Subscription deleted for user {user.id}")
    except Exception as e:
        logger.error(f"Handle subscription deleted error: {str(e)}")

def handle_payment_succeeded(invoice):
    """Handle successful payment webhook."""
    try:
        customer_id = invoice['customer']
        user = User.query.filter_by(stripe_customer_id=customer_id).first()
        
        if user and user.subscription_status != 'active':
            user.subscription_status = 'active'
            db.session.commit()
            
            logger.info(f"Payment succeeded for user {user.id}")
    except Exception as e:
        logger.error(f"Handle payment succeeded error: {str(e)}")

def handle_payment_failed(invoice):
    """Handle failed payment webhook."""
    try:
        customer_id = invoice['customer']
        user = User.query.filter_by(stripe_customer_id=customer_id).first()
        
        if user:
            user.subscription_status = 'past_due'
            db.session.commit()
            
            logger.info(f"Payment failed for user {user.id}")
    except Exception as e:
        logger.error(f"Handle payment failed error: {str(e)}")

