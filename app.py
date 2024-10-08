from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
import os
import json

######## Initial configuration ########
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


##### Login manager configuration #####

login_manager = LoginManager(app)
# Redirects to login page if user is not logged in
login_manager.login_view = 'login'
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))


def force_colour_mode():
    if session.get("colour_mode") is None:  # New account case
        session['colour_mode'] = 'light'
######### Routes and views ############


@app.route('/index', methods=['GET', 'POST'])
@app.route('/', methods=['GET', 'POST'])
def index():
    force_colour_mode()
    from forms import SearchForm
    search_form = SearchForm()
    if search_form.validate_on_submit():
        query = search_form.ingredients.data.split()
        parameters = {
            "ingredients": query
        }
        return redirect(url_for('advanced_results', parameters=json.dumps(parameters)))
    from helpers import random_recipes
    recipes = random_recipes()
    return render_template('index.html', recipes=recipes, searchform=search_form, show_search=True)


@app.route('/random')
def random():
    force_colour_mode()
    from helpers import random_recipes
    recipes = random_recipes()
    return render_template('random.html', recipes=recipes)

######### User Authentication Routes #########


@app.route('/register', methods=['GET', 'POST'])
def register():
    force_colour_mode()
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


@app.route('/login', methods=['GET', 'POST'])
def login():
    force_colour_mode()
    from models import User
    from forms import LoginForm
    from helpers import load_settings
    form = LoginForm()
    if form.validate_on_submit():
        # Remember the user if the checkbox is checked
        remember = True if request.form.get('remember') else False
        user = User.query.filter_by(username=form.username.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, remember=remember)
            load_settings(current_user.settings_json)
            flash(f'You have successfully logged in, {current_user.username}!')
            profile = json.loads(user.food_profile)
            has_taste = False if profile == {} or len(profile) == 0 else True
            if has_taste:  # Load the user's food profile into the session
                return redirect(url_for('index'))
            else:  # If the user has no food profile, redirect them to the profile creation page
                flash('Please create a food profile to get started.')
                return redirect(url_for('create_profile'))
        flash('Invalid username or password.')
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout successful.', 'success')
    return redirect(url_for('index'))

################## Search Routes #################


@app.route('/search/<string:query>', methods=['GET', 'POST'])
@login_required
def search(query):
    from forms import SearchForm
    search_form = SearchForm()
    if search_form.validate_on_submit():
        query = ",".join(search_form.ingredients.data.split())
        return redirect(url_for('search', query=query))
    from helpers import search_by_ingredients
    results = search_by_ingredients(query)
    return render_template('search.html', results=results, searchform=search_form, show_search=True)


@app.route('/advancedsearch', methods=['GET', 'POST'])
@login_required
def advancedsearch():
    inventory = json.loads(current_user.inventory)
    from forms import AdvancedSearchForm
    form = AdvancedSearchForm()
    # Load the user's inventory into the form
    form.ingredients.choices = [ingredient for ingredient in inventory.keys()]
    if form.validate_on_submit():
        # Parse the form data into a parameter JSON object
        parameters = {
            "cuisines": form.cuisines.data,
            "diet": form.diet.data,
            "allergies": form.allergies.data,
            "ingredients": form.ingredients.data
        }
        return redirect(url_for('advanced_results', parameters=json.dumps(parameters)))
    return render_template('advanced_search.html', inventory=inventory, form=form)


@app.route('/advanced_results/<string:parameters>', methods=['GET', 'POST'])
@login_required
def advanced_results(parameters):
    params = json.loads(parameters)
    from helpers import execute_advanced_search, local_search
    external_results = execute_advanced_search(params)
    ugc_results = local_search(**params)
    return render_template('search.html', external_results=external_results, ugc_results=ugc_results)

####### Profile and User-specific Routes #######


