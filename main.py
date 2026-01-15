from flask import Flask, render_template, request, flash, redirect, abort 
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
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


@app.route("/product/<product_id>")
def product_page(product_id):
    connection = connect_db()

    cursor = connection.cursor()

    cursor.execute("SELECT * FROM `Product` WHERE `ID` = %s", (product_id,) )

    result = cursor.fetchone()
    
    connection.close()
    
    if result is None:
        abort(404)
    else:
        return render_template("product.html.jinja", product = result)

@app.route("/product/<product_id>/add_to_cart", methods=["POST"])
@login_required
def add_to_cart(product_id):
    connection = connect_db()
    cursor = connection.cursor()

    quantity = request.form.get("quantity", 1) 
    user_id = current_user.id  

    cursor.execute(
        """
        INSERT INTO Cart (Quantity, ProductID, UserID)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE
        Quantity = Quantity + %s 
        """,
        (quantity, product_id, user_id, quantity)
    )

    connection.commit() 
    connection.close()

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


@app.route("/cart")
@login_required
def cart():
    connection = connect_db()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT * FROM Cart
        Join Product ON Product.ID = Cart.ProductID
        WHERE UserID = %s             
                   
    """,(current_user.id))

    result = cursor.fetchall()

    connection.close()

    return render_template("cart.html.jinja", cart=result)


@app.route("/cart/<product_id>/update_qty", methods=["POST"])
@login_required
def update_qty(product_id):
    new_qty = request.form["qty"]
    
    connection = connect_db()

    cursor = connection.cursor()

    cursor.execute("""
            UPDATE `Cart`
            SET `Quantity` = %s
            WHERE `ProductID` = %s AND `UserID` = %s
        """, (new_qty, product_id, current_user.id) )

    connection.close()

    return redirect("/cart")
    
    
@app.route("/checkout")
@login_required
def checkout():
    connection = connect_db()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT * FROM Cart
        Join Product ON Product.ID = Cart.ProductID
        WHERE UserID = %s             
                   
    """,(current_user.id))

    result = cursor.fetchall()

    connection.close()

    return render_template("checkout.html.jinja", cart=result)



@app.route("/checkout/payment", methods=["POST"])
@login_required
def payment():
    connection = connect_db()

    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM `Cart`
        WHERE `UserID` = %s
    """)

    connection.close()

    flash("Payment processed successfully! Thank you for your purchase.")

    return redirect("/browse")


@app.route("/order")
def order():
    """
    Fetch and display the order history for the current user.

    This function retrieves all orders made by the current user, including the order ID, 
    timestamp, total quantity of items, and total price. If no orders are found, it flashes 
    a message and renders the order page with an empty list.

    Returns:
        A rendered template displaying the order history or an empty list if no orders exist.
    """
    connection = connect_db()

    cursor = connection.cursor()

    cursor.execute("""SELECT 
                   `Sale`.`ID`,
                   `Sale`.`Timestamp`,
                   SUM(`SaleProduct`.`Quantity`) AS 'Quantity',
                   SUM(`SaleProduct`.`Quantity` * `Product`.`Price`) AS 'Total'
    FROM `Sale`
    JOIN `SaleProduct` ON `SaleProduct`.`SaleID` = `Sale`.`ID`
    JOIN `Product` ON `Product`.`ID` = `SaleProduct`.`ProductID`
    WHERE `Sale`.`UserID` = %s
    GROUP BY `Sale`.`ID`, `Sale`.`Timestamp`
""", (current_user.id,) )
    
    result = cursor.fetchall()

    connection.close()

    if not result:
        flash("No orders found.")
        return render_template("order.html.jinja", sales=[])
    
    return render_template("order.html.jinja", sales=result)




@app.route("/product/<product_id>/review", methods=["POST"])
@login_required
def review(product_id):
    # Get review from the form
    rating = request.form["rating"]
    comment = request.form["comment"]

    connection = connect_db()

    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO `Review` (`Rating`, `Comment`, `ProductID`, `UserID`)
        VALUES (%s, %s, %s, %s)
    """, (rating , comment, current_user.id , product_id) )

    connection.close()

    return redirect(f"/product/{product_id}")








