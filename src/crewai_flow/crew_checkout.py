import stripe, os
from typing import List, Dict, Any

api_key= os.getenv("STRIPE_API_KEY")
stripe.api_key= os.getenv("STRIPE_API_KEY")


# FOR PODUCTION, STRIPE SESSION
# def create_checkout_session(cart_items: List[Dict[str, Any]], success_url: str, cancel_url: str):
#     """
#     Create a Stripe checkout session for the items in the cart.
    
#     Args:
#         cart_items: List of cart items with product information
#         success_url: URL to redirect to after successful payment
#         cancel_url: URL to redirect to if payment is cancelled
        
#     Returns:
#         Checkout session URL
#     """
#     line_items = []
    
#     for item in cart_items:
#         product = item.product
#         line_items.append({
#             'price_data': {
#                 'currency': 'usd',
#                 'product_data': {
#                     'name': product.get('name', 'Unknown Product'),
#                     'description': f"Category: {product.get('category', 'N/A')}",
#                     'images': [product.get('image_url', '')] if product.get('image_url') else [],
#                 },
#                 'unit_amount': int(float(product.get('price', 0)) * 100),  # Convert to cents
#             },
#             'quantity': item.quantity,
#         })
    
#     # Create a checkout session
#     try:
#         checkout_session = stripe.checkout.Session.create(
#             payment_method_types=['card'],
#             line_items=line_items,
#             mode='payment',
#             success_url=success_url,
#             cancel_url=cancel_url,
#         )
#         return checkout_session.url
#     except Exception as e:
#         print(f"Error creating checkout session: {e}")
#         return None

# FOR DEVELOPMENT USE DUMMY SESSION
def create_checkout_session(cart_items: List, success_url: str, cancel_url: str):
    """
    Create a simulated checkout session for development.
    """
    # For development, just return a dummy checkout URL
    # This bypasses the actual Stripe API call
    
    # Build a query string with cart items
    items_param = []
    for item in cart_items:
        product = item.product
        name = product.get('name', 'Unknown')
        price = product.get('price', 0)
        quantity = item.quantity
        items_param.append(f"{name}:{price}:{quantity}")
    
    items_str = ",".join(items_param)
    
    # Create a dummy checkout URL
    checkout_url = f"{success_url}?items={items_str}"
    
    return checkout_url
