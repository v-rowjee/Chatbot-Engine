import requests


class API:
    @staticmethod
    async def generate_meal_plan(diet, intolerances, target_calories):
        url = 'https://api.spoonacular.com/mealplanner/generate'
        api_key = '3bc2008b2a0647d48ef82793932f96f5'
        params = {
            'timeFrame': 'day',
            'targetCalories': target_calories,
            'diet': diet,
            'exclude': ','.join(intolerances),
            'apiKey': api_key
        }
        response = requests.get(url, params=params)
        return response.json()

    @staticmethod
    async def get_target_calories(height, weight, age, gender, activity_level):
        url = "https://fitness-calculator.p.rapidapi.com/dailycalorie"
        api_key = '0087bd246emsh48078e1256c1fb0p1b1c91jsn7d50e485893d'
        params = {"age": f"{age}", "gender": f"{gender}", "height": f"{height}", "weight": f"{weight}",
                  "activitylevel": f"level_{activity_level}"}
        headers = {
            "content-type": "application/octet-stream",
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": "fitness-calculator.p.rapidapi.com"
        }

        response = requests.get(url, headers=headers, params=params)

        return response.json()
