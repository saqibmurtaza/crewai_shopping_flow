import chainlit as cl, json, stripe
from crewai_flow.crew_state import ShoppingState, CartItem
from crewai_flow.crew_checkout import create_checkout_session
from crewai_flow.crews.shopping_crew.shopping_crew import ShoppingCrew
from crewai_flow.crew_display import display_search_results, display_cart

class ShoppingFlow:
    def __init__(self):
        self.state = ShoppingState()
    
    async def search_products(self):
        print(f"DEBUG: Searching for products matching '{self.state.user_query}'...")
        # Kick off the search using the crew, passing the user's query.
        crew_output = ShoppingCrew().crew().kickoff(
            inputs={
                "query": self.state.user_query
            }
        )
        
        # Accessing the crew output
        desired_output = None

        for task_output in crew_output.tasks_output:
            raw_str = task_output.raw
            json_str = raw_str
            
            # Handle potential markdown code blocks
            if "```" in raw_str:
                parts = raw_str.split("```")
                if len(parts) >= 3:
                    json_str = parts[1]
                    if json_str.startswith("json\n"):
                        json_str = json_str[5:]
                else:
                    json_str = raw_str.split("```")[0].strip()
            
            try:
                parsed = json.loads(json_str)
                print(f"DEBUG: PARSED {parsed}")
                if isinstance(parsed, dict) and "products" in parsed:
                    desired_output = parsed
                    break
            except json.JSONDecodeError:
                continue

        if desired_output:
            print("Extracted JSON:", json.dumps(desired_output, indent=2))
            self.state.search_results = desired_output["products"]
            # Also store recommended products if available
            self.state.recommended_products = desired_output.get("recommended_products", [])
        else:
            print("No valid JSON output with 'products' key was found.")
            self.state.search_results = []
            self.state.recommended_products = []
    
    # # FOR PRODUCTTION
    # async def handle_checkout(self):
    #     """Process checkout using Stripe"""
    #     if not self.state.cart:
    #         await cl.Message(content="Your cart is empty. Add some products before checkout.").send()
    #         return
        
    #     # For development, use localhost URLs
    #     base_url = "http://localhost:8000"  # Adjust if your app runs on a different port
    #     success_url = f"{base_url}/checkout/success"
    #     cancel_url = f"{base_url}/checkout/cancel"
        
    #     # Create checkout session
    #     checkout_url = create_checkout_session(
    #         self.state.cart, 
    #         success_url=success_url,
    #         cancel_url=cancel_url
    #     )
        
    #     if checkout_url:
    #         # In a real app, you might redirect the user
    #         # For Chainlit, we'll provide a link
    #         message = (
    #             "## Proceed to Checkout\n\n"
    #             f"[Click here to complete your purchase]({checkout_url})\n\n"
    #             "This is a test checkout. You can use these test card numbers:\n"
    #             "- Success: 4242 4242 4242 4242\n"
    #             "- Decline: 4000 0000 0000 0002\n\n"
    #             "Use any future expiration date, any 3-digit CVC, and any postal code."
    #         )
    #         await cl.Message(content=message).send()
            
    #         # Update checkout status
    #         self.state.checkout_status = "Initiated"
    #     else:
    #         # More detailed error message
    #         if not stripe.api_key:
    #             await cl.Message(content="Checkout failed: Stripe API key is not configured. Please set up your Stripe API key.").send()
    #         else:
    #             await cl.Message(content="Sorry, we couldn't create a checkout session. Please try again later.").send()
    
    # FOR DEVELOPMENT
    async def handle_checkout(self):
        """Process checkout using a simulated checkout flow"""
        if not self.state.cart:
            await cl.Message(content="Your cart is empty. Add some products before checkout.").send()
            return
        
        # For development, use localhost URLs
        base_url = "http://localhost:8000"  # Adjust if your app runs on a different port
        success_url = f"{base_url}/checkout/success"
        cancel_url = f"{base_url}/checkout/cancel"
        
        # Create checkout session
        checkout_url = create_checkout_session(
            self.state.cart, 
            success_url=success_url,
            cancel_url=cancel_url
        )
        
        if checkout_url:
            # For development, simulate a successful checkout
            self.state.checkout_status = "Completed"
            
            # Calculate total
            total = sum(float(item.product.get('price', 0)) * item.quantity for item in self.state.cart)
            
            # Display checkout confirmation
            message = (
                "## 🎉 Order Confirmed!\n\n"
                "Thank you for your purchase! Your order has been processed successfully.\n\n"
                "**Order Summary:**\n"
            )
            
            for item in self.state.cart:
                product = item.product
                price = float(product.get('price', 0))
                quantity = item.quantity
                message += f"- {product.get('name')}: ${price} × {quantity} = ${price * quantity}\n"
            
            message += f"\n**Total: ${total:.2f}**\n\n"
            message += "Your order will be processed and shipped soon."
            
            await cl.Message(content=message).send()
            
            # Clear the cart
            self.state.cart = []
        else:
            await cl.Message(content="Sorry, we couldn't process your checkout. Please try again.").send()

    async def interaction_agent(self, message):
        user_action = message.content.lower().strip()
        
        if user_action.startswith("refine"):
            # Split the message into parts and join everything after "refine"
            parts = user_action.split(maxsplit=1)
            if len(parts) < 2:
                await cl.Message(content="Please specify what you want to search for after 'refine'.").send()
                return
            refined_query = parts[1].strip()
            self.state.user_query = refined_query
            await cl.Message(content=f"Refining search for '{refined_query}'...").send()
            await self.search_products()
            await display_search_results(self.state)

        elif user_action.startswith("add"):
            parts = user_action.split(maxsplit=1)
            if len(parts) < 2:
                await cl.Message(content="Please specify which product to add.").send()
                # Show all available products
                all_products = list(self.state.search_results)
                if hasattr(self.state, 'recommended_products') and self.state.recommended_products:
                    all_products.extend(self.state.recommended_products)
                if hasattr(self.state, 'previous_results') and self.state.previous_results:
                    all_products.extend([p for p in self.state.previous_results 
                                        if p not in self.state.search_results])
                rec_str = "\nAvailable products:\n"
                for prod in all_products:
                    rec_str += f"- {prod.get('name', 'N/A')} | Price: ${prod.get('price', 'N/A')}\n"
                await cl.Message(content=rec_str).send()
            else:
                prod_name = parts[1].strip().lower()
                # Search in current results, recommended products, and previous results
                all_products = list(self.state.search_results)
                if hasattr(self.state, 'recommended_products') and self.state.recommended_products:
                    all_products.extend(self.state.recommended_products)
                if hasattr(self.state, 'previous_results') and self.state.previous_results:
                    all_products.extend([p for p in self.state.previous_results 
                                        if p not in self.state.search_results])
                matching_item = next(
                    (p for p in all_products 
                    if prod_name in p.get("name", "").lower() or 
                    p.get("name", "").lower() in prod_name),
                    None
                )
                if matching_item:
                    # Check if the item is already in the cart
                    existing_item = next(
                        (item for item in self.state.cart 
                        if item.product.get("name") == matching_item.get("name")),
                        None
                    )
                    
                    if existing_item:
                        # Update quantity if item already exists
                        existing_item.quantity += 1
                        await cl.Message(content=f"Added another {matching_item.get('name')} to your cart (Quantity: {existing_item.quantity}).").send()
                    else:
                        # Add new item if it doesn't exist
                        self.state.cart.append(CartItem(product=matching_item))
                        await cl.Message(content=f"{matching_item.get('name')} has been added to your cart.").send()
                    
                    await display_cart(self.state.cart)
                    
                    # Add follow-up prompt after adding to cart
                    prompt = (
                        "What would you like to do next?\n"
                        "Type 'refine <query>' to refine your search,\n"
                        "or 'add <product name>' to add another item to your cart,\n"
                        "or 'view cart' to see your cart,\n"
                        "or 'checkout' to proceed to checkout."
                    )
                    await cl.Message(content=prompt).send()
                else:
                    await cl.Message(content="Product not found. Available products:").send()
                    rec_str = "\n"
                    # Show both search results and recommended products
                    for prod in self.state.search_results:
                        rec_str += f"- {prod.get('name', 'N/A')} | Price: ${prod.get('price', 'N/A')}\n"
                    if self.state.recommended_products:
                        rec_str += "\nRecommended products:\n"
                        for prod in self.state.recommended_products:
                            rec_str += f"- {prod.get('name', 'N/A')} | Price: ${prod.get('price', 'N/A')}\n"
                    await cl.Message(content=rec_str).send()

        
        elif user_action == "view cart":
            # Only display the cart, no search results
            await display_cart(self.state.cart)
        
        elif user_action == "checkout":
            await self.handle_checkout()
        
        elif user_action.startswith("remove"):
            parts = user_action.split(maxsplit=1)
            if len(parts) < 2:
                await cl.Message(content="Please specify which product to remove.").send()
                return
            
            prod_name = parts[1].strip().lower()
            for i, item in enumerate(self.state.cart):
                if prod_name in item.product.get("name", "").lower():
                    removed_item = self.state.cart.pop(i)
                    await cl.Message(content=f"Removed {removed_item.product.get('name')} from your cart.").send()
                    await display_cart(self.state.cart)
                    return
            
            await cl.Message(content=f"Could not find '{prod_name}' in your cart.").send()
        
        elif user_action.startswith("update"):
    # First, check if we have at least 3 parts (update, product, quantity)
            parts = user_action.split()
            if len(parts) < 3:
                await cl.Message(content="Please specify which product to update and the new quantity.").send()
                await cl.Message(content="Format: update <product name> <quantity>").send()
                return
            
            # The last part should be the quantity
            quantity_str = parts[-1]
            
            # Everything between "update" and the quantity is the product name
            # Join all parts except the first ("update") and the last (quantity)
            prod_name = " ".join(parts[1:-1]).lower()
            
            try:
                # Parse quantity
                quantity = int(quantity_str)
                if quantity <= 0:
                    await cl.Message(content="Quantity must be greater than 0.").send()
                    return
            except ValueError:
                await cl.Message(content="Please provide a valid quantity (a positive number).").send()
                return
            
            # Find and update the product
            found = False
            for item in self.state.cart:
                item_name = item.product.get("name", "").lower()
                # Check if product name contains the search term OR search term contains product name
                if prod_name in item_name or item_name in prod_name:
                    item.quantity = quantity
                    await cl.Message(content=f"Updated {item.product.get('name')} quantity to {quantity}.").send()
                    await display_cart(self.state.cart)
                    found = True
                    break
            
            if not found:
                await cl.Message(content=f"Could not find '{prod_name}' in your cart.").send()

        
        elif user_action == "clear cart":
            self.state.cart = []
            await cl.Message(content="Your cart has been cleared.").send()
        
        else:
            # Treat as a search query
            self.state.user_query = user_action
            await cl.Message(content=f"Searching for products matching '{user_action}'...").send()
            await self.search_products()
            await display_search_results(self.state)
