import difflib
import re
import requests

from random import choice
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
        nutrients = data_meal['nutrients']
        message = f'Your meal plan consists of: {", ".join(meals_title)} to be taken at breakfast, lunch and dinner respectively. '
        message += f'The meal for the day amounts to {nutrients["calories"]} calories (carbohydrates: {nutrients["carbohydrates"]}, protein: {nutrients["protein"]}, fat: {nutrients["fat"]})'
        dispatcher.utter_message(text=message)

        return [LoopInterrupted(True, None)]


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
        if tracker.slots.get("wants_detailed_diet") is False:
            updated_slots.remove("details")
            updated_slots.remove("height")
            updated_slots.remove("weight")
            updated_slots.remove("age")
            updated_slots.remove("gender")
            updated_slots.remove("activity_level")
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
        intent = tracker.latest_message["intent"].get("name")
        if intent == "deny":
            return {"diet": ""}
        if intent == "affirm":
            dispatcher.utter_message(text=f'Please choose from the following diets: {", ".join(self.diet_db())}.')
            return {"diet": None}

        diet_matches = difflib.get_close_matches(slot_value.lower(), self.diet_db())
        diet = diet_matches[0] if diet_matches else None
        if diet in self.diet_db():
            return {"diet": diet}
        else:
            dispatcher.utter_message(text=f'Please choose from the following diets: {", ".join(self.diet_db())}.')
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
        else:
            return {"has_allergens": False}

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
        return {"age": slot_value}

    def validate_gender(
            self,
            slot_value: Any,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: DomainDict,
    ) -> Dict[Text, Any]:
        if slot_value not in ["male", "female"]:
            return {"gender": choice(["male", "female"])}
        return {"gender": slot_value}

    def validate_activity_level(
            self,
            slot_value: Any,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: DomainDict,
    ) -> Dict[Text, Any]:
        activity_level = int(slot_value)
        if activity_level in [1, 2, 3, 4, 5]:
            return {"activity_level": activity_level}
        return {"activity_level": None}


class UtterSlotValues(Action):
    def name(self) -> Text:
        return "action_utter_slot_values"

    def run(
            self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        diet = tracker.slots.get("diet")
        height = tracker.slots.get("height")
        weight = tracker.slots.get("weight")
        age = tracker.slots.get("age")
        gender = tracker.slots.get("gender")
        activity_level = tracker.slots.get("activity_level")

        message = f"Generating a {diet} diet for a {age} year old {gender} who is {height}cm tall and weighs {weight}kg. You are also rated {activity_level}/5 active. "
        if tracker.slots.get("has_allergens") is True:
            allergens = tracker.slots.get("allergens")
            message += f"You also have the following allergens: {', '.join(allergens)}."
        else:
            message += "You have no allergens."
        dispatcher.utter_message(text=message)
        return []

class AskForHeight(Action):
    def name(self) -> Text:
        return "action_ask_height"

    def run(
            self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        requested_slots = []
        if tracker.slots.get("height") is None:
            requested_slots.append('height')
        if tracker.slots.get("weight") is None:
            requested_slots.append('weight')
        if tracker.slots.get("age") is None:
            requested_slots.append('age')
        if tracker.slots.get("gender") is None:
            requested_slots.append('gender')
        dispatcher.utter_message(text="Provide the following information: " + ", ".join(requested_slots))
        return []


class AskForWeight(Action):
    def name(self) -> Text:
        return "action_ask_weight"

    def run(
            self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        requested_slots = []
        if tracker.slots.get("height") is None:
            requested_slots.append('height')
        if tracker.slots.get("weight") is None:
            requested_slots.append('weight')
        if tracker.slots.get("age") is None:
            requested_slots.append('age')
        if tracker.slots.get("gender") is None:
            requested_slots.append('gender')
        dispatcher.utter_message(text="Provide the following information: " + ", ".join(requested_slots))
        return []


class AskForAge(Action):
    def name(self) -> Text:
        return "action_ask_age"

    def run(
            self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        requested_slots = []
        if tracker.slots.get("height") is None:
            requested_slots.append('height')
        if tracker.slots.get("weight") is None:
            requested_slots.append('weight')
        if tracker.slots.get("age") is None:
            requested_slots.append('age')
        if tracker.slots.get("gender") is None:
            requested_slots.append('gender')
        dispatcher.utter_message(text="Provide the following information: " + ", ".join(requested_slots))
        return []


class AskForGender(Action):
    def name(self) -> Text:
        return "action_ask_gender"

    def run(
            self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        requested_slots = []
        if tracker.slots.get("height") is None:
            requested_slots.append('height')
        if tracker.slots.get("weight") is None:
            requested_slots.append('weight')
        if tracker.slots.get("age") is None:
            requested_slots.append('age')
        if tracker.slots.get("gender") is None:
            requested_slots.append('gender')
        dispatcher.utter_message(text="Provide the following information: " + ", ".join(requested_slots))
        return []
