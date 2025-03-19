import chainlit as cl
import json
from pydantic import BaseModel, Field
from crewai.flow import Flow, start, listen
from crewai_shopping_flow.crews.shopping_crew.shopping_crew import ShoppingCrew
from crewai_shopping_flow.crews.shopping_crew.models import SearchResults

class CartItem(BaseModel):
    product: dict
    quantity: int = 1

class ShoppingState(BaseModel):
    user_query: str = ""
    search_results: SearchResults = SearchResults(products=[])
    recommendations: list = Field(default_factory=list)
    previous_results: list = Field(default_factory=list)
    cart: list[CartItem] = Field(default_factory=list)  # Changed to use CartItem
    checkout_status: str = ""

    def add_to_cart(self, product: dict) -> tuple[bool, str]:
        # Check if item already exists in cart
        for cart_item in self.cart:
            if cart_item.product.get('name') == product.get('name'):
                cart_item.quantity += 1
                return True, f"Increased quantity of {product.get('name')} in your cart to {cart_item.quantity}."
        # If item doesn't exist, add it
        self.cart.append(CartItem(product=product))
        return True, f"Added {product.get('name')} to your cart."

    def update_cart_quantity(self, product_name: str, quantity: int) -> tuple[bool, str]:
        for cart_item in self.cart:
            if cart_item.product.get('name').lower() == product_name.lower():
                if quantity <= 0:
                    self.cart.remove(cart_item)
                    return True, f"Removed {cart_item.product.get('name')} from your cart."
                cart_item.quantity = quantity
                return True, f"Updated quantity of {cart_item.product.get('name')} to {quantity}."
        return False, "Product not found in cart."

    def get_cart_total(self) -> float:
        return sum(float(item.product.get('price', 0)) * item.quantity for item in self.cart)

