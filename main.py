from flask import Flask, render_template, request, flash, redirect
import pymysql
from dynaconf import Dynaconf

app = Flask(__name__)

config = Dynaconf(settings_files=["settings.toml"])

app.secret_key = config.secret_key

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
    return render_template("browse.html.jinja")

@app.route("/product/<int:product_id>")
def product_page(product_id):
    connection = connect_db()

    cursor = connection.cursor()

    cursor.execute("SELECT * FROM `Product` WHERE `ID` = $s", (product_id,) )

    result = cursor.fetchone()
    
    connection.close()
    
    return render_template("product.html.jinja", product=result)


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

            cursor.execute("""INSERT INTO `User` (`Name`, `Email`, `Password`, `Address`)  \
            VALUES (%s, %s, %s, %s)
            """, (name, email, password, address))
        return "redirect('/login")"
    
        return render_template("register.html.jinja")

