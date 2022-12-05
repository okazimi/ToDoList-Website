import os
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from sqlalchemy.orm import relationship
from forms import RegisterForm, LoginForm, ToDoListForm
from werkzeug.security import generate_password_hash, check_password_hash

# INITIALIZE APP
app = Flask(__name__)

# CONFIGURE APP SECRET KEY
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")

# INITIALIZE BOOTSTRAP
Bootstrap(app)

# CONNECT TO DATABASE
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todolist.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# INITIALIZE LOGIN MANAGER
login_manager = LoginManager()
login_manager.init_app(app)


# USER TABLE CONFIGURATION
class User(UserMixin, db.Model):
    # TABLE NAME
    __tablename__ = "users"
    # TABLE COLUMNS
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(300), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    # ONE TO MANY RELATIONSHIP WITH TODOLIST
    todolists = relationship("ToDoList", back_populates="todolist_author")


# TODOLIST TABLE CONFIGURATION
class ToDoList(db.Model):
    # TABLE NAME
    __tablename__ = "todolist"
    # TABLE COLUMNS
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(300), nullable=False)
    date = db.Column(db.String(300), nullable=False)
    # MANY TODOLISTS TO ONE USER RELATIONSHIP
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    todolist_author = relationship("User", back_populates="todolists")

# # CREATE DATABASE/TABLE
# # ONLY NEEDED ONCE
# with app.app_context():
#     db.create_all()


# CREATE USER LOADER CALLBACK
@login_manager.user_loader
def load_user(user_id):
    # RETURN USER BASED ON USER ID
    return User.query.get(int(user_id))


# 401 ERROR HANDLING
@app.errorhandler(401)
def custom_401(error):
    # FLASH MESSAGE INFORMING USER TO LOGIN
    flash("Please Login")
    # RETURN HOME PAGE
    return redirect(url_for('login'))


# HOME PAGE
@app.route("/home", methods=["GET", "POST"])
@login_required
def home():
    # INITIALIZE FORM
    todolistitem = ToDoListForm()
    # QUERY DATABASE FOR TODOLIST ITEMS ASSOCIATED WITH CURRENT USER
    toDoListItems = ToDoList.query.filter_by(author_id=current_user.id)
    # CHECK IF USER POSTED
    if request.method == "POST":
        # CREATE TODOLIST ITEM
        toDoListItem = ToDoList(
            content=todolistitem.content.data,
            date=todolistitem.date.data,
            author_id=current_user.id
        )
        # ADD ITEM TO TODOLIST DATABASE
        db.session.add(toDoListItem)
        db.session.commit()
        # REDIRECT BACK TO HOME PAGE
        return redirect(url_for('home'))
    # RETURN HOME PAGE
    return render_template("index.html", current_user=current_user, toDoListItems=toDoListItems)


# REGISTER PAGE
@app.route("/register", methods=["GET", "POST"])
def register():
    # INITIALIZE FORM
    register_form = RegisterForm()
    # CHECK IF USER SUBMITTED REGISTER FORM
    if request.method == "POST":
        # CHECK IF USER ALREADY EXISTS IN DATABASE
        user = User.query.filter_by(email=register_form.email.data).first()
        # IF USER ALREADY EXISTS
        if user:
            # GENERATE FLASH MESSAGE
            flash("The provided email already exists, please login instead")
            # REDIRECT USER TO LOGIN PAGE
            return redirect(url_for('login'))
        # IF USER DOES NOT EXIST
        else:
            # CREATE NEW USER
            new_user = User(
                first_name=register_form.first_name.data,
                last_name=register_form.last_name.data,
                email=register_form.email.data,
                password=generate_password_hash(register_form.password.data, method='pbkdf2:sha256', salt_length=8),
            )
            # SAVE USER
            db.session.add(new_user)
            db.session.commit()
            # LOGIN USER
            login_user(new_user)
            # REDIRECT TO HOME PAGE
            return redirect(url_for('home'))
    # RETURN REGISTER PAGE
    return render_template("register.html")


# LOGIN PAGE
@app.route('/login', methods=["GET", "POST"])
def login():
    # INITIALIZE LOGIN FORM
    login_form = LoginForm()
    # CHECK IF LOGIN FORM WAS SUBMITTED
    if request.method == "POST":
        # OBTAIN USER'S EMAIL AND PASSWORD
        email = login_form.email.data
        password = login_form.password.data
        # QUERY DATABASE FOR USER
        user = User.query.filter_by(email=email).first()
        # IF USER EXISTS (CORRECT EMAIL)
        if user:
            # PASSWORD CORRECT?
            if check_password_hash(user.password, password):
                # LOGIN USER
                login_user(user)
                # REDIRECT USER TO HOME PAGE
                return redirect(url_for('home'))
            # PASSWORD INCORRECT :(
            else:
                # FLASH MESSAGE TO INFORM USER TO INCORRECT PASSWORD
                flash("Password enter is incorrect. Please try again.")
        # USER DOESNT EXIST
        else:
            # FLASH MESSAGE TO INFORM USER OF INCORRECT EMAIL
            flash("Please register to use our services")
            # REDIRECT USER TO REGISTER PAGE
            return redirect(url_for('register'))
    # RETURN LOGIN PAGE
    return render_template('login.html', current_user=current_user)


# LOGOUT BUTTON
@app.route('/logout')
def logout():
    # LOGOUT USER
    logout_user()
    # REDIRECT USER TO HOME PAGE
    return redirect(url_for("home"))


# DELETE TODOLIST ITEM
@app.route('/deleteToDoListItem/<int:item_id>')
@login_required
def deleteToDoListItem(item_id):
    # QUERY DATABASE FOR TODOLIST ITEM
    item_to_delete = ToDoList.query.get(item_id)
    # DELETE ITEM FROM DATABASE
    db.session.delete(item_to_delete)
    db.session.commit()
    # REFRESH HOME PAGE
    return redirect(url_for('home'))


# RUN APPLICATION IN DEBUG MODE
if __name__ == '__main__':
    app.run(debug=True)
