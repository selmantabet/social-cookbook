import requests
from flask import session, url_for
from flask_login import current_user
from flask_uploads import UploadSet, configure_uploads, IMAGES
import json
import os
from app import db, app


# Some constants
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
# Default DP from an icon on https://www.speechandlearning.com/sabrina-arizmendez
DEFAULT_DP = url_for('static', filename='default.jpg')
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
    payload = {}
    if params.get("ingredients") is None:
        payload["query"] = ""
    else:
        payload["query"] = ",".join(params.get("ingredients"))

    if params.get("cuisines") is None:
        payload["cuisine"] = ""
    else:
        payload["cuisine"] = ",".join(params.get("cuisines"))

    if params.get("allergies") is None:
        payload["intolerances"] = ""
    else:
        payload["intolerances"] = ",".join(params.get("allergies"))

    payload["diet"] = params.get("diet")
    payload["addRecipeInformation"] = True
    payload["ranking"] = 1

    headers = {
        'x-api-key': API_KEY
    }

    response = requests.request(
        "GET", endpoint, headers=headers, params=payload)
    # print("Response: ", json.dumps(response.json()))
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


def local_search(**params):
    from models import Recipe
    recipes = Recipe.query.all()
    scored_recipes = []
    for recipe in recipes:
        ingredients = json.loads(recipe.ingredients)
        allergies = recipe.allergies.split(",")
        score = 0
        if ingredients is not None:
            for ingredient in ingredients:
                if ingredient in params.get("ingredients"):
                    score += 1
        if params.get("cuisines") is not None:
            for cuisine in params.get("cuisines"):
                if cuisine in recipe.cuisines:
                    score += 1
        if params.get("diet") == recipe.diet:
            score += 1
        if params.get("allergies") is not None:
            for allergy in params.get("allergies"):
                if allergy in allergies:
                    score -= 1
        if score > 0:
            scored_recipes.append((recipe, score))
    scored_recipes.sort(key=lambda x: x[1], reverse=True)
    sorted_recipes = [recipe[0] for recipe in scored_recipes]
    print(sorted_recipes)
    result = {}
    for i in sorted_recipes:
        result[i.id] = i

    print(result)
    # json_result = json.dumps(result)
    return result


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
        "number": 8
    }
    headers = {
        'x-api-key': API_KEY
    }

    response = requests.request(
        "GET", endpoint, headers=headers, params=payload)

    return response.json().get('recipes')
