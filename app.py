from flask import Flask, render_template, session, redirect, url_for, g, request, flash
from database import get_db, close_db
from flask_session import Session
from forms import SignupForm, LoginForm, PhotoSearchForm, UploadPhotoForm, LimitedPhotoForm, BidForm, DeletePhotoForm, UpdatePhotoForm, PurchaseForm, CheckoutForm
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os

app = Flask(__name__)
app.teardown_appcontext(close_db)
app.config["SECRET_KEY"] = "this-is-my-secret-key"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["UPLOAD_FOLDER"] = "static/uploads"
app.config["ALLOWED_EXTENSIONS"] = {"jpg", "jpeg", "png"}
Session(app)


@app.before_request
def load_logged_in_user():
    g.user = session.get("user_id", None)

def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.user is None:
            return redirect(url_for("login", next=request.url))
        return view(*args, **kwargs)
    return wrapped_view

def get_random_photo():
    import random
    db = get_db()
    photos = db.execute("""SELECT * FROM photos""").fetchall()
    if not photos:
        print("No photos found in the database")
    return random.choice(photos) if photos else None

@app.route("/", methods=["GET", "POST"])
def home():
    db = get_db()
    themes = db.execute("""SELECT DISTINCT name FROM themes""").fetchall()
    theme_choices = [("All", "All Themes")]

    for theme in themes:
        theme_choices.append((theme["name"], theme["name"]))

    form = PhotoSearchForm()
    form.theme.choices = theme_choices  

    featured_photo = db.execute("""SELECT * FROM limited_photos 
                                WHERE end_date > CURRENT_TIMESTAMP
                                ORDER BY end_date ASC
                                LIMIT 1""").fetchone()
    
    if form.validate_on_submit():
        session["theme"] = form.theme.data
        session["price_min"] = form.price_min.data
        session["price_max"] = form.price_max.data
        session["filter_type"] = form.filter_type.data

        return redirect(url_for("gallery"))

    random_photo = get_random_photo()
    return render_template("home_page.html", form=form, random_photo=random_photo, featured_photo=featured_photo, caption="Photography Marketplace")


#  -----------------ADMIN SECTION------------------------

# --> constructed off of @login_required
def admin_required(view):
    @wraps(view)  
    def admin_view(*args, **kwargs):
        db = get_db()
        user = db.execute("""SELECT is_admin 
                          FROM users 
                          WHERE user_id = ?""", (session.get("user_id"),)).fetchone()
        
        if not user or not user["is_admin"]:
            return redirect(url_for("home")) 

        return view(*args, **kwargs) 
    
    return admin_view 


@app.route("/admin", methods=["GET", "POST"])
@admin_required
@login_required
def admin():
    return render_template("control_panel.html")


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]

@app.route("/admin/upload", methods=["GET", "POST"])
@login_required
@admin_required
def upload():
    db = get_db()
    themes = db.execute("""SELECT DISTINCT name FROM themes""").fetchall()

    theme_choices = []

    for theme in themes:
        theme_choices.append((theme["name"], theme["name"]))

    form = UploadPhotoForm()
    form.theme.choices = theme_choices
 
    if form.validate_on_submit():
        file = form.file.data
        title = form.title.data
        description = form.description.data
        theme = form.theme.data
        price_print = form.price_print.data
        price_license = form.price_license.data
        inventory = form.inventory.data

        if file and allowed_file(file.filename):
            filename = file.filename
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename).replace("\\", "/")

            file.save(file_path)

            db.execute("""INSERT INTO photos (title, description, theme, file_path, price_license, price_print, inventory) 
                       VALUES (?, ?, ?, ?, ?, ?, ?)""", (title, description, theme, file_path, price_license, price_print, inventory))
            
            db.commit()
            # selects the last row that was inserted
            photo_id = db.execute("""SELECT last_insert_rowid()""").fetchone()[0]

            db.execute("""INSERT INTO admin_logs (user_id, action, photo_id, title) 
                       VALUES (?, ?, ?, ?)""", (session["user_id"], "UPLOAD", photo_id, title))
            
            db.commit()

            flash("Photo uploaded successfully!", "success")
            return redirect(url_for("upload", theme=theme))
            
    return render_template("admin_upload.html", form=form)


