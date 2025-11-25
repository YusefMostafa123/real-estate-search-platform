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

''' used with live serching not local file
def get_crime_counts(conn, lat, lon):
    """
    Return (total_crimes, felonies, misdemeanors) within the chosen radius
    around (lat, lon).
    """
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
          COUNT(*) AS total_crimes,
          SUM(CASE WHEN LAW_CAT_CD = 'F' THEN 1 ELSE 0 END) AS felonies,
          SUM(CASE WHEN LAW_CAT_CD = 'M' THEN 1 ELSE 0 END) AS misdemeanors
        FROM NYPDArrestData
        WHERE
          Latitude  BETWEEN ? AND ?
          AND Longitude BETWEEN ? AND ?
          AND (Latitude  - ?) * (Latitude  - ?) +
              (Longitude - ?) * (Longitude - ?) <= ?
        """,
        (
            lat - RADIUS_DEG, lat + RADIUS_DEG,
            lon - RADIUS_DEG, lon + RADIUS_DEG,
            lat, lat, lon, lon, RADIUS_SQ,
        ),
    )
    row = cur.fetchone()
    cur.close()

    total = row["total_crimes"] or 0
    felonies = row["felonies"] or 0
    misdemeanors = row["misdemeanors"] or 0
    return total, felonies, misdemeanors
'''

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
'''' USed when we did not have local file
@app.route("/search")
def search():
    if "user_id" not in session:
        return redirect(url_for("login"))

    # --- read filters from query string (GET params) ---
    q = request.args.get("q", "").strip()

    min_price = request.args.get("min_price", "").strip()
    max_price = request.args.get("max_price", "").strip()

    min_beds = request.args.get("min_beds", "").strip()
    max_beds = request.args.get("max_beds", "").strip()

    min_baths = request.args.get("min_baths", "").strip()
    max_baths = request.args.get("max_baths", "").strip()

    min_sqft = request.args.get("min_sqft", "").strip()
    max_sqft = request.args.get("max_sqft", "").strip()

    sort = request.args.get("sort", "price_asc")  # default

    # ---- crime / school checkbox filters ----
    filter_keys = [
        "crime_low", "crime_medium", "crime_high",
        "school_low", "school_medium", "school_high",
    ]
    has_filter_params = any(k in request.args for k in filter_keys)

    def cb_on(name: str) -> bool:
        # If user hasn't touched filters yet: everything = checked
        if not has_filter_params:
            return True
        return request.args.get(name) == "1"

    crime_low_checked = cb_on("crime_low")
    crime_med_checked = cb_on("crime_medium")
    crime_high_checked = cb_on("crime_high")

    school_low_checked = cb_on("school_low")
    school_med_checked = cb_on("school_medium")
    school_high_checked = cb_on("school_high")

    # --- build SQL dynamically, but ONLY basic filtering in SQL ---
    sql = """
        SELECT ID, FORMATTED_ADDRESS, PRICE, BEDS, BATH, PROPERTYSQFT, COUNTY,
               LATITUDE, LONGITUDE
        FROM NYHouseDataset
    """
    conditions = []
    params = []

    # flexible address search (case-insensitive, partial)
    if q:
        conditions.append("UPPER(FORMATTED_ADDRESS) LIKE '%' || UPPER(?) || '%'")
        params.append(q)

    # price range
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

    # beds range
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

    # baths range
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

    # sqft range
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

    if conditions:
        sql += " WHERE " + " AND ".join(conditions)

    # IMPORTANT:
    # Use a fixed, neutral ordering + LIMIT so the candidate pool
    # is the same regardless of user sort choice.
    CANDIDATE_LIMIT = 250  # tweak if you want
    sql += f" ORDER BY ID LIMIT {CANDIDATE_LIMIT}"

    conn = get_db()
    cur = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()

    # ---- enrich with crime + school and apply checkbox filters ----
    results = []

    for row in rows:
        lat = row["LATITUDE"]
        lon = row["LONGITUDE"]

        # crime info
        total_crimes, felonies, misdemeanors = get_crime_counts(conn, lat, lon)
        crime_label = crime_severity_label(total_crimes)  # "Low"/"Medium"/"High"

        # school info
        school = get_nearest_school(conn, lat, lon)
        if school is not None and school["performance_level"]:
            perf_text = school["performance_level"]
            # e.g. "High performance" -> "High"
            school_band = perf_text.split()[0].capitalize()
        else:
            school_band = "Medium"  # neutral default

        # crime filter
        crime_ok = (
            (crime_low_checked and crime_label == "Low") or
            (crime_med_checked and crime_label == "Medium") or
            (crime_high_checked and crime_label == "High")
        )

        # school filter
        school_ok = (
            (school_low_checked and school_band == "Low") or
            (school_med_checked and school_band == "Medium") or
            (school_high_checked and school_band == "High")
        )

        if not (crime_ok and school_ok):
            continue

        d = dict(row)
        d["crime_label"] = crime_label
        d["school_band"] = school_band
        results.append(d)

    conn.close()

    # ---- final sort happens in Python on the filtered pool ----
    def sort_key(h):
        if sort.startswith("price"):
            return h["PRICE"] or 0
        if sort.startswith("sqft"):
            return h["PROPERTYSQFT"] or 0
        if sort.startswith("beds"):
            return h["BEDS"] or 0
        if sort.startswith("baths"):
            return h["BATH"] or 0
        # fallback
        return h["PRICE"] or 0

    reverse = sort.endswith("desc")
    results.sort(key=sort_key, reverse=reverse)

    # show at most 100 in the UI
    results = results[:100]

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
'''

