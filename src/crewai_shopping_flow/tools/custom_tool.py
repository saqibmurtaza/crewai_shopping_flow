import json
import gspread
import os
from pydantic import BaseModel, Field
from typing import Type
from crewai.tools import BaseTool
from crewai_shopping_flow.crews.shopping_crew.llm_config import llm

# Get the project root directory
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
CREDENTIALS_PATH = os.path.join(PROJECT_ROOT, "gc.json")

class SearchToolInput(BaseModel):
    """Input schema for SearchTool."""
    query: str = Field(..., description="User search query for furniture products.")

class SearchTool(BaseTool):
    name: str = "Furniture Search Tool"
    description: str = (
        "A tool to search for furniture products from a Google Sheet based on user queries. "
        "It retrieves relevant products and returns their details."
    )
    args_schema: Type[BaseModel] = SearchToolInput

    def _run(self, query: str) -> str:
        try:
            gc = gspread.service_account(filename=CREDENTIALS_PATH)
            sheet = gc.open("FurnitureProducts").sheet1
            products = sheet.get_all_records()
            # Use 'name' as the key consistently.
            matching_products = [p for p in products if query.lower() in p['name'].lower()]
            if not matching_products:
                return json.dumps({"products": [], "message": "No matching products found."})
            return json.dumps({
                "products": matching_products,
                "message": "Products found successfully"
            })
        except Exception as e:
            return json.dumps({
                "products": [],
                "error": str(e)
            })

class RecommendationToolInput(BaseModel):
    """Input schema for RecommendationTool."""
    user_preference: str = Field(..., description="User preference for furniture products.")

class RecommendationTool(BaseTool):
    name: str = "Furniture Recommendation Tool"
    description: str = (
        "A tool to suggest the best furniture products by category based on available stock."
    )
    args_schema: Type[BaseModel] = RecommendationToolInput

    def recommend_by_category(self, category_query: str) -> dict:
        try:
            gc = gspread.service_account(filename=CREDENTIALS_PATH)
            sheet = gc.open("FurnitureProducts").sheet1
            products = sheet.get_all_records()
        except Exception as e:
            return {"data": [], "error": str(e)}

        matching_products = [
            product for product in products
            if category_query.lower() in product.get('category', '').lower()
        ]
        if not matching_products:
            return {"data": [], "formatted": "No furniture products found in the database."}
        return {"data": matching_products}

    def _run(self, user_preference: str) -> str:
        result = self.recommend_by_category(user_preference)
        return json.dumps(result)

        
class CartManagerToolInput(BaseModel):
    """Input schema for CartManagerTool."""
    
    action: str = Field(..., description="Action to perform on the cart (add, remove, view, checkout).")
    product_name: str = Field("", description="Name of the product to add or remove (if applicable).")
    quantity: int = Field(1, description="Quantity of the product to add or remove (if applicable).")

class CartManagerTool(BaseTool):
    name: str = "Shopping Cart Manager"
    description: str = (
        "A tool that allows users to manage their shopping cart by adding, removing, viewing items, "
        "or proceeding to checkout."
    )
    args_schema: Type[BaseModel] = CartManagerToolInput

    def _run(self, action: str, product_name: str = "", quantity: int = 1) -> str:
        try:
            if action.lower() == "add":
                return f"Added {quantity} of {product_name} to the cart."
            elif action.lower() == "remove":
                return f"Removed {quantity} of {product_name} from the cart."
            elif action.lower() == "view":
                return "Displaying current cart contents."
            elif action.lower() == "checkout":
                return "Proceeding to checkout."
            else:
                return "Invalid cart action. Please specify add, remove, view, or checkout."
        except Exception as e:
            return f"Error managing cart: {str(e)}"

class CheckoutToolInput(BaseModel):
    """Input schema for CheckoutTool."""
    
    payment_method: str = Field(..., description="User-selected payment method.")
    shipping_address: str = Field(..., description="User's shipping address.")
    contact_info: str = Field(..., description="User's contact information.")

class CheckoutTool(BaseTool):
    name: str = "Checkout Manager"
    description: str = (
        "A tool that assists users in completing their purchase by processing payments, "
        "handling shipping details, and finalizing the checkout process."
    )
    args_schema: Type[BaseModel] = CheckoutToolInput

    def _run(self, payment_method: str, shipping_address: str, contact_info: str) -> str:
        try:
            # Process payment and finalize order
            confirmation_message = (
                f"Checkout successful!\n"
                f"Payment Method: {payment_method}\n"
                f"Shipping Address: {shipping_address}\n"
                f"Contact Info: {contact_info}\n"
                "Your order has been placed and will be shipped soon."
            )
            return confirmation_message
        except Exception as e:
            return f"Error during checkout: {str(e)}"

class SupportToolInput(BaseModel):
    """Input schema for SupportTool."""
    
    user_query: str = Field(..., description="User's support query or issue.")

class SupportTool(BaseTool):
    name: str = "Customer Support Assistant"
    description: str = (
        "A tool that assists users with customer support inquiries, providing help on orders, "
        "returns, refunds, product details, and general assistance."
    )
    args_schema: Type[BaseModel] = SupportToolInput

    def _run(self, user_query: str) -> str:
        try:
            # Generate response using Gemini Pro
            response = llm.generate(user_query)
            return response if response else "I'm sorry, I couldn't find an answer to your question. Please contact customer support."
        except Exception as e:
            return f"Error handling support request: {str(e)}"

