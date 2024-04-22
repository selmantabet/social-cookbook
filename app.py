from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
import os
import json

cwd = os.getcwd()
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cookbook.db/'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['DEFAULT_UPLOAD_DEST'] = os.path.join(
    cwd, "static", "uploads")  # Constant
# When the user logs on, the app will change the upload directory to the user's directory
app.config['UPLOADED_IMAGES_DEST'] = app.config['DEFAULT_UPLOAD_DEST']
app.config['ALLOWED_EXTENSIONS'] = set(['png', 'jpg', 'jpeg', 'gif'])

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


@app.route('/index', methods=['GET', 'POST'])
@app.route('/', methods=['GET', 'POST'])
def index():
    from forms import SearchForm
    search_form = SearchForm()
    if search_form.validate_on_submit():
        print("Search form submitted")
        query = ",".join(search_form.ingredients.data.split())
        return redirect(url_for('search', query=query))
    from models import Recipe
    from helpers import random_recipes
    recipes = random_recipes()
    return render_template('index.html', recipes=recipes, searchform=search_form, show_search=True)


@app.route('/register', methods=['GET', 'POST'])
def register():
    from models import User
    from forms import RegistrationForm
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, password=form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! You can now log in.')
        print(
            f"Successful registration: {form.username.data} / {form.password.data}")

        return redirect(url_for('login'))

    return render_template('registration.html', form=form)


@app.route('/search/<string:query>', methods=['GET', 'POST'])
@login_required
def search(query):
    from forms import SearchForm
    search_form = SearchForm()
    if search_form.validate_on_submit():
        print("Search form submitted")
        query = ",".join(search_form.ingredients.data.split())
        return redirect(url_for('search', query=query))
    print("Search query: ", query)
    from helpers import search_by_ingredients
    results = search_by_ingredients(query)
    return render_template('search.html', results=results, searchform=search_form, show_search=True)


# @app.route('/search', methods=['GET', 'POST'])
# def search():
#     query = request.args.get('query')
#     print("Search query: ", query)
#     return render_template('search.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    from models import User
    from forms import LoginForm
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user)
            flash(f'You have successfully logged in, {current_user.username}!')
            print("Logged in!")
            return redirect(url_for('index'))
        flash('Invalid username or password.')
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout successful.', 'success')
    return redirect(url_for('index'))


@app.route('/create_profile', methods=['GET', 'POST'])
@login_required
def create_profile():
    from helpers import load_settings, ALLERGIES, DIETS, TASTES, DEFAULT_PROFILE
    if session.get("food_profile") is not None:
        initial_data = session.get("food_profile")
    else:
        print("No profile found, using defaults.")
        initial_data = DEFAULT_PROFILE
    if request.method == 'POST':
        salty = request.form.get("salty")
        spicy = request.form.get("spicy")
        sour = request.form.get("sour")
        sweet = request.form.get("sweet")
        bitter = request.form.get("bitter")
        fatty = request.form.get("fatty")
        savory = request.form.get("savory")
        diet = request.form.get('diet')
        allergies = request.form.getlist('allergy')
        session['food_profile'] = {
            "taste": {
                "salty": salty, "spicy": spicy, "sour": sour, "sweet": sweet, "bitter": bitter, "fatty": fatty, "savory": savory
            },
            "diet": diet,
            "allergies": allergies
        }
        settings = json.loads(current_user.settings_json)
        settings['food_profile'] = session['food_profile']
        current_user.settings_json = json.dumps(settings)
        db.session.commit()
        flash('Profile updated successfully', 'success')

    return render_template('create_profile.html', tastes=TASTES, diets=DIETS, allergies=ALLERGIES, initial_data=initial_data)


@app.route('/add_recipe', methods=['GET', 'POST'])
@login_required
def add_recipe():
    from models import Recipe
    from forms import RecipeForm
    form = RecipeForm()
    if form.validate_on_submit():
        new_recipe = Recipe(
            title=form.title.data, ingredients=form.ingredients.data, instructions=form.instructions.data, user_id=current_user.id)
        db.session.add(new_recipe)
        db.session.commit()
        flash('Recipe added successfully', 'success')
        return redirect(url_for('index'))
    return render_template('add_recipe.html', form=form)


@app.route('/result/<int:result_id>')
def result(result_id):
    from helpers import search_by_recipe_id
    recipe = search_by_recipe_id(result_id)
    if recipe is None:
        flash('Recipe not found', 'error')
        return redirect(url_for('index'))
    return render_template('result.html', recipe=recipe)


@app.route('/view_recipe/<int:recipe_id>', methods=['GET', 'POST'])
def view_recipe(recipe_id):
    from models import Recipe
    recipe = Recipe.query.get(recipe_id)
    if recipe is None:
        flash('Recipe not found', 'error')
        return redirect(url_for('index'))
    return render_template('view_recipe.html', recipe=recipe)


@app.route('/my_recipes', methods=['GET', 'POST'])
@login_required
def my_recipes():
    from models import Recipe
    recipes = Recipe.query.filter_by(user_id=current_user.id)
    return render_template('my_recipes.html', recipes=recipes)


@app.route('/delete_recipe/<int:recipe_id>', methods=['GET', 'POST'])
@login_required
def delete_recipe(recipe_id):
    from models import Recipe
    recipe = Recipe.query.get(recipe_id)

    if recipe is None:
        flash('Recipe not found', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        db.session.delete(recipe)
        db.session.commit()
        flash('Recipe deleted successfully', 'success')
        return redirect(url_for('my_recipes'))

    return render_template('delete_recipe.html', recipe=recipe)


if __name__ == '__main__':
    app.run(debug=True)

login_manager.init_app(app)