@app.route('/create_profile', methods=['GET', 'POST'])
@login_required
def create_profile():
    from helpers import CUISINES, ALLERGIES, DIETS, TASTES, DEFAULT_PROFILE
    prof = json.loads(current_user.food_profile)
    if prof != {} or len(prof) > 0:
        initial_data = prof
    else:
        initial_data = DEFAULT_PROFILE

    if request.method == 'POST':
        # Load the user's new food profile into the session
        session['food_profile'] = {
            "cuisines": request.form.getlist('cuisine'),
            "taste": {
                "salty": request.form.get("salty"), "spicy": request.form.get("spicy"), "sour": request.form.get("sour"), "sweet": request.form.get("sweet"), "bitter": request.form.get("bitter"), "fatty": request.form.get("fatty"), "savory": request.form.get("savory")
            },
            "diet": request.form.get('diet'),
            "allergies": request.form.getlist('allergy')
        }
        # Save the user's food profile to the database
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
    if user_settings.get('has_dp') is True:  # Load the user's display picture
        dp = url_for('static', filename='uploads/' +
                     str(user.id) + '/dp.jpg')
    else:
        dp = url_for('static', filename='default.jpg')
    if user_id != current_user.id:  # Filter out private recipes if the user is not the owner
        from models import Recipe
        recipes = Recipe.query.filter_by(user_id=user_id, visibility='Public')
    else:
        recipes = current_user.recipes
    comments = user.comments  # Every comment the user has made
    profile = json.loads(user.food_profile)  # The user's food profile
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
        if os.path.isfile(dp_dir):  # Replace the user's current display picture
            os.remove(dp_dir)
        filename = images.save(settings.dp.data, name="dp.jpg")
        if filename is not None:  # Successfully uploaded
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


@app.route('/delete_item/<string:item>', methods=['GET', 'POST'])
@login_required
def delete_item(item):
    inventory = json.loads(current_user.inventory)
    if item not in inventory:
        flash('Item not found in pantry', 'error')
        return redirect(url_for('pantry'))
    del inventory[item]
    current_user.inventory = json.dumps(inventory)
    db.session.commit()
    flash('Item removed from pantry', 'success')
    return redirect(url_for('pantry'))


################ Recipe Management Routes ################

@app.route('/add_recipe', methods=['GET', 'POST'])
@login_required
def add_recipe():
    from models import Recipe
    from forms import RecipeForm
    from helpers import load_settings
    load_settings(current_user.settings_json)
    form = RecipeForm()
    if form.add_ingredient.data:
        form.ingredients.append_entry("")  # Add a new ingredient field
    if form.validate_on_submit():
        recipe_ingredients = {}
        for ingredient in form.ingredients.data:
            recipe_ingredients[ingredient['name']] = {
                "quantity": ingredient['quantity'], "unit": ingredient['unit']}
        taste = form.taste.data
        taste.pop('csrf_token')  # Not required for storage
        recipe = Recipe(title=form.title.data, ingredients=json.dumps(recipe_ingredients),
                        instructions=form.instructions.data, user_id=current_user.id, allergies=",".join(form.allergies.data), cuisines=",".join(form.cuisines.data), taste=json.dumps(taste), visibility=form.visibility.data, diet=form.diet.data)
        db.session.add(recipe)
        db.session.commit()
        # Ensure that an image file was selected
        if (form.image.data != '') and (form.image.data is not None):
            new_recipe = Recipe.query.filter_by(
                title=form.title.data, user_id=current_user.id).order_by(Recipe.id.desc()).first()  # Get the recipe that was just created
        from helpers import images
        import uuid
        # Generate random unique string to prevent overwriting
        uuid_string = str(uuid.uuid4())
        # Save the image to the user's directory
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


