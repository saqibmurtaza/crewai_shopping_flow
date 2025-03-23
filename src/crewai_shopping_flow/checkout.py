import stripe
from typing import List, Dict, Any

def create_checkout_session(cart_items: List[Dict[str, Any]], success_url: str, cancel_url: str):
    """
    Create a Stripe checkout session for the items in the cart.
    
    Args:
        cart_items: List of cart items with product information
        success_url: URL to redirect to after successful payment
        cancel_url: URL to redirect to if payment is cancelled
        
    Returns:
        Checkout session URL
    """
    line_items = []
    
    for item in cart_items:
        product = item.product
        line_items.append({
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': product.get('name', 'Unknown Product'),
                    'description': f"Category: {product.get('category', 'N/A')}",
                    'images': [product.get('image_url', '')] if product.get('image_url') else [],
                },
                'unit_amount': int(float(product.get('price', 0)) * 100),  # Convert to cents
            },
            'quantity': item.quantity,
        })
    
    # Create a checkout session
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
        )
        return checkout_session.url
    except Exception as e:
        print(f"Error creating checkout session: {e}")
        return None
