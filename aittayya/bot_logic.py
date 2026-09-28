# -*- coding: utf-8 -*-

import os
import logging
import time
import json
from typing import List, Dict, Any, Optional, Tuple
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
from math import radians, sin, cos, sqrt, atan2
from collections import defaultdict

load_dotenv()

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Constants: Links for static map information ---
MAY_I_HELP_YOU_LINK = "https://www.google.com/maps/d/edit?mid=1lQ4zD04ZmkEiyBxQ1V_5K50-jqGtkNk&usp=sharing"
MEDICAL_CAMP_LINK = "https://www.google.com/maps/d/edit?mid=1v2Zh3ByOFUEnzcS-6LZNL4WfY1KUbUU&usp=sharing"
MOBILE_TOILET_LINK = "https://www.google.com/maps/d/edit?mid=1MnU5kUKjccIr1c32vXeCOHhogmmHmaY&usp=sharing"
DRINKING_WATER_LINK = "https://www.google.com/maps/d/edit?mid=1iGbFoR4XsJ8J9PCY-cc7sSl5vW0OCa4&usp=sharing"
AMBULANCE_LINK = "https://www.google.com/maps/d/edit?mid=1lGurk2yIIMa5IzEWHk_FyrpW2hAs2yU&usp=sharing"

# --- Text dictionary for English and Tamil languages ---
MENU_TEXTS = {
    "en": {
        "welcome_message": "Vanakkam {user_name}! I am AIட்டையா, your digital assistant for Tiruchendur.",
        "language_selected": "You have selected {language_name}.",
        "main_menu_prompt": "How can I assist you today?",
        "option_vehicle_parking": "1. 🅿️ Four-Wheeler Parking",
        "option_temp_bus_stand": "2. 🚍 Temporary Bus Stand",
        "option_two_wheeler_parking": "3. 🏍️ Two-Wheeler Parking",
        "option_may_i_help_you": "4. 🤝 May I Help You Desk",
        "option_medical_camps": "5. 🏥 Medical Camps",
        "option_mobile_toilets": "6. 🚻 Mobile Toilets",
        "option_drinking_water": "7. 💧 Drinking Water Locations",
        "option_ambulance_points": "8. 🚑 Ambulance Points",
        "option_change_language": "9. Change Language",
        "option_end_conversation_text": "\nType 'X' to End Conversation.",
        "invalid_menu_option": "Invalid option. Please type a number from the menu or 'X' to end.",
        "route_prompt": "Which route are you arriving from?",
        "locations_for_route_title": "--- Available Locations for {RouteName} Route ---",
        "no_locations_available": "Sorry, no suitable spots are currently available for this selection.",
        "location_details_format": "\n📍 {LocationName}\n🗺️ {ViewMapLink}",
        "goodbye_message": "Thank you for using our service. Stay safe!",
        "view_on_map": "View on Map",
        "may_i_help_you_response": f"Here are the locations for 'May I Help You' desks:\n<a href='{MAY_I_HELP_YOU_LINK}' target='_blank'>Open Map</a>",
        "medical_camp_response": f"Here are the locations for Medical Camps:\n<a href='{MEDICAL_CAMP_LINK}' target='_blank'>Open Map</a>",
        "mobile_toilet_response": f"Here are the locations for Mobile Toilets:\n<a href='{MOBILE_TOILET_LINK}' target='_blank'>Open Map</a>",
        "drinking_water_response": f"Here are the locations for Drinking Water:\n<a href='{DRINKING_WATER_LINK}' target='_blank'>Open Map</a>",
        "ambulance_response": f"Here are the locations for Ambulance points:\n<a href='{AMBULANCE_LINK}' target='_blank'>Open Map</a>",
        "button_route_tin": "Tirunelveli Route",
        "button_route_tut": "Thoothukudi Route",
        "button_route_ngl": "Nagercoil Route",
    },
    "ta": {
        "welcome_message": "வணக்கம் {user_name}! நான் AIட்டையா, திருச்செந்தூருக்கான உங்கள் டிஜிட்டல் உதவியாளர்.",
        "language_selected": "நீங்கள் {language_name} தேர்ந்தெடுத்துள்ளீர்கள்.",
        "main_menu_prompt": "இன்று நான் உங்களுக்கு எப்படி உதவ முடியும்?",
        "option_vehicle_parking": "1. 🅿️ நான்கு சக்கர வாகன நிறுத்தம்",
        "option_temp_bus_stand": "2. 🚍 தற்காலிக பேருந்து நிறுத்தம்",
        "option_two_wheeler_parking": "3. 🏍️ இரு சக்கர வாகன நிறுத்தம்",
        "option_may_i_help_you": "4. 🤝 நான் உதவலாமா மையம்",
        "option_medical_camps": "5. 🏥 மருத்துவ முகாம்கள்",
        "option_mobile_toilets": "6. 🚻 நடமாடும் கழிப்பறைகள்",
        "option_drinking_water": "7. 💧 குடிநீர் இடங்கள்",
        "option_ambulance_points": "8. 🚑 ஆம்புலன்ஸ் இடங்கள்",
        "option_change_language": "9. மொழியை மாற்று",
        "option_end_conversation_text": "\nஉரையாடலை முடிக்க 'X' என டைப் செய்யவும்.",
        "invalid_menu_option": "தவறான தேர்வு. மெனுவில் இருந்து ஒரு எண்ணை டைப் செய்யவும் அல்லது முடிக்க 'X' ஐ டைப் செய்யவும்.",
        "route_prompt": "நீங்கள் எந்த வழியில் வருகிறீர்கள்?",
        "locations_for_route_title": "--- {RouteName} வழித்தடத்திற்கான இடங்கள் ---",
        "no_locations_available": "மன்னிக்கவும், இந்தத் தேர்வுக்கு பொருத்தமான இடங்கள் தற்போது இல்லை.",
        "location_details_format": "\n📍 {LocationName}\n🗺️ {ViewMapLink}",
        "goodbye_message": "நன்றி! வணக்கம்!",
        "view_on_map": "வரைபடத்தில் காண்க",
        "may_i_help_you_response": f"நான் உதவலாமா மையங்களின் இடங்கள் இங்கே:\n<a href='{MAY_I_HELP_YOU_LINK}' target='_blank'>வரைபடத்தைத் திறக்கவும்</a>",
        "medical_camp_response": f"மருத்துவ முகாம்களுக்கான இடங்கள் இங்கே:\n<a href='{MEDICAL_CAMP_LINK}' target='_blank'>வரைபடத்தைத் திறக்கவும்</a>",
        "mobile_toilet_response": f"நடமாடும் கழிப்பறைகளுக்கான இடங்கள் இங்கே:\n<a href='{MOBILE_TOILET_LINK}' target='_blank'>வரைபடத்தைத் திறக்கவும்</a>",
        "drinking_water_response": f"குடிநீர் இடங்கள் இங்கே:\n<a href='{DRINKING_WATER_LINK}' target='_blank'>வரைபடத்தைத் திறக்கவும்</a>",
        "ambulance_response": f"ஆம்புலன்ஸ் இடங்கள் இங்கே:\n<a href='{AMBULANCE_LINK}' target='_blank'>வரைபடத்தைத் திறக்கவும்</a>",
        "button_route_tin": "திருநெல்வேலி சாலை",
        "button_route_tut": "தூத்துக்குடி சாலை",
        "button_route_ngl": "நாகர்கோவில் சாலை",
    }
}
SUPPORTED_LANGUAGES = { "en": {"name": "English"}, "ta": {"name": "தமிழ் (Tamil)"} }
ROUTE_NAME_MAP = { "TUT": "Thoothukudi", "TIN": "Tirunelveli", "NGL": "Nagercoil" }

