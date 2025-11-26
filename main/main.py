from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from pathlib import Path
import math

RADIUS_MILES = 0.6 
MILES_PER_DEGREE = 69.0
RADIUS_DEG = RADIUS_MILES / MILES_PER_DEGREE
RADIUS_SQ = RADIUS_DEG * RADIUS_DEG

LOW_MAX_CRIMES = 166 
MEDIUM_MAX_CRIMES = 625


app = Flask(__name__)
app.secret_key = "change-this"

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "home_explorer.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def crime_severity_label(total_crimes: int) -> str:

    if total_crimes <= LOW_MAX_CRIMES:
        return "Low"
    elif total_crimes <= MEDIUM_MAX_CRIMES:
        return "Medium"
    else:
        return "High"


def get_nearest_school(conn, lat, lon):
    cur = conn.cursor()
    cur.execute(
        """
        SELECT *,
               ((lat - ?) * (lat - ?) + (long - ?) * (long - ?)) AS dist_sq
        FROM NYSchoolDataset
        ORDER BY dist_sq
        LIMIT 1
        """,
        (lat, lat, lon, lon),
    )
    school = cur.fetchone()
    cur.close()
    return school
@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("home"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user_id = request.form["user_id"]
        password = request.form["password"]

        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM UserInformation WHERE UserID = ? AND Password = ?",
            (user_id, password),
        )
        row = cur.fetchone()
        conn.close()

        if row:
            session["user_id"] = user_id
            return redirect(url_for("home"))
        else:
            return render_template("login.html", error="Invalid credentials")

    return render_template("login.html", error=None)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        user_id = request.form["user_id"]
        password = request.form["password"]
        status = request.form["status"]

        conn = get_db()
        cur = conn.cursor()

        cur.execute("SELECT 1 FROM UserInformation WHERE UserID = ?", (user_id,))
        exists = cur.fetchone()

        if exists:
            conn.close()
            return render_template("register.html",
                                   error="That User ID is already taken.")

        cur.execute("""
            INSERT INTO UserInformation (UserID, Password, Status)
            VALUES (?, ?, ?)
        """, (user_id, password, status))
        conn.commit()
        conn.close()

        return redirect(url_for("login"))

    return render_template("register.html", error=None)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ---------- HOME ----------
@app.route("/home")
def home():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("home.html", user_id=session["user_id"])