#used with local file
# ---------- SEARCH ----------
@app.route("/search")
def search():
    if "user_id" not in session:
        return redirect(url_for("login"))

    # --- read filters from query string (GET params) ---
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
            h.ID,
            h.FORMATTED_ADDRESS,
            h.PRICE,
            h.BEDS,
            h.BATH,
            h.PROPERTYSQFT,
            h.COUNTY,
            hs.total_crimes,
            hs.crime_severity,
            hs.school_band
        FROM NYHouseDataset AS h
        LEFT JOIN HouseStats AS hs
          ON hs.HouseID = h.ID
    """
    conditions = []
    params = []

    if q:
        conditions.append("UPPER(h.FORMATTED_ADDRESS) LIKE '%' || UPPER(?) || '%'")
        params.append(q)

    if min_price:
        try:
            conditions.append("h.PRICE >= ?")
            params.append(int(min_price))
        except ValueError:
            pass

    if max_price:
        try:
            conditions.append("h.PRICE <= ?")
            params.append(int(max_price))
        except ValueError:
            pass

    if min_beds:
        try:
            conditions.append("h.BEDS >= ?")
            params.append(int(min_beds))
        except ValueError:
            pass

    if max_beds:
        try:
            conditions.append("h.BEDS <= ?")
            params.append(int(max_beds))
        except ValueError:
            pass

    if min_baths:
        try:
            conditions.append("h.BATH >= ?")
            params.append(float(min_baths))
        except ValueError:
            pass

    if max_baths:
        try:
            conditions.append("h.BATH <= ?")
            params.append(float(max_baths))
        except ValueError:
            pass

    if min_sqft:
        try:
            conditions.append("h.PROPERTYSQFT >= ?")
            params.append(int(min_sqft))
        except ValueError:
            pass

    if max_sqft:
        try:
            conditions.append("h.PROPERTYSQFT <= ?")
            params.append(int(max_sqft))
        except ValueError:
            pass

    if conditions:
        sql += " WHERE " + " AND ".join(conditions)

    CANDIDATE_LIMIT = 400
    sql += f" ORDER BY h.ID LIMIT {CANDIDATE_LIMIT}"

    conn = get_db()
    cur = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()

    results = []

    for row in rows:
        crime_label = row["crime_severity"] or "Medium"
        school_band = row["school_band"] or "Medium"

        crime_ok = (
            (crime_low_checked and crime_label == "Low") or
            (crime_med_checked and crime_label == "Medium") or
            (crime_high_checked and crime_label == "High")
        )

        school_ok = (
            (school_low_checked and school_band == "Low") or
            (school_med_checked and school_band == "Medium") or
            (school_high_checked and school_band == "High")
        )

        if not (crime_ok and school_ok):
            continue

        d = dict(row)
        d["crime_label"] = crime_label
        d["school_band"] = school_band
        results.append(d)

    def sort_key(h):
        if sort.startswith("price"):
            return h["PRICE"] or 0
        if sort.startswith("sqft"):
            return h["PROPERTYSQFT"] or 0
        if sort.startswith("beds"):
            return h["BEDS"] or 0
        if sort.startswith("baths"):
            return h["BATH"] or 0
        return h["PRICE"] or 0

    reverse = sort.endswith("desc")
    results.sort(key=sort_key, reverse=reverse)

    results = results[:100]

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

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT h.*
        FROM Favorites f
        JOIN NYHouseDataset h ON f.home_id = h.ID
        WHERE f.user_id = ?
    """, (session["user_id"],))
    rows = cur.fetchall()
    conn.close()

    return render_template("favorites.html", favorites=rows)

