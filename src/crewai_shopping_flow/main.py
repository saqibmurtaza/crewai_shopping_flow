#!/usr/bin/env python
from pydantic import BaseModel
from crewai.flow import Flow, listen, start
from crewai_shopping_flow.crews.shopping_crew.shopping_crew import ShoppingCrew
from crewai_shopping_flow.crews.shopping_crew.llm_config import llm
import chainlit as cl
import os, ssl, certifi, urllib3, logging
import json

# Disable OpenTelemetry export
os.environ["OTEL_PYTHON_DISABLED"] = "true"
# or alternatively
os.environ["OTEL_SDK_DISABLED"] = "true"

os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"

os.environ['PYTHONHTTPSVERIFY'] = '0'
os.environ['CURL_CA_BUNDLE'] = ''

urllib3.disable_warnings()
logging.basicConfig(level=logging.DEBUG)

# Create a custom SSL context
context = ssl.create_default_context()
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE

# Configure urllib3 to use the custom context
urllib3.poolmanager.PoolManager(ssl_context=context)

class ShoppingState(BaseModel):
    user_query: str = ""
    search_results: list = []
    recommendations: list = []
    cart: list = []
    checkout_status: str = ""

class ShoppingFlow(Flow[ShoppingState]):
    llm = llm

    @start()
    def start_shopping(self):
        print("Starting shopping assistant")
        self.state.user_query = input("What are you looking for? ")
        print("User query:", self.state.user_query)

    @listen(start_shopping)
    def search_products(self):
        result = (
            ShoppingCrew()
            .crew()
            .kickoff()
        )
        # The result will now be properly formatted as JSON
        print("Search results:", result.raw)
        return result.raw

    @listen(search_products)
    def recommend_products(self):
        result = (
            ShoppingCrew()
            .crew()
            .kickoff(inputs={
                "user_query": self.state.search_results, 
                "user_preference": self.state.user_query})
        )
        print("Recommendations:", result.json)
        self.state.recommendations = result.json

    async def interaction_agent(self, message: cl.Message):
        """
        Chainlit-based interaction agent that presents recommendations and allows refinements.
        """

        # If recommendations are in JSON string format, parse them
        product_recommendations = self.state.recommendations
        if isinstance(product_recommendations, str):
            try:
                product_recommendations = json.loads(product_recommendations)
                if isinstance(product_recommendations, dict):
                    product_recommendations = product_recommendations.get('products', [])
            except json.JSONDecodeError:
                await cl.Message(content="Error processing recommendations.").send()
                return

        if not product_recommendations:
            await cl.Message(content="No product recommendations available. Try refining your search.").send()
            return

        # Display product recommendations
        recommendations_str = "Here are some product recommendations:\n"
        for prod in product_recommendations:
            if isinstance(prod, dict):
                recommendations_str += f"- {prod.get('name', 'N/A')} | Price: ${prod.get('price', 'N/A')}\n"
            else:
                recommendations_str += f"- {prod}\n"

        await cl.Message(content=recommendations_str).send()

        # Ask user for next action
        prompt = (
            "What would you like to do?\n"
            "1. **Refine search** (e.g., filter by category, sort by price).\n"
            "2. **Revert to previous selections.**\n"
            "3. **Add an item to your cart** (provide the product name).\n"
            "4. **View your cart.**\n"
            "5. **Proceed to checkout.**\n"
            "Please enter your choice."
        )
        await cl.Message(content=prompt).send()

        user_action_msg = await cl.listen()
        user_action = user_action_msg.text.lower().strip()

        # Handle sorting
        if "sort" in user_action:
            await cl.Message(content="How would you like to sort? (e.g., price, rating)").send()
            sort_criteria_msg = await cl.listen()
            sort_criteria = sort_criteria_msg.text.strip().lower()
            sorted_products = sorted(
                product_recommendations, key=lambda x: x.get(sort_criteria, 0)
            )
            self.state.recommendations = sorted_products  # Update state with sorted list
            sorted_str = "Here are the sorted results:\n"
            for prod in sorted_products:
                sorted_str += f"- {prod['product_name']} | Price: ${prod['price']}\n"
            await cl.Message(content=sorted_str).send()

        # Handle filtering
        elif "filter" in user_action:
            await cl.Message(content="What filter would you like to apply? (e.g., category: Living Room)").send()
            filter_criteria_msg = await cl.listen()
            filter_criteria = filter_criteria_msg.text.strip()
            try:
                key, value = filter_criteria.split(":")
                filtered_products = [
                    prod for prod in product_recommendations
                    if str(prod.get(key.strip(), "")).lower() == value.strip().lower()
                ]
                self.state.recommendations = filtered_products  # Update state with filtered results
                filtered_str = "Here are the filtered results:\n"
                for prod in filtered_products:
                    filtered_str += f"- {prod['product_name']} | Price: ${prod['price']}\n"
                await cl.Message(content=filtered_str).send()
            except ValueError:
                await cl.Message(content="Filter format error. Use 'key: value'.").send()

        # Handle revert selection
        elif "revert" in user_action:
            self.state.recommendations = self.state.search_results  # Reset to original search results
            await cl.Message(content="Reverted to previous selections.").send()

        # Handle adding to cart
        elif "add" in user_action and "cart" in user_action:
            await cl.Message(content="Which product would you like to add to your cart?").send()
            product_name_msg = await cl.listen()
            selected_item = product_name_msg.text.strip().lower()
            matching_item = next(
                (p for p in product_recommendations if p["product_name"].lower() == selected_item),
                None
            )
            if matching_item:
                self.state.cart.append(matching_item)
                await cl.Message(content=f"{matching_item['product_name']} has been added to your cart.").send()
            else:
                await cl.Message(content="Sorry, that product is not available.").send()

        # Handle viewing cart
        elif "view" in user_action and "cart" in user_action:
            if self.state.cart:
                cart_str = "Your cart contains:\n"
                for prod in self.state.cart:
                    cart_str += f"- {prod['product_name']} | Price: ${prod['price']}\n"
                await cl.Message(content=cart_str).send()
            else:
                await cl.Message(content="Your cart is empty.").send()

        # Handle checkout
        elif "checkout" in user_action:
            self.state.checkout_status = "Pending"
            await cl.Message(content="Proceeding to checkout...").send()
            # You can integrate checkout logic here (e.g., payment API, order processing)

        else:
            await cl.Message(content="I didn't understand that. Please try again.").send() 

    
   

    # @listen(search_products)
    # def add_to_cart(self):
    #     print("Adding products to cart...")
    #     self.state.cart = self.state.recommendations[:2]  # Simulating adding first 2 items
    #     print("Items added to cart:", self.state.cart)

    # @listen(add_to_cart)
    # def proceed_to_checkout(self):
    #     print("Proceeding to checkout...")
    #     self.state.checkout_status = "Checkout completed successfully!"
    #     print(self.state.checkout_status)


def kickoff():
    shopping_flow = ShoppingFlow()
    shopping_flow.kickoff()


def plot():
    shopping_flow = ShoppingFlow()
    shopping_flow.plot()


# Add these Chainlit handlers outside the class
@cl.on_chat_start
async def start():
    flow = ShoppingFlow()
    cl.user_session.set("flow", flow)

@cl.on_message
async def handle_message(message: cl.Message):
    flow = cl.user_session.get("flow")
    await flow.interaction_agent(message)


if __name__ == "__main__":
    kickoff()