@app.route('/admin/upload_limited', methods=['GET', 'POST'])
@admin_required
@login_required
def upload_limited():
    db = get_db()
    form = LimitedPhotoForm()

    if form.validate_on_submit():
        file = form.file.data
        title = form.title.data
        description = form.description.data
        base_price = float(form.base_price.data)

        if file and allowed_file(file.filename):
            filename = file.filename
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename).replace("\\", "/")

            file.save(file_path)

            db.execute("""INSERT INTO limited_photos (title, description, file_path, base_price, end_date) 
                       VALUES (?, ?, ?, ?, DATETIME('now', '+7 days'))""", (title, description, file_path, base_price))
            
            db.commit()

            photo_id = db.execute("""SELECT last_insert_rowid()""").fetchone()[0]

            if "user_id" in session:
                db.execute("""INSERT INTO admin_logs (user_id, action, photo_id, title) 
                       VALUES (?, ?, ?, ?)""", (session["user_id"], "UPLOAD", photo_id, title))
            
            db.commit()

            flash("Photo uploaded successfully!", "success")
            return redirect(url_for("upload_limited"))
            
    return render_template("admin_limited_upload.html", form=form)


@app.route("/admin/photos", methods=["GET", "POST"])
@admin_required
@login_required
def manage_photos():
    db = get_db()
    message = None
    
    # Delete a photo by title

    delete_form = DeletePhotoForm() 
    
    if delete_form.validate_on_submit():
        title = delete_form.delete_title.data.strip()

        photo = db.execute("""SELECT id, file_path FROM photos 
                           WHERE title = ?""", (title,)).fetchone()
        
        if photo:
            file_path = photo["file_path"]
            if file_path and os.path.exists(file_path):
                os.remove(file_path)

            db.execute("""DELETE FROM photos 
                       WHERE title = ?""", (title,))
            
            db.commit()

            db.execute("""INSERT INTO admin_logs (user_id, action, photo_id, title) 
                       VALUES 
                       (?, ?, ?, ?)""",
                       (session["user_id"], "DELETE", photo["id"], title))
            db.commit()
            return redirect(url_for("manage_photos"))
        else:
            message = "There is no photo"


    # Updating form section 
    photos = [dict(photo) for photo in db.execute("""SELECT * FROM photos""").fetchall()]

    update_forms = {}

    # Pre-fill the form with existing values 
    for photo in photos:
        form = UpdatePhotoForm()
        form.photo_id.data = photo["id"]
        form.title.data = photo["title"]
        form.description.data = photo["description"]
        form.price_license.data = photo["price_license"]
        form.price_print.data = photo["price_print"]
        form.inventory.data = photo["inventory"]

        
        update_forms[photo["id"]] = form

    if request.method == "POST":
        photo_id = int(request.form["photo_id"])
        form = dict(request.form)
        
        if form:
            new_title = form['title']
            new_description = form['description']
            new_price_license = float(form['price_license'] or 0.00)
            new_price_print = float(form['price_print'] or 0.00)
            new_inventory = form['inventory']

            db = get_db()
            db.execute("""UPDATE photos 
                           SET title = ?, description = ?, price_license = ?, price_print = ?, inventory = ? 
                           WHERE id = ?""",
                           (new_title, new_description, new_price_license, new_price_print, new_inventory, photo_id),)
            db.commit()

            db.execute("""INSERT INTO admin_logs (user_id, action, photo_id, title) 
                           VALUES 
                           (?, ?, ?, ?)""",(session["user_id"], "UPDATE", photo_id, new_title),)   
            db.commit()

            return redirect(url_for("manage_photos"))

    return render_template("admin_photos.html", photos=photos, delete_form=delete_form, update_forms=update_forms, message=message)


