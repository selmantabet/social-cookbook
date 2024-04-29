from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
import os
import json

cwd = os.getcwd()
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cookbook.db/'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = '3813c327b35448b0b33eba77abc89402'
app.config['DEFAULT_UPLOAD_DEST'] = os.path.join(
    cwd, "static", "uploads")  # Constant
# When the user logs on, the app will change the upload directory to the user's directory
app.config['UPLOADED_IMAGES_DEST'] = app.config['DEFAULT_UPLOAD_DEST']
app.config['ALLOWED_EXTENSIONS'] = set(['png', 'jpg', 'jpeg', 'gif'])

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.init_app(app)


@app.route('/index', methods=['GET', 'POST'])
@app.route('/', methods=['GET', 'POST'])
def index():
    from forms import SearchForm
    search_form = SearchForm()
    if search_form.validate_on_submit():
        print("Search form submitted")
        query = ",".join(search_form.ingredients.data.split())
        return redirect(url_for('search', query=query))
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


@app.route('/advancedsearch', methods=['GET', 'POST'])
@login_required
def advancedsearch():
    inventory = json.loads(current_user.inventory)
    from helpers import CUISINES, ALLERGIES, DIETS, TASTES, DEFAULT_PROFILE, execute_advanced_search
    prof = json.loads(current_user.food_profile)
    if prof != {} or len(prof) > 0:
        initial_data = prof
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
        cuisines = request.form.getlist('cuisine')
        ingredients = request.form.getlist('ingredient')
        parameters = {
            "cuisines": cuisines,
            "taste": {
                "salty": salty, "spicy": spicy, "sour": sour, "sweet": sweet, "bitter": bitter, "fatty": fatty, "savory": savory
            },
            "diet": diet,
            "allergies": allergies,
            "ingredients": ingredients
        }
        results = execute_advanced_search(parameters)
        return redirect(url_for('advanced_results', results=json.dumps(results)), code=307)
    return render_template('advanced_search.html', inventory=inventory, cuisines=CUISINES, tastes=TASTES, diets=DIETS, allergies=ALLERGIES, initial_data=initial_data)


