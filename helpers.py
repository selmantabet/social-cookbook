import requests
from flask import session
from flask_login import current_user
from flask_uploads import UploadSet, configure_uploads, IMAGES
import json
import os
from app import db, app

API_KEY = "4542ec46de1643b09c1f06550d95a510"
CUISINES = ["African", "Asian", "American", "British", "Cajun", "Caribbean", "Chinese", "Eastern European", "European", "French", "German",
            "Greek", "Indian", "Irish", "Italian", "Japanese", "Jewish", "Korean", "Latin American", "Mediterranean", "Mexican", "Middle Eastern",
            "Nordic", "Southern", "Spanish", "Thai", "Vietnamese"]
DIET_TITLES = ["Omnivore (Unrestricted)", "Vegetarian", "Vegan", "Gluten-free", "Paleo", "Keto", "Lacto-Vegetarian", "Ovo-Vegetarian",  "Pescetarian",
               "Primal", "Whole30", "Low FODMAP"]
DIET_VALUES = ["omnivore", "vegetarian", "vegan", "gluten free", "paleo", "ketogenic", "lacto-vegetarian", "ovo-vegetarian", "pescetarian",
               "primal", "whole30", "low fodmap"]
TASTE_TITLES = ["Salty", "Spicy",
                "Sour", "Sweet",  "Bitter", "Fatty", "Savory"]
TASTE_VALUES = ["salty", "spicy", "sour", "sweet", "bitter", "fatty", "savory"]
ALLERGY_TITLES = ["Peanut", "Dairy", "Soy", "Shellfish", "Seafood", "Egg", "Sulfite", "Gluten", "Sesame", "Tree Nut", "Grain",
                  "Wheat"]
ALLERGY_VALUES = ["peanut", "dairy", "soy", "shellfish", "seafood", "egg", "sulfite", "gluten", "sesame", "tree nut", "grain",
                  "wheat"]
DIETS = list(zip(DIET_TITLES, DIET_VALUES))
TASTES = list(zip(TASTE_TITLES, TASTE_VALUES))
ALLERGIES = list(zip(ALLERGY_TITLES, ALLERGY_VALUES))
DEFAULT_PROFILE = {
    "cuisines": [],
    "taste": {
        "salty": 50, "spicy": 50, "sour": 50, "sweet": 50, "bitter": 50, "fatty": 50, "savory": 50
    },
    "diet": "omnivore",
    "allergies": []
}
# This method was based on the docs here- https://flask-uploads.readthedocs.io/en/latest/
images = UploadSet('images', IMAGES)


def update_settings():
    settings = json.loads(current_user.settings_json)
    if session.get("colour_mode") is None:  # New account case
        session['colour_mode'] = 'light'
    settings['colour_mode'] = session['colour_mode']
    current_user.settings_json = json.dumps(settings)
    db.session.commit()
    return


def load_settings(settings_json):
    settings = json.loads(settings_json)
    session.update(settings)
    upload_dir = app.config["DEFAULT_UPLOAD_DEST"]
    user_dir = os.path.join(upload_dir, str(current_user.id))
    if not os.path.exists(user_dir):
        os.makedirs(user_dir)
    app.config["UPLOADED_IMAGES_DEST"] = user_dir
    # The uploads will now be saved in the user's folder
    configure_uploads(app, images)
    return


def clear_settings():
    color_mode = session.get('colour_mode')
    session.clear()
    session['color_mode'] = color_mode
    app.config["UPLOADED_IMAGES_DEST"] = app.config["DEFAULT_UPLOAD_DEST"]
    return


def reset_user_settings(user):
    settings = json.loads(user.settings_json)
    defaults = {
        "has_dp": False,
        "colour_mode": "light"
    }
    settings.update(defaults)
    user.settings_json = json.dumps(settings)
    db.session.commit()
    return


def clear_dp(user):
    user.settings_json = json.dumps({"has_dp": False})
    os.remove(os.path.join(app.config["UPLOADED_IMAGES_DEST"], "dp.jpg"))
    db.session.commit()
    return


def clear_food_profile(user):
    user.food_profile = json.dumps(DEFAULT_PROFILE)
    db.session.commit()
    return


def extract_req_profile(request):
    profile = {
        "cuisines": request.form.getlist("cuisines"),
        "taste": {
            "salty": int(request.form.get("salty")),
            "spicy": int(request.form.get("spicy")),
            "sour": int(request.form.get("sour")),
            "sweet": int(request.form.get("sweet")),
            "bitter": int(request.form.get("bitter")),
            "fatty": int(request.form.get("fatty")),
            "savory": int(request.form.get("savory"))
        },
        "diet": request.form.get("diet"),
        "allergies": request.form.getlist("allergies")
    }
    return profile


def execute_advanced_search(params):
    endpoint = "https://api.spoonacular.com/recipes/complexSearch"

    payload = {
        "query": ",".join(params.get("ingredients")),
        "cuisine": ",".join(params.get("cuisines")),
        "diet": params.get("diet"),
        "intolerances": ",".join(params.get("allergies")),

        "ranking": 1
    }
    headers = {
        'x-api-key': API_KEY
    }

    response = requests.request(
        "GET", endpoint, headers=headers, params=payload)
    return response.json()


def search_by_ingredients(ingredients):
    endpoint = "https://api.spoonacular.com/recipes/findByIngredients"

    payload = {
        "ingredients": ingredients,
        "ranking": 1
    }
    headers = {
        'x-api-key': API_KEY
    }

    response = requests.request(
        "GET", endpoint, headers=headers, params=payload)

    return response.json()


def search_by_recipe_id(recipe_id):
    endpoint = f"https://api.spoonacular.com/recipes/{recipe_id}/information"

    payload = {
        "includeNutrition": False
    }
    headers = {
        'x-api-key': API_KEY
    }

    response = requests.request(
        "GET", endpoint, headers=headers, params=payload)

    if response.status_code == 404:
        return None
    else:
        return response.json()


def random_recipes():
    endpoint = "https://api.spoonacular.com/recipes/random"

    payload = {
        "number": 10
    }
    headers = {
        'x-api-key': API_KEY
    }

    response = requests.request(
        "GET", endpoint, headers=headers, params=payload)

    return response.json().get('recipes')