@app.route("/favorites/add", methods=["POST"])
def add_favorite():
    if "user_id" not in session:
        return redirect(url_for("login"))

    home_id = request.form["home_id"]

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT OR IGNORE INTO Favorites(user_id, home_id)
        VALUES (?, ?)
    """, (session["user_id"], home_id))
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
    cur.execute("""
        DELETE FROM Favorites
        WHERE user_id = ? AND home_id = ?
    """, (session["user_id"], home_id))
    conn.commit()
    conn.close()

    return redirect(url_for("favorites"))

# ---------- LISTING DETAILS ----------
@app.route("/listing/<int:home_id>")
def listing_detail(home_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM NYHouseDataset WHERE ID = ?", (home_id,))
    house = cur.fetchone()
    if not house:
        conn.close()
        return "House not found", 404

    house_lat = house["LATITUDE"]
    house_lon = house["LONGITUDE"]

    cur.execute("""
        SELECT
            ID,
            school_name,
            borough,
            overall_score,
            performance_level,
            lat,
            long,
            ((lat - ?) * (lat - ?) + (long - ?) * (long - ?)) AS dist_sq
        FROM NYSchoolDataset
        ORDER BY dist_sq
        LIMIT 1
    """, (house_lat, house_lat, house_lon, house_lon))
    srow = cur.fetchone()

    if srow:
        dist_sq = srow["dist_sq"]
        distance_miles = (dist_sq ** 0.5) * 69.0
        perf_level = srow["performance_level"] or ""

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
            perf_band = perf_level or "Unknown"
            school_badge_class = "bg-secondary text-white"

        school_info = {
            "name": srow["school_name"],
            "borough": srow["borough"],
            "overall_score": srow["overall_score"],
            "performance_band": perf_band,
            "badge_class": school_badge_class,
            "distance_miles": distance_miles,
        }
    else:
        school_info = None
    radius_deg = 0.01
    radius_sq = radius_deg * radius_deg

    cur.execute("""
        SELECT
            COUNT(*) AS total_crimes,
            SUM(CASE WHEN LAW_CAT_CD = 'F' THEN 1 ELSE 0 END) AS felonies,
            SUM(CASE WHEN LAW_CAT_CD = 'M' THEN 1 ELSE 0 END) AS misdemeanors
        FROM NYPDArrestData
        WHERE
            (Latitude  - ?) * (Latitude  - ?) +
            (Longitude - ?) * (Longitude - ?) <= ?
    """, (house_lat, house_lat, house_lon, house_lon, radius_sq))

    total_crimes, felonies, misdemeanors = cur.fetchone()

    total_crimes = total_crimes or 0
    felonies = felonies or 0
    misdemeanors = misdemeanors or 0

    if total_crimes > 0:
        felony_rate = felonies / total_crimes
        misdemeanor_rate = misdemeanors / total_crimes
    else:
        felony_rate = 0.0
        misdemeanor_rate = 0.0

    if total_crimes <= 166:
        severity_label = "Low"
        badge_class = "bg-success text-white"
    elif total_crimes <= 625:
        severity_label = "Medium"
        badge_class = "bg-warning text-dark"
    else:
        severity_label = "High"
        badge_class = "bg-danger text-white"

    crime_info = {
        "total_crimes": total_crimes,
        "felonies": felonies,
        "misdemeanors": misdemeanors,
        "felony_rate": felony_rate,
        "misdemeanor_rate": misdemeanor_rate,
        "severity_label": severity_label,
        "badge_class": badge_class,
    }

    conn.close()

    return render_template(
        "listing_detail.html",
        house=house,
        school=school_info,
        crime=crime_info,
    )


if __name__ == "__main__":
    app.run(debug=True)
