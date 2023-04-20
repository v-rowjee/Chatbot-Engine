import difflib
import requests

from typing import Text, List, Any, Dict, Optional
from rasa_sdk import Tracker, FormValidationAction, Action
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from rasa_sdk.events import SlotSet, ConversationPaused, UserUtteranceReverted


class GenerateDiet(Action):
    def name(self) -> Text:
        return "action_generate_diet"

    async def generate_meal_plan(self, diet, intolerances):
        url = 'https://api.spoonacular.com/mealplanner/generate'
        api_key = '3bc2008b2a0647d48ef82793932f96f5'
        params = {
            'timeFrame': 'day',
            'targetCalories': '2500',
            'diet': diet,
            'exclude': ','.join(intolerances),
            'apiKey': api_key
        }
        response = requests.get(url, params=params)
        return response.json()

    async def run(
            self, dispatcher, tracker: Tracker, domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        diet = tracker.get_slot("diet") or ''
        if tracker.get_slot("ask_allergens") is False:
            intolerances = []
        else:
            intolerances = tracker.get_slot("allergens") or ''
        # calories = 2500

        data = await self.generate_meal_plan(diet, intolerances)
        meals = data['meals']
        meals_title = [meal['title'] for meal in meals]
        nutrients = data['nutrients']
        message = f'Your meal plan consists of: {", ".join(meals_title)} to be taken at breakfast, lunch and dinner respectively. '
        message += f'The meal for the day amounts to {nutrients["calories"]} calories (carbohydrates: {nutrients["carbohydrates"]}, protein: {nutrients["protein"]}, fat: {nutrients["fat"]})'
        dispatcher.utter_message(text=message)

        return []


class ValidateDietForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_diet_form"

    @staticmethod
    def diet_db() -> List[Text]:
        return ["Gluten Free", "Ketogenic", "Vegetarian", "Lacto-Vegetarian", "Ovo-Vegetarian", "Vegan",
                "Pescetarian", "Paleo", "Primal", "Low FODMAP", "Whole30"]

    @staticmethod
    def intolerances_db() -> List[Text]:
        return ["dairy", "egg", "gluten", "grain", "peanut", "seafood",
                "sesame", "shellfish", "soy", "sulfite", "nut", "wheat"]

    async def required_slots(
            self,
            domain_slots: List[Text],
            dispatcher: "CollectingDispatcher",
            tracker: "Tracker",
            domain: "DomainDict",
    ) -> List[Text]:
        updated_slots = domain_slots.copy()
        if tracker.slots.get("ask_allergens") is False:
            updated_slots.remove("allergens")
        return updated_slots

    def validate_ask_allergens(
            self,
            slot_value: Any,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: DomainDict,
    ) -> Dict[Text, Any]:
        if slot_value is True:
            return {"ask_allergens": True}
        else:
            return {"ask_allergens": False}

    def validate_diet(
            self,
            slot_value: Any,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: DomainDict,
    ) -> Dict[Text, Any]:
        diet_matches = difflib.get_close_matches(slot_value.lower(), self.diet_db())
        diet = diet_matches[0] if diet_matches else None
        if diet in self.diet_db():
            return {"diet": diet}
        else:
            dispatcher.utter_message(text=f'Please choose from the following diets: {", ".join(self.diet_db())}.')
            return {"diet": None}

    def validate_allergens(
            self,
            slot_value: Any,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: DomainDict,
    ) -> Dict[Text, Any]:

        matching_allergens = []
        for item in slot_value:
            matches = difflib.get_close_matches(item, self.intolerances_db(), n=len(self.intolerances_db()), cutoff=0.6)
            current_matching_allergens = [allergen for allergen in self.intolerances_db() if allergen in matches]
            matching_allergens += current_matching_allergens

        # remove duplicates from the list of matching allergens
        matching_allergens = list(set(matching_allergens))

        if all(allergen in self.intolerances_db() for allergen in matching_allergens):
            return {"allergens": matching_allergens}
        else:
            dispatcher.utter_message(
                text=f'Unfortunately, we only cater for the following allergens: {", ".join(self.intolerances_db())}.')
            return {"allergens": None}