@ app.route('/view_recipe/<int:recipe_id>', methods=['GET', 'POST'])
def view_recipe(recipe_id):
    force_colour_mode()
    from models import Recipe
    from forms import CommentForm
    from helpers import DEFAULT_DP, DIET_TITLES, DIET_VALUES
    recipe = Recipe.query.get_or_404(recipe_id)
    votes = recipe.votes
    if current_user.is_authenticated:
        pantry = list(json.loads(current_user.inventory).keys())
        pantry = list(map(lambda x: x.lower(), pantry))
        user_vote = [vote for vote in votes if vote.user_id == current_user.id]
        user_bmark = [
            bmark for bmark in recipe.bookmarks if bmark.user_id == current_user.id]
    else:
        pantry = []
        user_vote = []
        user_bmark = []
    print("Pantry", pantry)
    comments = recipe.comments
    user_vote = user_vote[0] if len(user_vote) > 0 else None
    user_bmark = user_bmark[0] if len(user_bmark) > 0 else None
    author_settings = json.loads(recipe.user.settings_json)
    author_dp = url_for('static', filename='uploads/' +
                        str(recipe.user.id) + '/dp.jpg') if author_settings.get("has_dp") else DEFAULT_DP
    dps = []
    for comment in comments:
        user_settings = json.loads(comment.user.settings_json)
        dp = url_for('static', filename='uploads/' +
                     str(comment.user.id) + '/dp.jpg') if user_settings.get("has_dp") else DEFAULT_DP

        dps.append(dp)
    comments_and_dps = zip(comments, dps)
    diet = DIET_TITLES[DIET_VALUES.index(recipe.diet)]
    form = CommentForm()
    if form.validate_on_submit():
        from models import Comment
        comment = Comment(content=form.content.data,
                          user_id=current_user.id, recipe_id=recipe_id)
        db.session.add(comment)
        db.session.commit()
        flash('Comment added successfully', 'success')
        return redirect(url_for('view_recipe', recipe_id=recipe_id))
    return render_template('view_recipe.html', recipe=recipe, author_dp=author_dp, ingredients=json.loads(recipe.ingredients), tastes=json.loads(recipe.taste), allergies=recipe.allergies.split(','), cuisines=recipe.cuisines.split(','), ratings=json.loads(recipe.rating), diet=diet, comments=comments_and_dps, form=form, user_vote=user_vote, user_bmark=user_bmark, pantry=pantry)


@ app.route('/view_external_recipe/<int:recipe_id>', methods=['GET', 'POST'])
def view_external_recipe(recipe_id):
    force_colour_mode()
    from helpers import search_by_recipe_id
    recipe = search_by_recipe_id(recipe_id)
    if recipe is None:
        flash('Recipe not found', 'error')
        return redirect(url_for('index'))
    if current_user.is_authenticated:
        pantry = list(json.loads(current_user.inventory).keys())
        pantry = list(map(lambda x: x.lower(), pantry))
    else:
        pantry = []
    return render_template('view_external_recipe.html', recipe=recipe, pantry=pantry)


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


@ app.route('/bookmark/<int:recipe_id>', methods=['GET', 'POST'])
@ login_required
def bookmark(recipe_id):
    from models import Bookmark
    bookmark = Bookmark.query.filter_by(
        user_id=current_user.id, recipe_id=recipe_id)
    if bookmark.count() > 0:  # If the user has already bookmarked the recipe, remove the bookmark
        bookmark.delete()
        db.session.commit()
        flash('Bookmark removed successfully', 'success')
        return redirect(url_for('view_recipe', recipe_id=recipe_id))
    bookmark = Bookmark(user_id=current_user.id, recipe_id=recipe_id)
    db.session.add(bookmark)
    db.session.commit()
    flash('Bookmark added successfully', 'success')
    return redirect(url_for('view_recipe', recipe_id=recipe_id))


@app.route('/bookmarks', methods=['GET', 'POST'])
@ login_required
def bookmarks():
    from models import Recipe, Bookmark
    bookmarks = Bookmark.query.filter_by(user_id=current_user.id)
    recipes = [Recipe.query.get(bmark.recipe_id) for bmark in bookmarks]
    return render_template('bookmarks.html', recipes=recipes)

######### Social Engagement Routes #########


