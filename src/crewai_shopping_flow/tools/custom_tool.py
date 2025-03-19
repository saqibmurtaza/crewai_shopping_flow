from typing import Type
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from crewai import LLM
import gspread, os
import json

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
            # Connect to Google Sheets
            gc = gspread.service_account(filename=CREDENTIALS_PATH)
            sheet = gc.open("FurnitureProducts").sheet1
            
            # Fetch all records; ensure your sheet includes a 'name' column. <<<<<
            products = sheet.get_all_records()
            
            # Search for matching products using .get() to safely access the "name" key <<<<<
            matching_products = [p for p in products if query.lower() in p.get('name', "").lower()]
            
            if not matching_products:
                return json.dumps({"products": [], "message": "No matching products found."})
                
            # Format results in JSON (each product now includes the 'category' field if available) <<<<<
            return json.dumps({
                "products": matching_products,
                "message": "Products found successfully"
            })
        except Exception as e:
            return json.dumps({
                "products": [],
                "error": str(e)
            })


# class RecommendationToolInput(BaseModel):
#     """Input schema for RecommendationTool."""
    
#     user_preference: str = Field(..., description="extracted category string from search results.")

# class RecommendationTool(BaseTool):
#     name: str = "Furniture Recommendation Tool"
#     description: str = (
#         "A tool to extract products category from search results and recommend products "
#         "based on the category."
#         "It retrieves relevant products and returns their details."
#     )
#     args_schema: Type[BaseModel] = RecommendationToolInput

#     def recommend_by_category(self, category_query: str) -> str:
#         print(f"DEBUG: Category Query: {category_query}")
#         try:
#             # Connect to Google Sheets
#             gc = gspread.service_account(filename=CREDENTIALS_PATH)
#             sheet = gc.open("FurnitureProducts").sheet1
#             products = sheet.get_all_records()
#         except Exception as e:
#             return f"Error fetching products from Google Sheets: {str(e)}"

#         # Filter products by category (case-insensitive)
#         matching_products = [
#             product for product in products
#             if category_query.lower() in product.get('category', '').lower()
#         ]
        
#         if not matching_products:
#             return json.dumps({
#                 "data": [],
#                 "formatted": "No furniture products found in the database."
#             })
        
        
#         return json.dumps({
#             "data": matching_products
#         })

#     def _run(self, user_preference: str) -> str:
#         # For a simple category-based recommendation, treat the user preference as the category query.
#         return self.recommend_by_category(user_preference)