# ---------- SEARCH ----------
@app.route("/search")
def search():
    if "user_id" not in session:
        return redirect(url_for("login"))

    q = request.args.get("q", "").strip()

    min_price = request.args.get("min_price", "").strip()
    max_price = request.args.get("max_price", "").strip()

    min_beds = request.args.get("min_beds", "").strip()
    max_beds = request.args.get("max_beds", "").strip()

    min_baths = request.args.get("min_baths", "").strip()
    max_baths = request.args.get("max_baths", "").strip()

    min_sqft = request.args.get("min_sqft", "").strip()
    max_sqft = request.args.get("max_sqft", "").strip()

    sort = request.args.get("sort", "price_asc")

    filter_keys = [
        "crime_low", "crime_medium", "crime_high",
        "school_low", "school_medium", "school_high",
    ]
    has_filter_params = any(k in request.args for k in filter_keys)

    def cb_on(name: str) -> bool:
        if not has_filter_params:
            return True
        return request.args.get(name) == "1"

    crime_low_checked = cb_on("crime_low")
    crime_med_checked = cb_on("crime_medium")
    crime_high_checked = cb_on("crime_high")

    school_low_checked = cb_on("school_low")
    school_med_checked = cb_on("school_medium")
    school_high_checked = cb_on("school_high")

    sql = """
        SELECT
            ID,
            FORMATTED_ADDRESS,
            PRICE,
            BEDS,
            BATH,
            PROPERTYSQFT,
            COUNTY,
            total_crimes,
            crime_severity,
            school_band
        FROM NYHouseDataset
    """
    conditions = []
    params = []

    if q:
        conditions.append("UPPER(FORMATTED_ADDRESS) LIKE '%' || UPPER(?) || '%'")
        params.append(q)

    if min_price:
        try:
            conditions.append("PRICE >= ?")
            params.append(int(min_price))
        except ValueError:
            pass

    if max_price:
        try:
            conditions.append("PRICE <= ?")
            params.append(int(max_price))
        except ValueError:
            pass

    if min_beds:
        try:
            conditions.append("BEDS >= ?")
            params.append(int(min_beds))
        except ValueError:
            pass

    if max_beds:
        try:
            conditions.append("BEDS <= ?")
            params.append(int(max_beds))
        except ValueError:
            pass

    if min_baths:
        try:
            conditions.append("BATH >= ?")
            params.append(float(min_baths))
        except ValueError:
            pass

    if max_baths:
        try:
            conditions.append("BATH <= ?")
            params.append(float(max_baths))
        except ValueError:
            pass

    if min_sqft:
        try:
            conditions.append("PROPERTYSQFT >= ?")
            params.append(int(min_sqft))
        except ValueError:
            pass

    if max_sqft:
        try:
            conditions.append("PROPERTYSQFT <= ?")
            params.append(int(max_sqft))
        except ValueError:
            pass

    crime_labels = []
    if crime_low_checked:
        crime_labels.append("Low")
    if crime_med_checked:
        crime_labels.append("Medium")
    if crime_high_checked:
        crime_labels.append("High")
        
    if has_filter_params and crime_labels and len(crime_labels) < 3:
        placeholders = ", ".join("?" * len(crime_labels))
        conditions.append(f"COALESCE(crime_severity, 'Medium') IN ({placeholders})")
        params.extend(crime_labels)

    school_labels = []
    if school_low_checked:
        school_labels.append("Low")
    if school_med_checked:
        school_labels.append("Medium")
    if school_high_checked:
        school_labels.append("High")

    if has_filter_params and school_labels and len(school_labels) < 3:
        placeholders = ", ".join("?" * len(school_labels))
        conditions.append(f"COALESCE(school_band, 'Medium') IN ({placeholders})")
        params.extend(school_labels)

    if conditions:
        sql += " WHERE " + " AND ".join(conditions)

    sort_map = {
        "price_asc":  "PRICE ASC",
        "price_desc": "PRICE DESC",
        "sqft_asc":   "PROPERTYSQFT ASC",
        "sqft_desc":  "PROPERTYSQFT DESC",
        "beds_asc":   "BEDS ASC, PRICE ASC",
        "beds_desc":  "BEDS DESC, PRICE ASC",
        "baths_asc":  "BATH ASC, PRICE ASC",
        "baths_desc": "BATH DESC, PRICE ASC",
    }
    order_by = sort_map.get(sort, "PRICE ASC")
    sql += f" ORDER BY {order_by} LIMIT 100"

    conn = get_db()
    cur = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()

    results = [dict(r) for r in rows]

    return render_template(
        "search.html",
        results=results,
        search_q=q,
        min_price=min_price,
        max_price=max_price,
        min_beds=min_beds,
        max_beds=max_beds,
        min_baths=min_baths,
        max_baths=max_baths,
        min_sqft=min_sqft,
        max_sqft=max_sqft,
        sort=sort,
        crime_low=crime_low_checked,
        crime_medium=crime_med_checked,
        crime_high=crime_high_checked,
        school_low=school_low_checked,
        school_medium=school_med_checked,
        school_high=school_high_checked,
    )
    
