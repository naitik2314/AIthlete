import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('USDA_API_KEY')

BASE_URL = "https://api.nal.usda.gov/fdc/v1"

query = "apple with skin raw"


# Step 1: Search for Food to Get the FDC ID
search_params = {
    "query": query,
    "api_key": API_KEY,
    "pageSize": 5,  # Fetch a few results for accuracy
    "dataType": ["Foundation", "Branded", "SR Legacy"]  # Prioritize Foundation data
}

search_response = requests.get(f"{BASE_URL}/foods/search", params=search_params)

if search_response.status_code == 200:
    search_data = search_response.json()

    if "foods" in search_data and len(search_data["foods"]) > 0:
        best_food = search_data["foods"][0]  # Get the first search result
        fdc_id = best_food["fdcId"]  # Extract FDC ID for exact lookup

        # Step 2: Fetch Detailed Data Using FDC ID
        detail_response = requests.get(f"{BASE_URL}/food/{fdc_id}", params={"api_key": API_KEY})

        if detail_response.status_code == 200:
            detail_data = detail_response.json()

            print(f"Food: {detail_data['description']} (Source: {detail_data['dataType']})")

            # Macronutrient Mapping
            macronutrient_ids = {
                1003: "Protein",
                1004: "Fat",
                1005: "Carbohydrates",
                1008: "Calories"
            }

            # Ensure "foodNutrients" exists and is not empty
            if "foodNutrients" in detail_data and isinstance(detail_data["foodNutrients"], list):
                # Extract nutrient values safely
                nutrients = {
                    nutrient["nutrient"]["id"]: nutrient.get("amount", 0)
                    for nutrient in detail_data["foodNutrients"]
                    if "nutrient" in nutrient and "id" in nutrient["nutrient"]
                }

                # Print Nutrient Values
                for nutrient_id, nutrient_name in macronutrient_ids.items():
                    print(f"{nutrient_name}: {nutrients.get(nutrient_id, 'N/A')} G")
            else:
                print("No nutrient data available for this food.")
        else:
            print(f"Error fetching details for FDC ID {fdc_id}: {detail_response.status_code}")

    else:
        print("No food data found. Try a different search term.")
else:
    print(f"Error {search_response.status_code}: {search_response.text}")