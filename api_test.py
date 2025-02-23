import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('USDA_API_KEY')

BASE_URL = "https://api.nal.usda.gov/fdc/v1"

query = "apple with skin raw"


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
                1008: "Calories",  # Standard calories (may be missing)
                1002: "Energy (kJ)",  # Convert if needed
                2047: "Calories (Atwater General)",  # Preferred
                2048: "Calories (Atwater Specific)"  # More precise
            }

            # Default serving size (100g if not provided)
            serving_size = detail_data.get("servingSize", 100)
            serving_unit = detail_data.get("servingSizeUnit", "g")

            print(f"Default Serving Size: {serving_size} {serving_unit}")

            # Ensure "foodNutrients" exists and is not empty
            if "foodNutrients" in detail_data and isinstance(detail_data["foodNutrients"], list):
                # Extract nutrient values safely
                nutrients = {
                    nutrient["nutrient"]["id"]: nutrient.get("amount", 0)
                    for nutrient in detail_data["foodNutrients"]
                    if "nutrient" in nutrient and "id" in nutrient["nutrient"]
                }

                # Handle Calories properly
                calories = nutrients.get(1008, None)  # Standard Calories (kcal)
                atwater_general = nutrients.get(2047, None)  # Atwater General Factors
                atwater_specific = nutrients.get(2048, None)  # Atwater Specific Factors
                energy_kj = nutrients.get(1002, None)  # Energy in kJ

                # Choose the best available calorie value
                if calories is None or calories == 0:
                    if atwater_general is not None and atwater_general > 0:
                        calories = atwater_general
                    elif atwater_specific is not None and atwater_specific > 0:
                        calories = atwater_specific
                    elif energy_kj is not None and energy_kj > 0:
                        calories = round(energy_kj * 0.239, 2)  # Convert kJ to kcal
                    else:
                        calories = "Not Available"

                # Scale Nutrients Based on Serving Size
                scale_factor = serving_size / 100  # Convert to user-selected portion
                scaled_nutrients = {
                    nutrient_name: round(nutrients.get(nutrient_id, 0) * scale_factor, 2)
                    for nutrient_id, nutrient_name in macronutrient_ids.items()
                }

                # Print Scaled Nutrient Values
                for nutrient_name, value in scaled_nutrients.items():
                    unit = "KCAL" if "Calories" in nutrient_name else "G"
                    print(f"{nutrient_name}: {value} {unit}")

            else:
                print("No nutrient data available for this food.")
        else:
            print(f"Error fetching details for FDC ID {fdc_id}: {detail_response.status_code}")

    else:
        print("No food data found. Try a different search term.")
else:
    print(f"Error {search_response.status_code}: {search_response.text}")