@app.route("/admin/logs", methods=["GET", "POST"])
@admin_required
@login_required
def view_logs():
    db = get_db()

    logs = db.execute("""SELECT * FROM admin_logs
                      ORDER BY timestamp""").fetchall()
    
    return render_template("admin_logs.html", logs=logs)


@app.route("/admin/payment-logs", methods=["GET", "POST"])
@admin_required
@login_required
def view_payment_logs():
    db = get_db()

    logs = db.execute("""SELECT * FROM admin_payment_logs
                      ORDER BY timestamp""").fetchall()
    
    return render_template("admin_payment_logs.html", logs=logs)



# # ----------------------- USER SECTION -------------------------

@app.route("/signup", methods=["GET", "POST"])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        user_id = form.user_id.data
        password = form.password.data
        db = get_db()
        clash = db.execute("""SELECT * FROM users
                           WHERE user_id = ?;""", (user_id,)).fetchone()
        if clash is not None:
            form.user_id.errors.append("This username has already been taken")
        else:
            db.execute("""INSERT INTO users (user_id, password) 
                       VALUES (?, ?);""", (user_id, generate_password_hash(password)))
            db.commit() 
            return redirect( url_for("login") )
    return render_template("signup.html", form=form, caption="Sign_up")


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user_id = form.user_id.data
        password = form.password.data
        db = get_db()
        user_in_db = db.execute("""SELECT * FROM users
                                WHERE user_id = ?;""", (user_id,)).fetchone()
        if user_in_db is None:
            form.user_id.errors.append("No such user name!")
        elif not check_password_hash(
                    user_in_db["password"], password):
            form.password.errors.append("Incorrect password!")
        else:
            session.clear()
            session["user_id"] = user_id
            session.modified = True
            next_page = request.args.get("next")
            if not next_page:
                next_page = url_for("home")
            return redirect(next_page)
    return render_template("login.html", form=form)


@app.route("/logout")
def logout():
    session.clear()
    session.modified = True
    return redirect( url_for("home") )


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    db = get_db()
    user_id = session["user_id"]

    purchases = db.execute("""SELECT purchases.*, photos.title, photos.file_path 
                           FROM purchases
                           JOIN photos ON purchases.photo_id = photos.id
                           WHERE purchases.user_id = ?
                           ORDER BY purchases.purchase_date""", (user_id,)).fetchall()
    
    return render_template("profile.html", purchases=purchases, user_id=user_id)


# # -------------MAIN CONTENT--------------------


@app.route("/gallery", methods=["GET", "POST"])
def gallery():
    db = get_db()
    themes = db.execute("""SELECT DISTINCT theme FROM photos""").fetchall()
    
    theme_choices = [("All", "All Themes")]
    for t in themes:
        theme_choices.append((t["theme"], t["theme"]))

    form = PhotoSearchForm()
    form.theme.choices = theme_choices  

    if form.validate_on_submit():
        session["theme"] = form.theme.data
        session["price_min"] = float(form.price_min.data or 0)
        session["price_max"] = float(form.price_max.data or 10000) 
        session["filter_type"] = form.filter_type.data

        session.modified = True

        return redirect( url_for('gallery') )

    elif request.method == "GET":
        form.theme.data = session.get("theme", "All")
        form.price_min.data = float(session.get("price_min", 0) or 0)
        form.price_max.data = float(session.get("price_max", 10000) or 10000)
        form.filter_type.data = session.get("filter_type", "both")

    theme = session.get("theme", "All")
    price_min = float(session.get("price_min", 0) or 0)
    price_max = float(session.get("price_max", 10000) or 10000)
    filter_type = session.get("filter_type", "both")

    query = "SELECT * FROM photos WHERE 1=1"
    placeholders = []

    if theme != "All":
        query += " AND theme = ?"
        placeholders.append(theme)

    if filter_type == "license":
        query += " AND price_license BETWEEN ? AND ?"
        placeholders.append(price_min)
        placeholders.append(price_max)
    elif filter_type == "print":
        query += " AND price_print BETWEEN ? AND ?"
        placeholders.append(price_min)
        placeholders.append(price_max)
    else:
        query += """ AND ( (price_license BETWEEN ? AND ?) AND (price_print BETWEEN ? AND ?) )"""
        placeholders.append(price_min)
        placeholders.append(price_max)
        placeholders.append(price_min)
        placeholders.append(price_max)

    photos = db.execute(query, placeholders).fetchall()

    return render_template("gallery.html", form=form, photos=photos, selected_theme=form.theme.data)