class BotLogic:
    def __init__(self):
        logger.info("Stateless BotLogic class initialized.")
        self.PARKING_LOTS_CACHE = []
        self.WEBSITE_CONTENT_CACHE = {}
        self.LAST_FETCH_TIME = 0
        self.CACHE_DURATION = 60
        self.db = None
        self.initialize_firestore()
        self._preload_data()

    def initialize_firestore(self):
        if firebase_admin._apps:
            if not self.db: self.db = firestore.client()
            return
        try:
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred)
            self.db = firestore.client()
            logger.info("Firestore initialized successfully using Application Default Credentials.")
        except Exception as e:
            logger.error(f"Failed to initialize Firestore: {e}", exc_info=True)
            raise e

    def _preload_data(self):
        if not self.db: return
        self.fetch_all_parking_lots(force_refresh=True)
        self.fetch_website_content(force_refresh=True)

    def fetch_website_content(self, force_refresh: bool = False):
        if (not force_refresh) and (time.time() - self.LAST_FETCH_TIME < self.CACHE_DURATION) and self.WEBSITE_CONTENT_CACHE:
            return self.WEBSITE_CONTENT_CACHE
        if not self.db: return {}
        try:
            doc_ref = self.db.collection('website_content').document('landing_page')
            doc = doc_ref.get()
            if doc.exists:
                self.WEBSITE_CONTENT_CACHE = doc.to_dict()
                self.LAST_FETCH_TIME = time.time()
                logger.info("Successfully fetched website content.")
            else:
                self.WEBSITE_CONTENT_CACHE = {}
                logger.warning("Website content document 'landing_page' not found.")
        except Exception as e:
            logger.error(f"Error fetching website content: {e}", exc_info=True)
            self.WEBSITE_CONTENT_CACHE = {}
        return self.WEBSITE_CONTENT_CACHE

    def fetch_firestore_collection(self, collection_name: str) -> List[Dict[str, Any]]:
        if not self.db: return []
        try:
            return [doc.to_dict() for doc in self.db.collection(collection_name).stream()]
        except Exception as e:
            logger.error(f"Error fetching Firestore collection '{collection_name}': {e}", exc_info=True)
            return []
            
    def fetch_all_parking_lots(self, force_refresh: bool = False):
        if (not force_refresh) and (time.time() - self.LAST_FETCH_TIME < self.CACHE_DURATION) and self.PARKING_LOTS_CACHE:
            return
        self.PARKING_LOTS_CACHE = self.fetch_firestore_collection("parking_lots")
        self.LAST_FETCH_TIME = time.time()
        
    def _get_response_structure(self, text="", photos=None, buttons=None):
        return {"text": text, "photos": photos or [], "buttons": buttons or []}

    def process_user_input(self, user_id: str, input_type: str, data: Any, user_name: str, current_state: Dict) -> Tuple[List[Dict], Dict]:
        state = current_state.copy()
        text_input = str(data).strip()

        if text_input == "START_ENGLISH_CHAT":
            state = {'lang': 'en', 'menu_level': 'main_menu'}
            welcome_msg = self._get_response_structure(text=self.get_text(state, 'welcome_message', user_name=user_name))
            menu_msg = self._get_response_structure(text=self._get_menu_text(state))
            return [welcome_msg, menu_msg], state
            
        if text_input == "START_TAMIL_CHAT":
            state = {'lang': 'ta', 'menu_level': 'main_menu'}
            welcome_msg = self._get_response_structure(text=self.get_text(state, 'welcome_message', user_name=user_name))
            menu_msg = self._get_response_structure(text=self._get_menu_text(state))
            return [welcome_msg, menu_msg], state

        if text_input.lower() == 'x':
            return [self._get_response_structure(self.get_text(state, "goodbye_message"))], {}

        current_level = state.get('menu_level', 'main_menu')
        handler_name = f"_handle_{current_level}"
        handler = getattr(self, handler_name, self._handle_main_menu)
        
        return handler(state, text_input)

    def _handle_main_menu(self, state, choice):
        if choice == '9': return self._change_language(state)

        # Vehicle Parking, Bus Stand, and Two-wheeler all now require a route.
        if choice in ['1', '2', '3']:
            state['menu_level'] = 'route_prompt'
            if choice == '1': state['type'] = '4w'
            elif choice == '2': state['type'] = 'bus'
            elif choice == '3': state['type'] = '2w'

            prompt_text = self.get_text(state, "route_prompt")
            buttons = self._get_route_buttons(state)
            return [self._get_response_structure(text=prompt_text, buttons=buttons)], state
        
        # Static menu options
        menu_actions = {
            "4": self.get_text(state, "may_i_help_you_response"),
            "5": self.get_text(state, "medical_camp_response"),
            "6": self.get_text(state, "mobile_toilet_response"),
            "7": self.get_text(state, "drinking_water_response"),
            "8": self.get_text(state, "ambulance_response"),
        }
        result_text = menu_actions.get(choice)

        if result_text:
            state['menu_level'] = 'main_menu'
            return [self._get_response_structure(text=result_text), self._get_response_structure(text=self._get_menu_text(state))], state
        
        # Invalid option
        state['menu_level'] = 'main_menu'
        return [self._get_response_structure(text=self.get_text(state, 'invalid_menu_option')), self._get_response_structure(text=self._get_menu_text(state))], state

    def _handle_route_prompt(self, state, text_input):
        route_map = {"1": "TIN", "2": "TUT", "3": "NGL"}
        route_code = route_map.get(text_input)
        
        if route_code:
            state["menu_level"] = "main_menu"
            vehicle_type = state.get('type')
            
            # Determine keyword based on the type stored in state
            if vehicle_type == '4w': keyword = 'AVAILABLE'
            elif vehicle_type == 'bus': keyword = 'Busstand'
            elif vehicle_type == '2w': keyword = '2 wheeler'
            else:
                # Fallback for an unlikely error case
                reply_text = self.get_text(state, 'no_locations_available')
                return [self._get_response_structure(text=reply_text), self._get_response_structure(text=self._get_menu_text(state))], state

            reply_text = self._find_locations_by_route_and_type(state, route_preference=route_code, keyword=keyword)
            return [self._get_response_structure(text=reply_text), self._get_response_structure(text=self._get_menu_text(state))], state
        else:
            # If invalid route, ask again
            state["menu_level"] = "route_prompt"
            response_text = f"Invalid route selection.\n\n{self.get_text(state, 'route_prompt')}"
            buttons = self._get_route_buttons(state)
            return [self._get_response_structure(text=response_text, buttons=buttons)], state

    def _handle_change_language(self, state, text_input):
        if text_input in SUPPORTED_LANGUAGES:
            state['lang'] = text_input
            state['menu_level'] = 'main_menu'
            lang_selected_msg = self._get_response_structure(text=self.get_text(state, 'language_selected', language_name=SUPPORTED_LANGUAGES[text_input]['name']))
            menu_msg = self._get_response_structure(text=self._get_menu_text(state))
            return [lang_selected_msg, menu_msg], state
        else:
            return self._change_language(state)

    def _change_language(self, state):
        state['menu_level'] = 'change_language'
        text = "Please select your language:"
        buttons = [{"text": "English", "payload": "en"}, {"text": "தமிழ் (Tamil)", "payload": "ta"}]
        return [self._get_response_structure(text=text, buttons=buttons)], state

    def get_text(self, state: Dict, key: str, **kwargs) -> str:
        lang = state.get('lang', 'en')
        template_string = MENU_TEXTS.get(lang, {}).get(key, MENU_TEXTS["en"].get(key))
        return template_string.format_map(defaultdict(str, **kwargs))

    def _get_menu_text(self, state: Dict) -> str:
        # Corrected order of menu items
        text_keys = [
            "main_menu_prompt", "option_vehicle_parking", "option_temp_bus_stand", 
            "option_two_wheeler_parking", "option_may_i_help_you", "option_medical_camps", 
            "option_mobile_toilets", "option_drinking_water", "option_ambulance_points",
            "option_change_language", "option_end_conversation_text"
        ]
        return "\n".join([self.get_text(state, key) for key in text_keys])

    def _get_route_buttons(self, state: Dict) -> List[Dict]:
        return [
            {'text': self.get_text(state, 'button_route_tin'), 'payload': '1'},
            {'text': self.get_text(state, 'button_route_tut'), 'payload': '2'},
            {'text': self.get_text(state, 'button_route_ngl'), 'payload': '3'},
        ]
        
    def _find_locations_by_route_and_type(self, state: Dict, route_preference: str, keyword: str) -> str:
        self.fetch_all_parking_lots(force_refresh=True)
        keyword_lower = keyword.lower()

        applicable_lots = [
            lot for lot in self.PARKING_LOTS_CACHE 
            if str(lot.get("route", "")).strip().upper() == route_preference
            and lot.get('user_for_this_function', False)
            and keyword_lower in str(lot.get('available_closed', '')).lower()
        ]
        
        if not applicable_lots:
            return self.get_text(state, "no_locations_available")

        sorted_lots = sorted(applicable_lots, key=lambda x: x.get('parkinglotid', 'P999'))
        
        route_display_name = ROUTE_NAME_MAP.get(route_preference, "Selected")
        title = self.get_text(state, "locations_for_route_title", RouteName=route_display_name)
        
        details_list = []
        for lot in sorted_lots:
            try:
                coords_str = lot.get('parking_way_coordinates')
                if not coords_str: continue

                map_link = f"<a href='https://www.google.com/maps?q={coords_str}' target='_blank'>{self.get_text(state, 'view_on_map')}</a>"
                details = self.get_text(state, "location_details_format", 
                    LocationName=lot.get("parking_name", "Unknown"), 
                    ViewMapLink=map_link
                )
                details_list.append(details)
            except Exception:
                continue

        if not details_list:
            return self.get_text(state, "no_locations_available")
            
        return f"{title}\n" + "\n".join(details_list)