# ---------- FAVORITES ----------
@app.route("/favorites")
def favorites():
    if "user_id" not in session:
        return redirect(url_for("login"))

    # range filters
    price_min = request.args.get("price_min", type=int)
    price_max = request.args.get("price", type=int)

    beds_min = request.args.get("beds", type=int)
    beds_max = request.args.get("beds_max", type=int)

    baths_min = request.args.get("baths", type=float)
    baths_max = request.args.get("baths_max", type=float)

    sqft_min = request.args.get("sqft", type=int)
    sqft_max = request.args.get("sqft_max", type=int)

    # sort dropdown (Price asc, Price desc, Sqft asc/desc, Beds asc/desc, Baths asc/desc)
    sort_by = request.args.get("sort_by", default="price_asc", type=str)

    query = """
        SELECT h.*
        FROM Favorites f
        JOIN NYHouseDataset h ON f.home_id = h.ID
        WHERE f.user_id = ?
    """
    params = [session["user_id"]]

    # price range
    if price_min is not None:
        query += " AND h.PRICE >= ?"
        params.append(price_min)
    if price_max is not None:
        query += " AND h.PRICE <= ?"
        params.append(price_max)

    # beds range
    if beds_min is not None:
        query += " AND h.BEDS >= ?"
        params.append(beds_min)
    if beds_max is not None:
        query += " AND h.BEDS <= ?"
        params.append(beds_max)

    # baths range
    if baths_min is not None:
        query += " AND h.BATH >= ?"
        params.append(baths_min)
    if baths_max is not None:
        query += " AND h.BATH <= ?"
        params.append(baths_max)

    # sqft range
    if sqft_min is not None:
        query += " AND h.PROPERTYSQFT >= ?"
        params.append(sqft_min)
    if sqft_max is not None:
        query += " AND h.PROPERTYSQFT <= ?"
        params.append(sqft_max)

    # sorting for favorites
    sort_map = {
        "price_asc":  "h.PRICE ASC",
        "price_desc": "h.PRICE DESC",
        "sqft_asc":   "h.PROPERTYSQFT ASC",
        "sqft_desc":  "h.PROPERTYSQFT DESC",
        "beds_asc":   "h.BEDS ASC, h.PRICE ASC",
        "beds_desc":  "h.BEDS DESC, h.PRICE ASC",
        "baths_asc":  "h.BATH ASC, h.PRICE ASC",
        "baths_desc": "h.BATH DESC, h.PRICE ASC",
    }
    order_clause = sort_map.get(sort_by, "h.PRICE ASC")
    query += " ORDER BY " + order_clause

    conn = get_db()
    cur = conn.cursor()
    cur.execute(query, tuple(params))
    rows = cur.fetchall()
    conn.close()

    current_filters = {
        "price_min": price_min,
        "price_max": price_max,
        "beds_min": beds_min,
        "beds_max": beds_max,
        "baths_min": baths_min,
        "baths_max": baths_max,
        "sqft_min": sqft_min,
        "sqft_max": sqft_max,
    }

    return render_template(
        "favorites.html",
        favorites=rows,
        current_sort=sort_by,
        current_filters=current_filters,
    )


@app.route("/favorites/add", methods=["POST"])
def add_favorite():
    if "user_id" not in session:
        return redirect(url_for("login"))

    home_id = request.form["home_id"]

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO Favorites(user_id, home_id) VALUES (?, ?)",
        (session["user_id"], home_id),
    )
    conn.commit()
    conn.close()

    return redirect(url_for("search"))


@app.route("/favorites/remove", methods=["POST"])
def remove_favorite():
    if "user_id" not in session:
        return redirect(url_for("login"))

    home_id = request.form["home_id"]

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM Favorites WHERE user_id = ? AND home_id = ?",
        (session["user_id"], home_id),
    )
    conn.commit()
    conn.close()

    return redirect(url_for("favorites"))