class ShoppingFlow(Flow[ShoppingState]):

    @start()
    async def start_shopping(self):
        print("Starting shopping assistant")

    @listen(start_shopping)
    async def search_products(self):
        # Kick off the search using the crew, passing the user's query.
        crew_output = ShoppingCrew().crew().kickoff(
            inputs={
                "query": self.state.user_query
            }
        )
        
        # Accessing the crew output
        desired_output = None

        for task_output in crew_output.tasks_output:
            # Get the raw string and remove any markdown code block markers if present
            raw_str = task_output.raw
            json_str = raw_str.split("```")[0].strip()
            
            try:
                parsed = json.loads(json_str)
                # Check if this parsed output contains the desired "products" key
                if isinstance(parsed, dict) and "products" in parsed:
                    desired_output = parsed
                    break
            except json.JSONDecodeError:
                continue

        if desired_output:
            print("Extracted JSON:", json.dumps(desired_output, indent=2))
        else:
            print("No valid JSON output with 'products' key was found.")
        
        # Update the state with the search results
        self.state.search_results = desired_output["products"]
        self.state.recommendations= desired_output["products"]
        print(f"DEBUG: Search results: {self.state.search_results}")
        print(f"DEBUG: Recommendations: {self.state.recommendations}")
                    
    
    # @listen(search_products)
    # async def get_recommendation(self):
    #     print("Getting recommendations")

    #     # Use the original search results from the CrewAI flow.
    #     search_results = self.state.search_results
    #     print(f"DEBUG: Search results: {search_results}")

    #     # extract the category from the search results
    #     category = search_results[0].get("category", "")
    #     print(f"DEBUG: Category Query: {category}")

    #     # Prepare a list to collect complementary products.
    #     complementary_products = []

    #     # search for complementary products based on the category
    #     comp_query = category
    
    #     comp_result = (
    #         ShoppingCrew()
    #         .crew()
    #         .kickoff(inputs={"query": comp_query})
    #     )
    #     output = json.loads(comp_result.raw)
    #     if output.get("products"):
    #         complementary_products.extend(output["products"])
    #     print(f"DEBUG: Complementary products: {complementary_products}")
                        
    #     # Merge original search results with complementary products, removing duplicates by product name.
    #     all_products = {prod.get("name"): prod for prod in search_results}
    #     for prod in complementary_products:
    #         if prod.get("name") not in all_products:
    #             all_products[prod.get("name")] = prod
    #     combined_products = list(all_products.values())
    #     print(f"DEBUG: Combined products: {combined_products}")
    #     self.state.recommendations = combined_products
    
    #     await cl.Message(content=combined_products).send()
    #     prompt = (
    #         "What would you like to do?\n"
    #         "1. Add an item to cart: Type 'add <product name>'\n"
    #         "2. Refine your search: Type 'refine <query>'\n"
    #         "3. View your cart: Type 'view cart'\n"
    #         "4. Proceed to checkout: Type 'checkout'\n\n"
    #         "💡 You can add items from both current and previous results!"
    #     )
    #     await cl.Message(content=prompt).send()
        
    #     prompt = (
    #         "What would you like to do?\n"
    #         "1. Add an item to cart: Type 'add <product name>'\n"
    #         "2. Refine your search: Type 'refine <query>'\n"
    #         "3. View your cart: Type 'view cart'\n"
    #         "4. Proceed to checkout: Type 'checkout'\n\n"
    #         "💡 You can add items from both current and previous results!"
    #     )
    #     await cl.Message(content=prompt).send()
        
    #     return json.dumps({"products": self.state.recommendations})


    async def interaction_agent(self, message: cl.Message):
        """
        The interaction agent handles incoming user messages.
        If no recommendations exist, the message is treated as a search query.
        Otherwise, the message is processed as an action command.
        """
        # Parse recommendations if necessary
        product_recommendations = self.state.recommendations
        if isinstance(product_recommendations, str):
            try:
                product_recommendations = json.loads(product_recommendations)
                if isinstance(product_recommendations, dict):
                    product_recommendations = product_recommendations.get("products", [])
            except json.JSONDecodeError:
                await cl.Message(content="Error processing recommendations.").send()
                return

        if not product_recommendations:
            # Treat the message as a search query
            self.state.user_query = message.content.strip()
            await cl.Message(content=f"Searching for products matching '{self.state.user_query}'...").send()
            await self.search_products()
            if not self.state.recommendations:
                await cl.Message(content="No products found. Please refine your search.").send()
                return
            else:
                rec_str = "Found products:\n"
                for prod in self.state.recommendations:
                    rec_str += f"- {prod.get('name', 'N/A')} | Price: ${prod.get('price', 'N/A')}\n"
                await cl.Message(content=rec_str).send()
                prompt = (
                    "What would you like to do next?\n"
                    "Type 'refine <query>' to refine your search,\n"
                    "or 'add <product name>' to add an item to your cart,\n"
                    "or 'view cart' to see your cart,\n"
                    "or 'checkout' to proceed to checkout."
                )
                await cl.Message(content=prompt).send()
                return

        # Process the message as an action command
        user_action = message.content.strip().lower()
        if user_action.startswith("refine"):
            # Split the message into parts and join everything after "refine"
            parts = message.content.split(maxsplit=1)
            if len(parts) < 2:
                await cl.Message(content="Please specify what you want to search for after 'refine'.").send()
                return
            refined_query = parts[1].strip()
            self.state.user_query = refined_query
            await cl.Message(content=f"Refining search for '{refined_query}'...").send()
            await self.search_products()
            if self.state.recommendations:
                rec_str = "Refined product recommendations:\n"
                for prod in self.state.recommendations:
                    rec_str += f"- {prod.get('name', 'N/A')} | Price: ${prod.get('price', 'N/A')}\n"
                await cl.Message(content=rec_str).send()
                prompt = (
                    "What would you like to do next?\n"
                    "Type 'refine <query>' to refine your search,\n"
                    "or 'add <product name>' to add an item to your cart,\n"
                    "or 'view cart' to see your cart,\n"
                    "or 'checkout' to proceed to checkout."
                )
                await cl.Message(content=prompt).send()
            else:
                await cl.Message(content="No products match your refined query.").send()
        elif user_action.startswith("add"):
            parts = user_action.split(maxsplit=1)
            if len(parts) < 2:
                await cl.Message(content="Please specify which product to add.").send()
                # Show all available products
                all_products = list(self.state.recommendations)
                if self.state.previous_results:
                    all_products.extend([p for p in self.state.previous_results 
                                      if p not in self.state.recommendations])
                    
                rec_str = "\nAvailable products:\n"
                for prod in all_products:
                    rec_str += f"- {prod.get('name', 'N/A')} | Price: ${prod.get('price', 'N/A')}\n"
                await cl.Message(content=rec_str).send()
            else:
                prod_name = parts[1].strip().lower()
                # Search in both current and previous results
                all_products = list(self.state.recommendations)
                if self.state.previous_results:
                    all_products.extend([p for p in self.state.previous_results 
                                      if p not in self.state.recommendations])
                
                matching_item = next(
                    (p for p in all_products 
                     if prod_name in p.get("name", "").lower() or 
                     p.get("name", "").lower() in prod_name),
                    None
                )
                if matching_item:
                    self.state.cart.append(CartItem(product=matching_item))
                    await cl.Message(content=f"{matching_item.get('name')} has been added to your cart.").send()
                    # Show cart and available options
                    cart_str = "\nYour cart contains:\n"
                    total = 0
                    for prod in self.state.cart:
                        price = prod.product.get('price', 0)
                        cart_str += f"- {prod.product.get('name', 'N/A')} | Price: ${price}\n"
                        total += float(price)
                    cart_str += f"\nTotal: ${total:.2f}"
                    await cl.Message(content=cart_str).send()
                else:
                    await cl.Message(content="Product not found in recommendations. Available products:").send()
                    # Show available products to help user
                    rec_str = "\n"
                    for prod in self.state.recommendations:
                        rec_str += f"- {prod.get('name', 'N/A')} | Price: ${prod.get('price', 'N/A')}\n"
                    await cl.Message(content=rec_str).send()

            # Always show options after add attempt
            prompt = (
                "\nWhat would you like to do next?\n"
                "- Add another item by typing 'add <product name>'\n"
                "- Type 'refine <query>' to search for different products\n"
                "- Type 'view cart' to see your cart\n"
                "- Type 'checkout' to proceed to checkout"
            )
            await cl.Message(content=prompt).send()
            return
        elif user_action.startswith(("update", "remove")) or user_action == "clear cart":
            await self.handle_cart_action(user_action, message)
        elif "view cart" in user_action:
            cart_message = await self.format_cart_message()
            await cl.Message(content=cart_message).send()
        elif "checkout" in user_action:
            self.state.checkout_status = "Completed"
            await cl.Message(content="Checkout completed successfully!").send()
        else:
            await cl.Message(content="I'm sorry, I didn't understand that. Please try again.").send()

    async def format_cart_message(self) -> str:
        if not self.state.cart:
            return "Your cart is empty."
        
        cart_str = "🛒 Your Cart:\n"
        total = 0
        for item in self.state.cart:
            price = float(item.product.get('price', 0))
            item_total = price * item.quantity
            cart_str += (f"- {item.product.get('name', 'N/A')} | "
                        f"Price: ${price} | Quantity: {item.quantity} | "
                        f"Subtotal: ${item_total:.2f}\n")
            total = self.state.get_cart_total()
        cart_str += f"\n💰 Total: ${total:.2f}"
        
        cart_str += "\n\n📝 Cart Management Options:\n"
        cart_str += "- Update quantity: Type 'update <product name> <quantity>'\n"
        cart_str += "- Remove item: Type 'remove <product name>'\n"
        cart_str += "- Clear cart: Type 'clear cart'"
        
        return cart_str

    async def handle_cart_action(self, action: str, message: cl.Message):
        parts = action.split()
        if action.startswith("update") and len(parts) >= 3:
            product_name = " ".join(parts[1:-1])
            try:
                quantity = int(parts[-1])
                success, msg = self.state.update_cart_quantity(product_name, quantity)
                await cl.Message(content=msg).send()
                if success:
                    await cl.Message(content=await self.format_cart_message()).send()
            except ValueError:
                await cl.Message(content="Please provide a valid quantity number.").send()
        elif action.startswith("remove"):
            product_name = " ".join(parts[1:])
            success, msg = self.state.update_cart_quantity(product_name, 0)
            await cl.Message(content=msg).send()
            if success:
                await cl.Message(content=await self.format_cart_message()).send()
        elif action == "clear cart":
            self.state.cart = []
            await cl.Message(content="Cart has been cleared.").send()

# --- Chainlit Handlers (Outside the Class) ---

@cl.on_chat_start
async def start():
    flow = ShoppingFlow()
    await flow.start_shopping()  # Initialize state if necessary.
    cl.user_session.set("flow", flow)
    await cl.Message(content="Welcome to our furniture store! What are you looking for today?").send()

@cl.on_message
async def handle_message(message: cl.Message):
    flow = cl.user_session.get("flow")
    await flow.interaction_agent(message)

def kickoff():
    ShoppingFlow().kickoff()


if __name__ == "__main__":
    kickoff()


#     from crewai.flow import run_flow

# if __name__ == "__main__":
#     from crewai.flow import run_flow
#     run_flow(ShoppingFlow())
