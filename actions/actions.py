import difflib
import random

from typing import Text, List, Any, Dict, Optional
from rasa_sdk import Tracker, FormValidationAction, Action
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from rasa_sdk.events import SlotSet, ConversationPaused, UserUtteranceReverted, LoopInterrupted, EventType

from actions.api import API
from actions.clean_slot import CleanSlot


class GenerateDiet(Action):
    def name(self) -> Text:
        return "action_generate_diet"

    async def run(
            self, dispatcher, tracker: Tracker, domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        diet = tracker.get_slot("diet") or ''
        if tracker.get_slot("has_allergens") is False:
            intolerances = []
        else:
            intolerances = tracker.get_slot("allergens") or ''

        goal = tracker.get_slot("goal")
        height = tracker.get_slot("height")
        weight = tracker.get_slot("weight")
        age = tracker.get_slot("age")
        gender = tracker.get_slot("gender")
        activity_level = tracker.get_slot("activity_level")

        data_calories = await API.get_target_calories(height, weight, age, gender, activity_level)
        if goal == 'lose_weight':
            calories = data_calories['data']['goals']['Weight loss']['calory']
        elif goal == 'gain_weight':
            calories = data_calories['data']['goals']['Weight gain']['calory']
        else:
            calories = data_calories['data']['goals']['maintain weight']

        calories = int(calories)

        data_meal = await API.generate_meal_plan(diet, intolerances, calories)
        meals = data_meal['meals']
        meals_title = [meal['title'] for meal in meals]
        meals_url = [meal['sourceUrl'] for meal in meals]
        meals_id = [meal['id'] for meal in meals]
        nutrients = data_meal['nutrients']

        if meals:
            message = f'Your meal plan consists of the following meals to be taken at breakfast, lunch and dinner respectively.\n'
            message += f'The meal for the day amounts to {nutrients["calories"]} calories (carbohydrates: {int(nutrients["carbohydrates"])}g, protein: {int(nutrients["protein"])}g, fat: {int(nutrients["fat"])}g)'
            dispatcher.utter_message(text=message)

            for index, (meal_id, meal_title, meal_url) in enumerate(zip(meals_id, meals_title, meals_url), 1):
                img_url = await API.get_recipe_card(meal_id)
                meal_string = f'{index}. {meal_title} ({meal_url})\n'
                dispatcher.utter_message(image=img_url, text=meal_string)

        else:
            message = 'No meals found. Please try again.'
            dispatcher.utter_message(text=message)

        return [SlotSet("confirm", None), LoopInterrupted(True, None)]


class ValidateDietForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_diet_form"

    @staticmethod
    def diet_db() -> List[Text]:
        return ["", "Gluten Free", "Ketogenic", "Vegetarian", "Lacto-Vegetarian", "Ovo-Vegetarian", "Vegan",
                "Pescetarian", "Paleo", "Primal", "Low FODMAP", "Whole30"]

    @staticmethod
    def intolerances_db() -> List[Text]:
        return ["dairy", "egg", "gluten", "grain", "peanut", "seafood",
                "sesame", "shellfish", "soy", "sulfite", "tree nut", "wheat"]

    async def required_slots(
            self,
            domain_slots: List[Text],
            dispatcher: "CollectingDispatcher",
            tracker: "Tracker",
            domain: "DomainDict",
    ) -> List[Text]:
        updated_slots = domain_slots.copy()
        if tracker.slots.get("has_allergens") is False:
            updated_slots.remove("allergens")
        return updated_slots

    def validate_goal(
            self,
            slot_value: Any,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: DomainDict,
    ) -> Dict[Text, Any]:
        if slot_value in ['lose_weight', 'gain_weight', 'maintain_weight']:
            return {"goal": slot_value}
        return {"goal": None}

    def validate_diet(
            self,
            slot_value: Any,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: DomainDict,
    ) -> Dict[Text, Any]:
        if tracker.get_intent_of_latest_message() in ["inform_no_diet", "deny"]:
            return {"diet": ""}
        else:
            diet_matches = difflib.get_close_matches(slot_value, self.diet_db())
            diet = diet_matches[0] if diet_matches else None
            if diet in self.diet_db():
                return {"diet": diet}
            else:
                dispatcher.utter_message(
                    text=f'Please choose from the following diets: {", ".join(self.diet_db()[1:])}.')
                return {"diet": None}

    def validate_has_allergens(
            self,
            slot_value: Any,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: DomainDict,
    ) -> Dict[Text, Any]:
        if slot_value is True:
            return {"has_allergens": True}
        elif slot_value is False:
            return {"has_allergens": False}
        else:
            return {"has_allergens": None}

    def validate_allergens(
            self,
            slot_value: Any,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: DomainDict,
    ) -> Dict[Text, Any]:
        matching_allergens = []
        for item in slot_value:
            matches = difflib.get_close_matches(item, self.intolerances_db(), n=len(self.intolerances_db()))
            current_matching_allergens = [allergen for allergen in self.intolerances_db() if allergen in matches]
            matching_allergens += current_matching_allergens

        # remove duplicates from the list of matching allergens
        matching_allergens = list(set(matching_allergens))

        if all(allergen in self.intolerances_db() for allergen in matching_allergens):
            return {"has_allergens": True, "allergens": matching_allergens}
        else:
            dispatcher.utter_message(
                text=f'Unfortunately, we only cater for the following allergens: {", ".join(self.intolerances_db())}.')
            return {"allergens": None}

    def validate_height(
            self,
            slot_value: Any,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: DomainDict,
    ) -> Dict[Text, Any]:
        height = CleanSlot.height(slot_value)
        return {"height": height}

    def validate_weight(
            self,
            slot_value: Any,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: DomainDict,
    ) -> Dict[Text, Any]:
        weight = CleanSlot.weight(slot_value)
        return {"weight": weight}

    def validate_age(
            self,
            slot_value: Any,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: DomainDict,
    ) -> Dict[Text, Any]:
        age = CleanSlot.age(slot_value)
        return {"age": age}

    def validate_gender(
            self,
            slot_value: Any,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: DomainDict,
    ) -> Dict[Text, Any]:
        if slot_value not in ["male", "female"]:
            # dispatcher.utter_message(text=f'Please provide a valid gender. (male or female)')
            return {"gender": random.choice(["male", "female"])}
        return {"gender": slot_value}

    def validate_activity_level(
            self,
            slot_value: Any,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: DomainDict,
    ) -> Dict[Text, Any]:
        activity_level = int(float(slot_value))
        if activity_level in [1, 2, 3, 4, 5]:
            return {"activity_level": activity_level}
        return {"activity_level": None}

    def validate_confirm(
            self,
            slot_value: Any,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: DomainDict,
    ) -> Dict[Text, Any]:
        return {"confirm": slot_value}


class AskForConfirmation(Action):
    def name(self) -> Text:
        return "action_ask_confirm"

    def run(
            self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        goal = tracker.slots.get("goal")
        diet = tracker.slots.get("diet")
        height = tracker.slots.get("height")
        weight = tracker.slots.get("weight")
        age = tracker.slots.get("age")
        gender = tracker.slots.get("gender")
        activity_level = tracker.slots.get("activity_level")

        message = f"Great! I can now generate a customised meal plan for you.\n\nBased on the information you provided, I will create a {diet} diet designed to help you {goal.replace('_', ' ')} at {age} years old. As per your physical attributes, you mentioned being a {gender} standing at {height}cm tall, weighing {weight}kg and being {activity_level * 20}% active. "
        allergens = tracker.slots.get("allergens")
        if allergens not in [None, []]:
            message += f"I will also consider that you are allergic to {', '.join(allergens)}."
        else:
            message += "You also confirm not having any allergies."

        message += "\n\nDo you want to continue? If not, please specify any changes you would like to make before generating the meal plan."
        dispatcher.utter_message(text=message, buttons=[{"title": "Continue", "payload": "/affirm"}])
        return []


class AskForDetails(Action):
    def name(self) -> Text:
        return "action_ask_details"

    def run(
            self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        slots = ['height', 'weight', 'age', 'gender']
        requested_slots = [slot for slot in slots if tracker.slots.get(slot) is None]

        start_string_list = ["Please provide your", "Could you please share your", "I will now need your"]

        if len(requested_slots) > 1:
            message = f"{random.choice(start_string_list)} {', '.join(requested_slots[:-1])} and {requested_slots[-1]}."
            message += "\n\nYou can specify all your details in one line and in metric format (e.g. 170cm, 80kg, 25 years old, female)."
            dispatcher.utter_message(text=message)
        elif len(requested_slots) == 1:
            message = f"One last detail is needed. Can you provide your {requested_slots[0]}."
            dispatcher.utter_message(text=message)
        return []


class AskForHeight(Action):
    def name(self) -> Text:
        return "action_ask_height"

    def run(
            self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        return AskForDetails().run(dispatcher, tracker, domain)


class AskForWeight(Action):
    def name(self) -> Text:
        return "action_ask_weight"

    def run(
            self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        return AskForDetails().run(dispatcher, tracker, domain)


class AskForAge(Action):
    def name(self) -> Text:
        return "action_ask_age"

    def run(
            self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        return AskForDetails().run(dispatcher, tracker, domain)


class AskForGender(Action):
    def name(self) -> Text:
        return "action_ask_gender"

    def run(
            self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        return AskForDetails().run(dispatcher, tracker, domain)


class ActionConfirmSlotValues(Action):
    def name(self) -> Text:
        return "action_confirm_slot_values"

    def run(
            self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        if tracker.get_slot("allergens") is []:
            return [SlotSet("has_allergens", False), SlotSet("allergens", None)]
        return []
