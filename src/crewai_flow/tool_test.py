from pydantic import BaseModel
import json, os, gspread

# Get the project root directory
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
CREDENTIALS_PATH = os.path.join(PROJECT_ROOT, "gc.json")


# Assuming you've already defined your RecommendationTool and RecommendationToolInput

class RecommendationToolInput(BaseModel):
    recommendation_pref: str

class RecommendationTool:
    name = "Furniture Recommendation Tool"
    description = (
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

    def _run(self, recommendation_pref: str) -> str:
        return self.recommend_by_category(recommendation_pref)

# Instantiate the tool
tool = RecommendationTool()

# Test with a sample category
test_category = "seating"
result = tool._run(recommendation_pref=test_category)
print("Test Result:", result)
