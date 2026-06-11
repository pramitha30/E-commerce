from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
from config import get_db_connection

app = Flask(__name__)
app.secret_key = "supersecretkey"


# ================= HOME =================
@app.route("/")
def home():
    if "user_id" not in session:
        return redirect("/login")

    search = request.args.get("search")

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    if search:
        cursor.execute("SELECT * FROM products WHERE name LIKE %s", ("%" + search + "%",))
    else:
        cursor.execute("SELECT * FROM products")

    products = cursor.fetchall()
    cursor.close()
    db.close()

    return render_template("index.html", products=products)


# ================= REGISTER =================
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute(
            "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
            (name, email, password)
        )

        db.commit()
        cursor.close()
        db.close()

        return redirect("/login")

    return render_template("register.html")


# ================= LOGIN =================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()

        cursor.close()
        db.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            return redirect("/")
        else:
            return "Invalid credentials"

    return render_template("login.html")


# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ================= ADD TO CART =================
@app.route("/add_to_cart/<int:product_id>")
def add_to_cart(product_id):

    if "user_id" not in session:
        return redirect("/login")

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    # Get product from DB
    cursor.execute("SELECT * FROM products WHERE id=%s", (product_id,))
    product = cursor.fetchone()

    if not product:
        cursor.close()
        db.close()
        return "Product not found"

    # Check stock
    if product["stock"] <= 0:
        cursor.close()
        db.close()
        return "Out of Stock"

    # Reduce stock by 1
    cursor.execute(
        "UPDATE products SET stock = stock - 1 WHERE id=%s",
        (product_id,)
    )
    db.commit()

    cursor.close()
    db.close()

    # Add to session cart
    if "cart" not in session:
        session["cart"] = {}

    cart = session["cart"]
    product_id = str(product_id)

    if product_id in cart:
        cart[product_id] += 1
    else:
        cart[product_id] = 1

    session["cart"] = cart

    return redirect("/")


# ================= VIEW CART =================
@app.route("/cart")
def view_cart():
    if "user_id" not in session:
        return redirect("/login")

    cart = session.get("cart", {})

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cart_items = []
    total = 0

    for product_id, quantity in cart.items():
        cursor.execute("SELECT * FROM products WHERE id=%s", (product_id,))
        product = cursor.fetchone()

        if product:
            product["quantity"] = quantity
            product["subtotal"] = product["price"] * quantity
            total += product["subtotal"]
            cart_items.append(product)

    cursor.close()
    db.close()

    return render_template("cart.html", cart_items=cart_items, total=total)


# ================= ADMIN =================
@app.route("/admin", methods=["GET", "POST"])
def admin():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    if request.method == "POST":
        name = request.form["name"]
        price = request.form["price"]
        stock = request.form["stock"]

        cursor.execute(
            "INSERT INTO products (name, price, stock, image) VALUES (%s, %s, %s, %s)",
            (name, price, stock, "laptop.jpg")
        )
        db.commit()

    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template("admin.html", products=products)


if __name__ == "__main__":
    app.run(debug=True)