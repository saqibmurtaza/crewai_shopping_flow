#!/usr/bin/env python
from pydantic import BaseModel
from crewai.flow import Flow, listen, start
from crewai_shopping_flow.crews.shopping_crew.shopping_crew import ShoppingCrew
import os
import ssl
import certifi
import urllib3
import logging

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
    
    @listen(recommend_products)
    def interaction_agent(self):
        """Handles user interaction, presenting product results and refining selections dynamically."""

        # Retrieve the latest product recommendations from the state
        product_recommendations = self.state.recommendations

        if not product_recommendations:
            return "No product recommendations available. Try refining your search."

        # Present product recommendations to the user
        response = f"Here are some product recommendations:\n"
        # response += "\n".join(
        #     [f"- {prod['product_name']} | Price: ${prod['price']}" for prod in product_recommendations]
        # )
        response += product_recommendations

        # Engage in conversation loop for refinements
        user_action = self.llm.ask(
            "Would you like to refine the search? (e.g., sort by price, filter by category, revert selection)"
        ).lower()

        if "sort" in user_action:
            sort_criteria = self.llm.ask("How would you like to sort? (e.g., price, rating)")
            sorted_products = sorted(
                product_recommendations, key=lambda x: x.get(sort_criteria, 0)
            )
            response = "Here are the sorted results:\n" + "\n".join(
                [f"- {prod['product_name']} | Price: ${prod['price']}" for prod in sorted_products]
            )
            self.state.recommendations = sorted_products  # Update recommendations

        elif "filter" in user_action:
            filter_criteria = self.llm.ask("What filter would you like to apply? (e.g., category: Living Room)")
            key, value = filter_criteria.split(":")
            filtered_products = [
                prod for prod in product_recommendations if str(prod.get(key.strip(), "")).lower() == value.strip().lower()
            ]
            response = "Here are the filtered results:\n" + "\n".join(
                [f"- {prod['product_name']} | Price: ${prod['price']}" for prod in filtered_products]
            )
            self.state.recommendations = filtered_products  # Update recommendations

        elif "revert" in user_action:
            response = "Reverting to previous selections."
            self.state.recommendations = self.state.previous_recommendations

        elif "add to cart" in user_action:
            selected_item = self.llm.ask("Which product would you like to add to the cart?")
            matching_item = next((p for p in product_recommendations if p['product_name'].lower() == selected_item.lower()), None)
            if matching_item:
                self.state.cart.append(matching_item)
                response = f"{matching_item['product_name']} has been added to your cart."
            else:
                response = "Sorry, that product is not available."

        return response


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


if __name__ == "__main__":
    kickoff()
