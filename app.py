from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cookbook.db/'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'
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
