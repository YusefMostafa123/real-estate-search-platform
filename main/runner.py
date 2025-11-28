import db, page_loader, requests, sys, util, time # type: ignore
from flask import Flask, request

# Startup Sequence
util.clear_terminal()
app = Flask(
    import_name= "Home Listing and Price Explorer",
    template_folder = f'{util.ROOT}/templates',
    static_folder = f'{util.ROOT}/static')

app.secret_key = 'CS480'
app.config['EXPLAIN_TEMPLATE_LOADING'] = ("-d" in sys.argv)

def run():
    util.print_welcome_message()
    if "-l" in sys.argv:
        util.print_init_db_message()
        db.init_db()
    app.run(debug=("-d" in sys.argv), port = util.PORT)


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
    return requests.process_logout()

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