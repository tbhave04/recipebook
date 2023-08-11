from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, render_template_string
from flask_sqlalchemy import SQLAlchemy
from PIL import Image
import pytesseract
import re
import spacy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///recipes.db'
db = SQLAlchemy(app)


class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    ingredients = db.Column(db.Text, nullable=False)
    instructions = db.Column(db.Text, nullable=False)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)


def extract_ingredients_and_instructions(image):
    nlp = spacy.load("./Project/en_core_web_sm-3.0.0/en_core_web-sm")
    text = pytesseract.image_to_string(image)
    text_doc = nlp(text)
    sentences = list(text_doc)
    print(len(sentences))

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'GET':
        search_query = request.args.get('search')
        if search_query:
            with app.app_context():
                recipes = Recipe.query.filter(Recipe.title.ilike(f"%{search_query}%")).all()
        else:
            with app.app_context():
                recipes = Recipe.query.all()
        return render_template('index.html', recipes=recipes)

    image = request.files['file']
    img = Image.open(image)
    text = pytesseract.image_to_string(img)
    #ingredients = extract_ingredients_and_instructions(img)

    return render_template('customize.html', msg=text)

@app.route('/submit', methods=['POST'])
def submit():
    title = request.form['title']
    ingredients = request.form['ingredients']
    instructions = request.form['instructions']

    with app.app_context():
        recipe = Recipe(title=title, ingredients=ingredients, instructions=instructions)
        db.session.add(recipe)
        db.session.commit()

    return redirect(url_for('home'))


@app.route('/recipe/<int:recipe_index>')
def recipe_details(recipe_index):
    with app.app_context():
        recipe = Recipe.query.get(recipe_index)
    return render_template('recipe_details.html', recipe=recipe)


@app.route('/delete_recipe/<int:recipe_index>', methods=['POST'])
def delete_recipe(recipe_index):
    with app.app_context():
        recipe = Recipe.query.get(recipe_index)
        if recipe:
            db.session.delete(recipe)
            db.session.commit()
    return redirect(url_for('home'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Check if the username or email already exists in the database
        with app.app_context():
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                flash('Username already exists. Please choose a different username.', 'error')
                return redirect(url_for('signup'))

            existing_email = User.query.filter_by(email=email).first()
            if existing_email:
                flash('Email address already exists. Please use a different email.', 'error')
                return redirect(url_for('signup'))

            # Create a new user
            user = User(username=username, email=email, password=password)
            db.session.add(user)
            db.session.commit()

        flash('Signup successful. Please login with your new account.', 'success')
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if the username and password match a user in the database
        with app.app_context():
            user = User.query.filter_by(username=username).first()
            if user and user.password == password:
                # Successful login, redirect to the home page or any other desired page
                return redirect(url_for('home'))
            else:
                flash('Invalid username or password.', 'error')
                return redirect(url_for('login'))

    return render_template('login.html')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run()