# ---------- LISTING DETAILS ----------
@app.route("/listing/<int:home_id>")
def listing_detail(home_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT
            h.*,
            s.school_name,
            s.borough,
            s.overall_score,
            s.performance_level
        FROM NYHouseDataset h
        LEFT JOIN NYSchoolDataset s
          ON s.ID = h.school_id
        WHERE h.ID = ?
    """, (home_id,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return "House not found", 404

    house = row

    total_crimes = row["total_crimes"] or 0
    felonies = row["felonies"] or 0
    misdemeanors = row["misdemeanors"] or 0
    crime_severity = row["crime_severity"] or "Medium"

    if total_crimes > 0:
        felony_rate = felonies / total_crimes
        misdemeanor_rate = misdemeanors / total_crimes
    else:
        felony_rate = 0.0
        misdemeanor_rate = 0.0

    if crime_severity == "Low":
        badge_class = "bg-success text-white"
    elif crime_severity == "Medium":
        badge_class = "bg-warning text-dark"
    else:
        badge_class = "bg-danger text-white"

    crime_info = {
        "total_crimes": total_crimes,
        "felonies": felonies,
        "misdemeanors": misdemeanors,
        "felony_rate": felony_rate,
        "misdemeanor_rate": misdemeanor_rate,
        "severity_label": crime_severity,
        "badge_class": badge_class,
    }

    if row["school_name"]:
        perf_level = row["performance_level"] or ""
        if "High" in perf_level:
            perf_band = "High"
            school_badge_class = "bg-success text-white"
        elif "Medium" in perf_level:
            perf_band = "Medium"
            school_badge_class = "bg-warning text-dark"
        elif "Low" in perf_level:
            perf_band = "Low"
            school_badge_class = "bg-danger text-white"
        else:
            perf_band = "Unknown"
            school_badge_class = "bg-secondary text-white"

        school_info = {
            "name": row["school_name"],
            "borough": row["borough"],
            "overall_score": row["overall_score"],
            "performance_band": perf_band,
            "badge_class": school_badge_class,
            "distance_miles": row["school_distance_miles"],
        }
    else:
        school_info = None

    return render_template(
        "listing_detail.html",
        house=house,
        school=school_info,
        crime=crime_info,
    )

# ---------- LISTING DETAILS Fav----------

@app.route("/favorites/listing/<int:home_id>")
def listing_detail_fav(home_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT
            h.*,
            s.school_name,
            s.borough,
            s.overall_score,
            s.performance_level
        FROM NYHouseDataset h
        LEFT JOIN NYSchoolDataset s
          ON s.ID = h.school_id
        WHERE h.ID = ?
    """, (home_id,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return "House not found", 404

    house = row

    total_crimes = row["total_crimes"] or 0
    felonies = row["felonies"] or 0
    misdemeanors = row["misdemeanors"] or 0
    crime_severity = row["crime_severity"] or "Medium"

    if total_crimes > 0:
        felony_rate = felonies / total_crimes
        misdemeanor_rate = misdemeanors / total_crimes
    else:
        felony_rate = 0.0
        misdemeanor_rate = 0.0

    if crime_severity == "Low":
        badge_class = "bg-success text-white"
    elif crime_severity == "Medium":
        badge_class = "bg-warning text-dark"
    else:
        badge_class = "bg-danger text-white"

    crime_info = {
        "total_crimes": total_crimes,
        "felonies": felonies,
        "misdemeanors": misdemeanors,
        "felony_rate": felony_rate,
        "misdemeanor_rate": misdemeanor_rate,
        "severity_label": crime_severity,
        "badge_class": badge_class,
    }

    if row["school_name"]:
        perf_level = row["performance_level"] or ""
        if "High" in perf_level:
            perf_band = "High"
            school_badge_class = "bg-success text-white"
        elif "Medium" in perf_level:
            perf_band = "Medium"
            school_badge_class = "bg-warning text-dark"
        elif "Low" in perf_level:
            perf_band = "Low"
            school_badge_class = "bg-danger text-white"
        else:
            perf_band = "Unknown"
            school_badge_class = "bg-secondary text-white"

        school_info = {
            "name": row["school_name"],
            "borough": row["borough"],
            "overall_score": row["overall_score"],
            "performance_band": perf_band,
            "badge_class": school_badge_class,
            "distance_miles": row["school_distance_miles"],
        }
    else:
        school_info = None

    return render_template(
        "listing_detail_fav.html", 
        house=house,
        school=school_info,
        crime=crime_info,
    )

if __name__ == "__main__":
    app.run(debug=True)