@app.route("/photo/<int:photo_id>", methods=["GET", "POST"])
@login_required
def photo_detail(photo_id):
    form = PurchaseForm()
    db = get_db()
    
    photo = db.execute("""SELECT * FROM photos WHERE id = ?""", (photo_id,)).fetchone()
    
    if not photo:
        return redirect( url_for("gallery" ) )

    if form.validate_on_submit(): 
        buy_license = form.buy_license.data
        buy_print = form.buy_print.data
        quantity = form.quantity.data


        if not buy_license and not buy_print:
            flash("Please select a purchase option", "error")
            return redirect( url_for("photo_detail", photo_id=photo_id) )

        if buy_print:
            if photo["inventory"] <= 0:
                flash("Sorry, this print is out of stock", "error")
                return redirect( url_for("photo_detail", photo_id=photo_id ))
            
            if quantity > photo["inventory"]:
                flash(f"Only {photo["inventory"]} prints available!", 'error')
                return redirect( url_for("photo_detail", photo_id=photo_id ))


        if "cart" not in session:
            session["cart"] = {}

        if photo_id not in session["cart"]:
            session["cart"][photo_id] = {"license": False, "print_qty": 0, "file_path": photo["file_path"]}

        if buy_license:
            session["cart"][photo_id]["license"] = True
        if buy_print:
            session["cart"][photo_id]["print_qty"] += quantity 

        session.modified = True  
        flash("Item added to cart!", "success")
        return redirect(url_for("cart"))

    return render_template("photo_detail.html", photo=photo, form=form)


@app.route("/cart", methods=["GET", "POST"])
@login_required
def cart():
    if "cart" not in session:
        session["cart"] = {}
        session.modified = True

    price = {}
    names = {}
    db = get_db()
    for photo_id in session["cart"]:
        photo = db.execute("""SELECT * FROM photos WHERE id = ?;""", (photo_id,)).fetchone()

        license = session["cart"][photo_id]["license"] 
        print_qty = session["cart"][photo_id]["print_qty"]

        total_price = 0.00
        if license:
            total_price += photo["price_license"]
        if print_qty >= 1:
            total_price += photo["price_print"] * print_qty
        price[photo_id] = round(total_price, 2)

        name = photo["title"]
        names[photo_id] = name

    total_price = sum(price.values())
    return render_template("cart.html", cart=session["cart"], names=names, price=price, total_price=total_price)


@app.route("/remove_from_cart/<int:photo_id>", methods=["GET", "POST"])
@login_required
def remove_from_cart(photo_id):
    if "cart" in session and photo_id in session["cart"]:
        del session["cart"][photo_id] 

        session.modified = True  

    return redirect(url_for("cart")) 


@app.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    if "cart" not in session:
        return redirect(url_for("cart"))

    cart = session["cart"]
    db = get_db()

    price = {}  # Store calculated prices per item
    names = {}  # Store item titles
    total_price = 0.00

    for photo_id in cart:
        photo = db.execute("""SELECT * FROM photos 
                           WHERE id = ?;""", (photo_id,)).fetchone()

        license = cart[photo_id]["license"]
        print_qty = cart[photo_id]["print_qty"]


        item_price = 0.00
        if license:
            item_price += photo["price_license"]
        if print_qty >= 1:
            item_price += photo["price_print"] * print_qty
        
        price[photo_id] = round(item_price, 2)
        names[photo_id] = photo["title"]
        total_price += item_price  
        total_price = round(total_price, 2)

        if print_qty > 0:
            if photo["inventory"] < print_qty:
                flash(f"Not enough stock for {photo["title"]}!", 'error')
                return redirect( url_for("cart" ))
            
            db.execute("""UPDATE photos SET inventory = inventory - ?
                       WHERE id = ?""",(print_qty, photo_id) )
            
            db.commit()

    db = get_db()

    form = CheckoutForm()
    
    if form.validate_on_submit():
        user_id = session["user_id"]

        db.execute("""INSERT INTO purchases (user_id, photo_id, license, print_qty, price_license, price_print, purchase_date)
                   VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""", (user_id, photo_id, license, print_qty, photo["price_license"] if license else 0, photo["price_print"] * print_qty))

        db.execute(
            """INSERT INTO admin_payment_logs (user_id, print_qty, total) 
            VALUES (?,?, ?)""",(user_id, print_qty, total_price))
        
        db.commit()

        session["cart"] = {}  
        return redirect(url_for("order_confirmation"))

    return render_template("checkout.html", cart=cart, names=names, price=price, total_price=total_price, form=form)

