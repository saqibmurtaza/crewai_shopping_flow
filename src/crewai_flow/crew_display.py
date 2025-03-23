import chainlit as cl

async def display_search_results(state):
    """Helper function to display search results and recommendations consistently."""
    if state.search_results:
        rec_str = "Found products:\n\n"
        for prod in state.search_results:
            rec_str += f"- {prod.get('name', 'N/A')} | Price: ${prod.get('price', 'N/A')}\n"
        
        # Add recommended products if available
        if hasattr(state, 'recommended_products') and state.recommended_products:
            rec_str += "\nYou might also like:\n\n"
            for prod in state.recommended_products:
                rec_str += f"- {prod.get('name', 'N/A')} | Price: ${prod.get('price', 'N/A')}\n"
        
        await cl.Message(content=rec_str).send()
        
        # Always include the follow-up prompt
        prompt = (
            "What would you like to do next?\n"
            "Type 'refine <query>' to refine your search,\n"
            "or 'add <product name>' to add an item to your cart,\n"
            "or 'view cart' to see your cart,\n"
            "or 'checkout' to proceed to checkout."
        )
        await cl.Message(content=prompt).send()
        return True
    else:
        await cl.Message(content="No products found. Please try a different search.").send()
        return False


async def display_cart(cart):
    """Display the current cart contents with cart management options."""
    if not cart:
        await cl.Message(content="Your cart is empty.").send()
        return
    
    cart_str = "Your cart contains:\n\n"
    total = 0
    for item in cart:
        price = float(item.product.get('price', 0))
        cart_str += f"- {item.product.get('name', 'N/A')} | Price: ${price} | Quantity: {item.quantity}\n"
        total += price * item.quantity
    
    cart_str += f"\nTotal: ${total:.2f}"
    
    # Add cart management options
    cart_str += "\n\n📝 Cart Management Options:\n"
    cart_str += "- Update quantity: Type 'update <product name> <quantity>'\n"
    cart_str += "- Remove item: Type 'remove <product name>'\n"
    cart_str += "- Clear cart: Type 'clear cart'\n"
    cart_str += "\nor 'checkout' to proceed to checkout."
    
    await cl.Message(content=cart_str).send()