@app.route('/advanced_results', methods=['POST'])
@login_required
def advanced_results():
    return render_template('search.html', results=json.loads(request.args.get("results")).get('results'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    from models import User
    from forms import LoginForm
    from helpers import load_settings
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user)
            load_settings(current_user.settings_json)
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
    from helpers import CUISINES, ALLERGIES, DIETS, TASTES, DEFAULT_PROFILE
    prof = json.loads(current_user.food_profile)
    if prof != {} or len(prof) > 0:
        initial_data = prof
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
        cuisines = request.form.getlist('cuisine')
        session['food_profile'] = {
            "cuisines": cuisines,
            "taste": {
                "salty": salty, "spicy": spicy, "sour": sour, "sweet": sweet, "bitter": bitter, "fatty": fatty, "savory": savory
            },
            "diet": diet,
            "allergies": allergies
        }
        current_user.food_profile = json.dumps(session['food_profile'])
        db.session.commit()
        flash('Profile updated successfully', 'success')
        return redirect(url_for('index'))

    return render_template('create_profile.html', cuisines=CUISINES, tastes=TASTES, diets=DIETS, allergies=ALLERGIES, initial_data=initial_data)


@app.route('/profile/<int:user_id>', methods=['GET', 'POST'])
@login_required
def profile(user_id):
    from helpers import load_settings
    load_settings(current_user.settings_json)
    from models import User
    user = User.query.get_or_404(user_id)
    user_settings = json.loads(user.settings_json)
    if user_settings.get('has_dp') is True:
        dp = url_for('static', filename='uploads/' +
                     str(user.id) + '/dp.jpg')
    else:
        dp = url_for('static', filename='default.jpg')
    if user_id != current_user.id:
        from models import Recipe
        recipes = Recipe.query.filter_by(user_id=user_id, visibility='Public')
    else:
        recipes = current_user.recipes
    comments = user.comments
    profile = json.loads(user.food_profile)
    has_taste = False if profile == {} or len(profile) == 0 else True
    return render_template('profile.html', user=user, recipes=recipes, dp=dp, has_taste=has_taste, tastes=profile.get('taste'), comments=comments)


@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    from helpers import load_settings, images
    from forms import SettingsForm
    settings = SettingsForm()
    load_settings(current_user.settings_json)
    if "clear" in request.form:
        from helpers import clear_dp
        clear_dp(current_user)
        flash('Display picture cleared!')
        return redirect(url_for('account'))
    if settings.validate_on_submit():
        dp_dir = os.path.join(
            app.config["UPLOADED_IMAGES_DEST"], "dp.jpg")
        if os.path.isfile(dp_dir):
            os.remove(dp_dir)
        filename = images.save(settings.dp.data, name="dp.jpg")
        if filename is not None:
            settings = json.loads(current_user.settings_json)
            settings['has_dp'] = True
            session.update(settings)
            current_user.settings_json = json.dumps(settings)
            db.session.commit()
        else:
            flash("Upload failed.")
        flash('Display picture updated!')
        return redirect(url_for('account'))

    return render_template('account.html', settings=settings)


@app.route('/pantry', methods=['GET', 'POST'])
@login_required
def pantry():
    from forms import PantryForm
    form = PantryForm()
    inventory = json.loads(current_user.inventory)
    if form.validate_on_submit():
        print("Pantry form submitted")
        item = form.name.data
        quantity = form.quantity.data
        unit = request.form.get('unit')
        if item in inventory:
            flash('Item already in pantry', 'error')
            return redirect(url_for('pantry'))
        else:
            inventory[item] = {"quantity": quantity, "unit": unit}
            current_user.inventory = json.dumps(inventory)
            db.session.commit()
            flash('Item added to pantry', 'success')
            return redirect(url_for('pantry'))

    return render_template('pantry.html', items=inventory, form=form)


@app.route('/add_recipe', methods=['GET', 'POST'])
@login_required
def add_recipe():
    from models import Recipe
    from forms import RecipeForm
    from helpers import load_settings
    load_settings(current_user.settings_json)
    form = RecipeForm()
    if form.add_ingredient.data:
        form.ingredients.append_entry("")
    if form.validate_on_submit():
        recipe_ingredients = {}
        for ingredient in form.ingredients.data:
            recipe_ingredients[ingredient['name']] = {
                "quantity": ingredient['quantity'], "unit": ingredient['unit']}
        taste = form.taste.data
        taste.pop('csrf_token')
        recipe = Recipe(title=form.title.data, ingredients=json.dumps(recipe_ingredients),
                        instructions=form.instructions.data, user_id=current_user.id, allergies=",".join(form.allergies.data), cuisines=",".join(form.cuisines.data), taste=json.dumps(taste), visibility=form.visibility.data)
        db.session.add(recipe)
        db.session.commit()
        if (form.image.data != '') and (form.image.data is not None):
            new_recipe = Recipe.query.filter_by(
                title=form.title.data, user_id=current_user.id).order_by(Recipe.id.desc()).first()  # Get the recipe that was just created
        from helpers import images
        import uuid
        uuid_string = str(uuid.uuid4())
        filename = images.save(form.image.data, name=uuid_string)
        if filename is not None:
            new_recipe.image_file = filename
            db.session.commit()
        else:
            flash("Image upload failed.")
            return redirect(url_for('index'))
        flash('Recipe added successfully', 'success')
        return redirect(url_for('index'))
    return render_template('add_recipe.html', form=form)


@ app.route('/result/<int:result_id>')
def result(result_id):
    from helpers import search_by_recipe_id
    recipe = search_by_recipe_id(result_id)
    if recipe is None:
        flash('Recipe not found', 'error')
        return redirect(url_for('index'))
    return render_template('result.html', recipe=recipe)


@ app.route('/view_recipe/<int:recipe_id>', methods=['GET', 'POST'])
def view_recipe(recipe_id):
    from models import Recipe
    recipe = Recipe.query.get(recipe_id)
    if recipe is None:
        flash('Recipe not found', 'error')
        return redirect(url_for('index'))
    return render_template('view_recipe.html', recipe=recipe)


@ app.route('/view_external_recipe/<int:recipe_id>', methods=['GET', 'POST'])
def view_external_recipe(recipe_id):
    return render_template('view_external_recipe.html', recipe_id=recipe_id)


@ app.route('/my_recipes', methods=['GET', 'POST'])
@ login_required
def my_recipes():
    from models import Recipe
    recipes = Recipe.query.filter_by(user_id=current_user.id)
    return render_template('my_recipes.html', recipes=recipes)


@ app.route('/delete_recipe/<int:recipe_id>', methods=['GET', 'POST'])
@ login_required
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


@ app.route("/change_colour")
def change_colour():
    colour = session.get('colour_mode')
    if colour is None:
        session['colour_mode'] = 'dark'
    else:
        session['colour_mode'] = 'dark' if colour == 'light' else 'light'
    if current_user.is_authenticated:
        settings = json.loads(current_user.settings_json)
        settings['colour_mode'] = session['colour_mode']
        current_user.settings_json = json.dumps(settings)
        db.session.commit()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
