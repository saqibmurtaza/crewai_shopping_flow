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
        result = ShoppingCrew().crew().kickoff(inputs={
            "query": self.state.user_query,
            "user_preference": self.state.user_query
        })
        print("Raw search results:", result.raw)
        try:
            parsed = json.loads(result.raw)
            self.state.search_results = parsed.get("products", [])
            self.state.recommendations = self.state.search_results
        except Exception as e:
            print("Error parsing search results:", e)
        return result.raw

    @listen(search_products)
    async def recommend_products(self):
        # For simplicity, here we assume recommendations mirror search_results.
        if not self.state.recommendations:
            self.state.recommendations = self.state.search_results
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
            else:
                await cl.Message(content="No products match your refined query.").send()
        elif user_action.startswith("add"):
            parts = user_action.split(maxsplit=1)
            if len(parts) < 2:
                await cl.Message(content="Please specify which product to add.").send()
            else:
                prod_name = parts[1].strip()
                matching_item = next(
                    (p for p in self.state.recommendations if p.get("name", "").lower() == prod_name.lower()),
                    None
                )
                if matching_item:
                    self.state.cart.append(matching_item)
                    await cl.Message(content=f"{matching_item.get('name')} has been added to your cart.").send()
                else:
                    await cl.Message(content="Product not found in recommendations.").send()
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
