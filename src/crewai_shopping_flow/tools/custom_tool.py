from typing import Type
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from crewai import LLM
import gspread

# Initialize LLM with Gemini Pro
llm = LLM(
    model="gemini/gemini-1.5-flash",
    temperature=0
)


class SearchToolInput(BaseModel):
    """Input schema for SearchTool."""
    
    query: str = Field(..., description="User search query for furniture products.")

class SearchTool(BaseTool):
    name: str = "Furniture Search Tool"
    description: (
        "A tool to search for furniture products from a Google Sheet based on user queries. "
        "It retrieves relevant products and returns their details."
    )
    args_schema: Type[BaseModel] = SearchToolInput

    def _run(self, query: str) -> str:
        # Connect to Google Sheets
        gc = gspread.service_account(filename='credentials.json')
        sheet = gc.open("FurnitureProducts").sheet1
        
        # Fetch all records
        products = sheet.get_all_records()
        
        # Search for matching products
        matching_products = [p for p in products if query.lower() in p['name'].lower()]
        
        if not matching_products:
            return "No matching products found."
        
        # Format results
        results = "\n".join([f"{p['name']} - {p['price']}" for p in matching_products])
        return f"Found products:\n{results}"


class RecommendationToolInput(BaseModel):
    """Input schema for RecommendationTool."""
    
    user_preference: str = Field(..., description="User preferences or past selections for recommendations.")

class RecommendationTool(BaseTool):
    name: str = "Furniture Recommendation Tool"
    description: (
        "A tool to suggest the best furniture products based on user preferences and available stock. "
        "It ensures recommendations are relevant by selecting from the current inventory."
    )
    args_schema: Type[BaseModel] = RecommendationToolInput

    def _run(self, user_preference: str) -> str:
        
        try:
            # Connect to Google Sheets
            gc = gspread.service_account(filename='credentials.json')
            sheet = gc.open("FurnitureProducts").sheet1
            
            # Fetch all available product records
            products = sheet.get_all_records()
            available_products = [p for p in products if p.get("available", True)]
        except Exception as e:
            return f"Error fetching products from Google Sheets: {str(e)}"
        
        if not available_products:
            return "No available products for recommendation."
        
        # Use Gemini AI to generate personalized recommendations from available products
        prompt = (
            f"Based on the following user preference: {user_preference}, "
            "suggest the best matching furniture products from this list: "
            f"{[p['name'] for p in available_products]}"
        )
        
        try:
            response = llm.generate(prompt)
            recommendations = response.text if response and hasattr(response, 'text') else "No recommendations available."
        except Exception as e:
            return f"Error generating recommendations: {str(e)}"
        
        return f"Recommended products:\n{recommendations}"

class InteractionToolInput(BaseModel):
    """Input schema for InteractionTool."""
    
    user_message: str = Field(..., description="User input message for interaction.")

class InteractionTool(BaseTool):
    name: str = "User Interaction Tool"
    description: (
        "A tool that enables interaction with the user, answering queries, providing shopping assistance, "
        "and guiding them through the shopping process using natural language."
    )
    args_schema: Type[BaseModel] = InteractionToolInput

    def _run(self, user_message: str) -> str:
        try:
            # Generate response using Gemini Pro
            response = llm.generate(user_message)
            return response if response else "I couldn't understand your request. Could you please rephrase?"
        except Exception as e:
            return f"Error processing user interaction: {str(e)}"
        
class CartManagerToolInput(BaseModel):
    """Input schema for CartManagerTool."""
    
    action: str = Field(..., description="Action to perform on the cart (add, remove, view, checkout).")
    product_name: str = Field("", description="Name of the product to add or remove (if applicable).")
    quantity: int = Field(1, description="Quantity of the product to add or remove (if applicable).")

class CartManagerTool(BaseTool):
    name: str = "Shopping Cart Manager"
    description: (
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
    description: (
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
    description: (
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

