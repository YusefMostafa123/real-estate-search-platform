import db, page_loader, requests
from flask import Flask, render_template, request, redirect, url_for, session

# Startup Sequence
app = Flask("Home Listing and Price Explorer")

def run():
    db.init_db()
    app.secret_key = "change-this"
    app.config["EXPLAIN_TEMPLATE_LOADING"] = True
    app.run(debug=True, port = 5001)


# Page Endpoints
@app.route("/search")
def search():
    return page_loader.load_search(request)

@app.route("/favorites")
def favorites():
    return page_loader.load_favorites(request)

@app.route("/favorites/add", methods=["POST"])
def add_favorite():
    return requests.process_add_favorite(request)

@app.route("/favorites/remove", methods=["POST"])
def remove_favorite():
    return requests.process_remove_favorite(request)

@app.route("/listing/<int:home_id>")
def listing_by_id(home_id):
    return page_loader.load_listing(home_id)

@app.route("/compare")
def compare():
    return page_loader.load_compare(request)

@app.route("/favorites/listing/<int:home_id>")
def favorite_listing(home_id):
    return page_loader.load_favorite_listing_by_id(home_id)

@app.route("/logout")
def logout():
    return requests.proccess_logout()

@app.route("/admin_home")
def admin_home():
    return requests.process_admin_login()

@app.route("/home")
def home():
    return page_loader.load_home()

@app.route("/add_listing", methods=["GET", "POST"])
def add_listing():
    return requests.process_add_listing(request)

@app.route("/")
def index():
    return page_loader.load_index()

@app.route("/register", methods=["GET", "POST"])
def register():
    return requests.process_register(request)

@app.route("/login", methods=["GET", "POST"])
def login():
    return requests.process_login(request = request)


# Finally, we run the app!
run()