@app.route("/order_confirmation")
@login_required
def order_confirmation():
    return render_template("order_confirmation.html")


# # ----------LIMITED ITEM SECTION/BIDDING-------------


@app.route('/limited_edition')
@login_required
def limited_edition():
    db = get_db()
    
    photos = db.execute("""SELECT * FROM limited_photos 
                        WHERE end_date > DATETIME('now')""").fetchall()
    
    bids = db.execute("""SELECT bids.user_id, bids.bid_amount, limited_photos.title 
                      FROM bids 
                      JOIN users ON bids.user_id = users.user_id 
                      JOIN limited_photos ON bids.photo_id = limited_photos.id
                      ORDER BY bids.bid_amount DESC 
                      LIMIT 10""").fetchall()
    
    return render_template("limited_gallery.html", photos=photos, bids=bids)


@app.route('/bid/<int:photo_id>', methods=['GET', 'POST'])
@login_required
def bid_on_photo(photo_id):
    db = get_db()
    form = BidForm()

    photo = db.execute("""SELECT * FROM limited_photos 
                       WHERE id = ?""", (photo_id,)).fetchone()

    if not photo:
        flash("Photo not found!", "error")
        return redirect(url_for("limited_edition"))

    highest_bid = db.execute("""SELECT MAX(bid_amount) FROM bids 
                             WHERE photo_id = ?""", (photo_id,)).fetchone()[0] or photo["base_price"]

    if form.validate_on_submit():
        bid_amount = float(form.bid_amount.data)
        if highest_bid is not None:
            highest_bid = float(highest_bid)
        else:
            float(photo["base_price"])
        
        if bid_amount <= highest_bid or bid_amount <= photo["base_price"]:
            flash("Your bid must be higher than the current highest bid!", "error")
        else:
            db.execute("""INSERT INTO bids (photo_id, user_id, bid_amount) 
                       VALUES (?, ?, ?)""",(photo_id, session["user_id"], bid_amount))
            
            db.commit()
            
            flash("Bid placed successfully!", "success")

        return redirect( url_for("bid_on_photo", photo_id=photo_id) )

    return render_template("bid.html", form=form, photo=photo, highest_bid=highest_bid)


@app.route("/process_bid", methods=["GET", "POST"])
def process_bid():
    db = get_db()

    ended_bids = db.execute("""SELECT limited_photos.id AS photo_id, limited_photos.title, limited_photos.file_path, 
                            bids.user_id, MAX(bids.bid_amount) AS highest_bid
                            FROM limited_photos
                            JOIN bids ON limited_photos.id = bids.photo_id
                            WHERE limited_photos.end_date < DATETIME('now')
                            GROUP BY limited_photos.id;""").fetchall()

    for bid in ended_bids:
        db.execute("""INSERT INTO admin_payment_logs (user_id, print_qty, amount_paid)
                   VALUES (?, ?, ?)""", (bid["user_id"], 1, bid["highest_bid"]))

        db.commit()

        db.execute("""DELETE FROM limited_photos 
                   WHERE id = ?""", (bid["photo_id"],))
        
        db.commit() 

    return "Bids processed!"

