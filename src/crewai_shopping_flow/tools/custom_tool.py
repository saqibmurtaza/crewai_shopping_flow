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


class RecommendationToolInput(BaseModel):
    """Input schema for RecommendationTool."""
    
    query: str = Field(..., description="User query for furniture product category.")

class RecommendationTool(BaseTool):
    name: str= "Furniture Recommendation Tool"
    description: str = (
        "A tool to search for furniture products from a Google Sheet based on product category."
        "It retrieves relevant products and returns their details."
    )
    args_schema = RecommendationToolInput

    def recommend_by_category(self, category: str) -> str:
        print(f"DEBUG: Category: {category}")
        try:
            # Simulating Google Sheets connection and fetching data
            gc = gspread.service_account(filename=CREDENTIALS_PATH)
            sheet = gc.open("FurnitureProducts").sheet1
            
            # Fetch all records; ensure your sheet includes a 'name' column. <<<<<
            all_products = sheet.get_all_records()
        
        except Exception as e:
            return f"Error fetching products from Google Sheets: {str(e)}"

        # Filter products by category (case-insensitive)
        matching_products = [
            product for product in all_products if category.lower() in product["category"].lower()
        ]

        if matching_products:
            return json.dumps({"recommended_products": matching_products})
        else:
            return json.dumps({
                "recommended_products": [],
                "formatted": "No furniture products found in the database."
            })

    def _run(self, query: str) -> str:
        return self.recommend_by_category(query)
