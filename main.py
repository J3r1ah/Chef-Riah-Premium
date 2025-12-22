from flask import Flask, render_template, request, flash, redirect, abort 
from flask_login import LoginManager, login_user, logout_user, login_required 
import pymysql

from dynaconf import Dynaconf

app = Flask(__name__)

config = Dynaconf(settings_files=["settings.toml"])

app.secret_key = config.secret_key

login_manager = LoginManager(app)

login_manager.login_view = "login"

class User:
    is_authenticated = True
    is_active = True
    is_anonymous = False

    def __init__(self, result):
        self.name = result['Name']
        self.emial = result['Email']
        self.id = result['ID']

    def get_id(self):
        return str(self.id)
    
@login_manager.user_loader
def load_user(user_id):
    connection = connect_db()

    cursor = connection.cursor()

    cursor.execute(" SELECT * FROM User WHERE ID = %s", (user_id) )

    result = cursor.fetchone()

    connection.close()

    if result is None:
        return None
    
    return User(result)


def connect_db():
    conn = pymysql.connect(
        host = "db.steamcenter.tech",
        user = "joliverasfair",
        password = config.password,
        database = "joliverasfair_chef_riah_premuim",
        autocommit = True,
        cursorclass = pymysql.cursors.DictCursor
    )
    return conn

@app.route("/")
def home():
    return render_template("homepage.html.jinja")

@app.route("/browse")
def browse():
    connection = connect_db()

    cursor = connection.cursor()

    cursor.execute("SELECT * FROM `Product`")

    result = cursor.fetchall()
    
    connection.close()
    return render_template("browse.html.jinja", products = result)
    return render_template("browse.html.jinja")


@app.route("/product/<int:product_id>")
def product_page(product_id):
    connection = connect_db()

    cursor = connection.cursor()

    cursor.execute("SELECT * FROM `Product` WHERE `ID` = $s", (product_id,) )

    result = cursor.fetchone()
    
    connection.close()
    
    if result is None:
        abort(404)
    return render_template("product.html.jinja", product = result)

@app.route ("/product/<product_id>/add_to_cart", methods=["POST"])
@login_required
def add_to_cart(product_id):
    
    connection = connect_db()

    cursor = connection.cursor()

    cursor.execute("INSERT INTO `CART` (`U")
    
    
   


    return redirect("/cart")

@app.route("/register", methods=["POST", "GET"])
def register():  
        if request.method == "POST":
            name = request.form["name"]

            email = request.form["email"]

            password = request.form["password"]
            confirm_password = request.form["confirm_password"]

            address = request.form["address"]

            if password != confirm_password:
                flash("Passwords do not match!")
            elif len(password) < 8:
                flash("Password must be at least 8 characters long!")
                flash("password is too short")
                
            else:
                connection = connect_db()

                cursor = connection.cursor()
                
                try:
                    cursor.execute(
                        'INSERT INTO `User` (`Name`, `Email`, `Password`, `Address`) VALUES (%s, %s, %s, %s)',
                        (name, email, password, address))
                except pymysql.err.IntegrityError:
                    flash("Email already registered!")
                    connection.close()
                else:
                    connection.commit()  
                    connection.close()
                    return redirect('/login')
        
        return render_template("register.html.jinja")

@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        email = request.form["email"]

        password = request.form["password"]

        connection = connect_db()

        cursor = connection.cursor()

        cursor.execute("""
            SELECT * FROM `User` WHERE `Email` = %s
        """, (email))

        result = cursor.fetchone()

        connection.close()

        if result is None:
            flash("No user found with that email!")
        elif result["Password"] != password:
            flash("Incorrect password!")
        else:
            login_user(User(result))
            return redirect("/browse")
            
    return render_template("login.html.jinja")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")   


