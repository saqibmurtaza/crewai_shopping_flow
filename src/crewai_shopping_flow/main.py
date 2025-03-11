import chainlit as cl
import json
from pydantic import BaseModel
from crewai.flow import Flow, start, listen
from crewai_shopping_flow.crews.shopping_crew.shopping_crew import ShoppingCrew
from crewai_shopping_flow.crews.shopping_crew.llm_config import llm
class ShoppingState(BaseModel):
    user_query: str = ""
    search_results: list = []
    recommendations: list = []
    previous_results: list = []  # Add this to keep track of previous results
    cart: list = []
    checkout_status: str = ""

class ShoppingFlow(Flow[ShoppingState]):
    llm = llm  # Your LLM instance

    @start()
    async def start_shopping(self):
        print("Starting shopping assistant")
        # Optionally initialize state. Here, we leave the query empty.
        # This method is called once at the beginning.

    @listen(start_shopping)
    async def search_products(self):
        # Store previous results before new search
        if self.state.recommendations:
            self.state.previous_results = self.state.recommendations.copy()
            
        result = ShoppingCrew().crew().kickoff(
            inputs={
                "query": self.state.user_query,
                "user_preference": self.state.user_query
            }
        )
        try:
            parsed = json.loads(result.raw)
            if isinstance(parsed, dict):
                products = parsed.get("products", [])
                # Filter for relevant items based on the query
                query_terms = self.state.user_query.lower().split()
                relevant_products = [
                    p for p in products
                    if any(term in p.get("name", "").lower() or 
                          term in p.get("description", "").lower() 
                          for term in query_terms)
                ]
                
                self.state.search_results = relevant_products
                self.state.recommendations = relevant_products

                if parsed.get("message"):
                    await cl.Message(content=parsed["message"]).send()
            else:
                print("Unexpected response format:", parsed)
        except Exception as e:
            print("Error parsing search results:", e)
            await cl.Message(content="Sorry, I encountered an error processing the search results.").send()
        return result.raw

    @listen(search_products)
    async def recommend_products(self):
        if not self.state.recommendations:
            self.state.recommendations = self.state.search_results

        if self.state.recommendations:
            # Organize recommendations by category
            rec_str = "Here are our recommendations:\n\n"
            
            # Show current search results
            rec_str += "🔍 Current Search Results:\n"
            for prod in self.state.recommendations:
                rec_str += f"- {prod.get('name', 'N/A')} | Price: ${prod.get('price', 'N/A')}\n"
                if prod.get('description'):
                    rec_str += f"  {prod.get('description')}\n"
            
            # Show previous results if they exist and are different
            if self.state.previous_results:
                previous_names = {p.get('name') for p in self.state.previous_results}
                current_names = {p.get('name') for p in self.state.recommendations}
                if previous_names - current_names:  # If there are unique previous results
                    rec_str += "\n📌 Previously Viewed Items:\n"
                    for prod in self.state.previous_results:
                        if prod.get('name') not in current_names:
                            rec_str += f"- {prod.get('name', 'N/A')} | Price: ${prod.get('price', 'N/A')}\n"
            
            await cl.Message(content=rec_str).send()
            
            # Show options to the user
            prompt = (
                "What would you like to do?\n"
                "1. Add an item to cart: Type 'add <product name>'\n"
                "2. Refine your search: Type 'refine <query>'\n"
                "3. View your cart: Type 'view cart'\n"
                "4. Proceed to checkout: Type 'checkout'\n\n"
                "💡 You can add items from both current and previous results!"
            )
            await cl.Message(content=prompt).send()
        
        return json.dumps({"products": self.state.recommendations})

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
                    self.state.cart.append(matching_item)
                    await cl.Message(content=f"{matching_item.get('name')} has been added to your cart.").send()
                    # Show cart and available options
                    cart_str = "\nYour cart contains:\n"
                    total = 0
                    for prod in self.state.cart:
                        price = prod.get('price', 0)
                        cart_str += f"- {prod.get('name', 'N/A')} | Price: ${price}\n"
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
        elif "view cart" in user_action:
            if self.state.cart:
                cart_str = "Your cart contains:\n"
                for prod in self.state.cart:
                    cart_str += f"- {prod.get('name', 'N/A')} | Price: ${prod.get('price', 'N/A')}\n"
                await cl.Message(content=cart_str).send()
            else:
                await cl.Message(content="Your cart is empty.").send()
        elif "checkout" in user_action:
            self.state.checkout_status = "Completed"
            await cl.Message(content="Checkout completed successfully!").send()
        else:
            await cl.Message(content="I'm sorry, I didn't understand that. Please try again.").send()

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

if __name__ == "__main__":
    from crewai.flow import run_flow
    run_flow(ShoppingFlow())