@app.route('/upvote/<int:recipe_id>', methods=['GET', 'POST'])
@ login_required
def upvote(recipe_id):
    from models import Recipe, Vote
    vote = Vote.query.filter_by(user_id=current_user.id, recipe_id=recipe_id)
    if vote.count() > 0:  # If the user has already voted on the recipe
        if vote.first().upvote:  # If the user has already upvoted the recipe, remove the upvote
            Recipe.query.get(recipe_id).rating = json.dumps(
                {"upvotes": json.loads(Recipe.query.get(recipe_id).rating)['upvotes'] - 1, "downvotes": json.loads(Recipe.query.get(recipe_id).rating)['downvotes']})
            vote.delete()
            db.session.commit()
            flash('Vote updated successfully', 'success')
            return redirect(url_for('view_recipe', recipe_id=recipe_id))
        else:  # If the user has downvoted the recipe, change the vote to an upvote
            vote.first().upvote = True
            Recipe.query.get(recipe_id).rating = json.dumps(
                {"upvotes": json.loads(Recipe.query.get(recipe_id).rating)['upvotes'] + 1, "downvotes": json.loads(Recipe.query.get(recipe_id).rating)['downvotes'] - 1})
            db.session.commit()
            flash('Vote updated successfully', 'success')
            return redirect(url_for('view_recipe', recipe_id=recipe_id))
    recipe = Recipe.query.get_or_404(recipe_id)
    ratings = json.loads(recipe.rating)
    ratings['upvotes'] += 1
    recipe.rating = json.dumps(ratings)
    vote = Vote(user_id=current_user.id, recipe_id=recipe_id, upvote=True)
    db.session.add(vote)
    db.session.commit()
    flash('Vote updated successfully', 'success')
    return redirect(url_for('view_recipe', recipe_id=recipe_id))


@app.route('/downvote/<int:recipe_id>', methods=['GET', 'POST'])
@ login_required
def downvote(recipe_id):
    from models import Recipe, Vote
    vote = Vote.query.filter_by(user_id=current_user.id, recipe_id=recipe_id)
    if vote.count() > 0:  # If the user has already voted on the recipe
        if not vote.first().upvote:  # If the user has already downvoted the recipe, remove the downvote
            Recipe.query.get(recipe_id).rating = json.dumps(
                {"upvotes": json.loads(Recipe.query.get(recipe_id).rating)['upvotes'], "downvotes": json.loads(Recipe.query.get(recipe_id).rating)['downvotes'] - 1})
            vote.delete()
            db.session.commit()
            flash('Vote updated successfully', 'success')
            return redirect(url_for('view_recipe', recipe_id=recipe_id))
        else:  # If the user has upvoted the recipe, change the vote to a downvote
            vote.first().upvote = False
            Recipe.query.get(recipe_id).rating = json.dumps(
                {"upvotes": json.loads(Recipe.query.get(recipe_id).rating)['upvotes'] - 1, "downvotes": json.loads(Recipe.query.get(recipe_id).rating)['downvotes'] + 1})
            db.session.commit()
            flash('Vote updated successfully', 'success')
            return redirect(url_for('view_recipe', recipe_id=recipe_id))
    recipe = Recipe.query.get_or_404(recipe_id)
    ratings = json.loads(recipe.rating)
    ratings['downvotes'] += 1
    recipe.rating = json.dumps(ratings)
    vote = Vote(user_id=current_user.id, recipe_id=recipe_id, upvote=False)
    db.session.add(vote)
    db.session.commit()
    flash('Vote updated successfully', 'success')
    return redirect(url_for('view_recipe', recipe_id=recipe_id))


@app.route("/delete_comment/<int:comment_id>")
@login_required
def delete_comment(comment_id):
    from models import Comment
    comment = Comment.query.get_or_404(comment_id)
    recipe_id = comment.recipe.id
    if comment.user_id != current_user.id:
        flash("You cannot delete this comment!")
        return redirect(url_for('view_recipe', recipe_id=recipe_id))
    db.session.delete(comment)
    db.session.commit()
    flash("Comment deleted!")
    return redirect(url_for('view_recipe', recipe_id=recipe_id))


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
