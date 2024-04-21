import requests

API_KEY = "4542ec46de1643b09c1f06550d95a510"


def search_by_ingredients(ingredients):
    endpoint = "https://api.spoonacular.com/recipes/findByIngredients"

    payload = {
        "ingredients": ingredients,
        "ranking": 2
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
