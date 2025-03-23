# from typing import Type
# from crewai.tools import BaseTool
# from pydantic import BaseModel, Field
# from crewai import LLM
# import gspread, os
# import json

# # Get the project root directory
# PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
# CREDENTIALS_PATH = os.path.join(PROJECT_ROOT, "gc.json")

# class SearchToolInput(BaseModel):
#     """Input schema for SearchTool."""
#     query: str = Field(..., description="User search query for furniture products.")

# class SearchTool(BaseTool):
#     name: str = "Furniture Search Tool"
#     description: str = (
#         "A tool to search for furniture products from a Google Sheet based on user queries. "
#         "It retrieves relevant products and also suggests similar products based on category."
#     )
#     args_schema: Type[BaseModel] = SearchToolInput

#     def _run(self, query: str) -> str:
#         try:
#             # Connect to Google Sheets
#             gc = gspread.service_account(filename=CREDENTIALS_PATH)
#             sheet = gc.open("FurnitureProducts").sheet1
            
#             # Fetch all records; ensure your sheet includes 'name' and 'category' columns
#             products = sheet.get_all_records()
            
#             # 🔹 First Search: Match products based on user query
#             matching_products = [p for p in products if query.lower() in p.get('name', "").lower()]
            
#             if not matching_products:
#                 return json.dumps({"products": [], "recommended": [], "message": "No matching products found."})
            
#             # 🔹 Extract category from first matching product (if available)
#             category = matching_products[0].get("category", "").strip()

#             # 🔹 Second Search: Find more products in the same category (excluding the searched product)
#             recommended_products = [p for p in products if p.get("category", "").strip().lower() == category.lower() and p not in matching_products]
#             # 🔹 Combine results and return JSON
#             result= json.dumps({
#                 "search_products": matching_products,
#                 "recommended_products": recommended_products,
#                 "message": "Products found successfully."
#             })
#             print(f"SearchTool: {result}")
#             return result

#         except Exception as e:
#             return json.dumps({
#                 "your_search": [],
#                 "recommended": [],
#                 "error": str(e)
#             })

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
        "It retrieves relevant products and also suggests similar products based on category."
    )
    args_schema: Type[BaseModel] = SearchToolInput

    def _run(self, query: str) -> str:
        try:
            # Connect to Google Sheets
            gc = gspread.service_account(filename=CREDENTIALS_PATH)
            sheet = gc.open("FurnitureProducts").sheet1
            
            # Fetch all records; ensure your sheet includes 'name' and 'category' columns
            products = sheet.get_all_records()
            
            # 🔹 Handle plurals and variations
            query_variations = [query.lower()]
            if query.lower().endswith('s'):
                query_variations.append(query.lower()[:-1])  # Remove 's' for plural
            else:
                query_variations.append(query.lower() + 's')  # Add 's' for singular
            
            # 🔹 First Search: Match products based on user query and its variations
            matching_products = []
            for p in products:
                product_name = p.get('name', "").lower()
                for variation in query_variations:
                    if variation in product_name:
                        matching_products.append(p)
                        break
            
            if not matching_products:
                return json.dumps({"products": [], "recommended": [], "message": "No matching products found."})
            
            # 🔹 Extract all unique categories from matching products
            categories = set(p.get("category", "").strip() for p in matching_products if p.get("category"))
            
            # 🔹 Second Search: Find more products in any of the matching categories
            recommended_products = []
            for p in products:
                product_category = p.get("category", "").strip()
                if product_category in categories and p not in matching_products:
                    recommended_products.append(p)
            
            # 🔹 Combine results and return JSON
            result = json.dumps({
                "products": matching_products,
                "recommended_products": recommended_products,
                "message": f"Products found successfully in categories: {', '.join(categories)}."
            })
            print(f"SearchTool: {result}")
            return result

        except Exception as e:
            return json.dumps({
                "products": [],
                "recommended": [],
                "error": str(e)
            })

