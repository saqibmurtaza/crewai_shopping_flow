#!/usr/bin/env python
from pydantic import BaseModel
from crewai.flow import Flow, listen, start
from crewai_shopping_flow.crews.shopping_crew.shopping_crew import ShoppingCrew


class ShoppingState(BaseModel):
    user_query: str = ""
    recommendations: list = []
    cart: list = []
    checkout_status: str = ""

class ShoppingFlow(Flow[ShoppingState]):

    @start()
    def start_shopping(self):
        print("Starting shopping assistant")
        self.state.user_query = input("What are you looking for? ")

    @listen(start_shopping)
    def search_products(self):
        print("Searching for products...")
        result = (
            ShoppingCrew()
            .crew()
            .kickoff(inputs={"query": self.state.user_query})
        )
        self.state.recommendations = result.raw
        print("Products found:", self.state.recommendations)

    @listen(search_products)
    def add_to_cart(self):
        print("Adding products to cart...")
        self.state.cart = self.state.recommendations[:2]  # Simulating adding first 2 items
        print("Items added to cart:", self.state.cart)

    @listen(add_to_cart)
    def proceed_to_checkout(self):
        print("Proceeding to checkout...")
        self.state.checkout_status = "Checkout completed successfully!"
        print(self.state.checkout_status)


def kickoff():
    shopping_flow = ShoppingFlow()
    shopping_flow.kickoff()


def plot():
    shopping_flow = ShoppingFlow()
    shopping_flow.plot()


if __name__ == "__main__":
    kickoff()
