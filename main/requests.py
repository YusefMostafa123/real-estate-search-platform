from flask import render_template, redirect, url_for, session
import db

def process_add_favorite(request):
    if "user_id" not in session:
        return redirect(url_for("login"))

    home_id = request.form["home_id"]

    conn = db.get()
    conn.execute(
        "INSERT OR IGNORE INTO Favorites(user_id, home_id) VALUES (?, ?)",
        (session["user_id"], home_id),
    )
    conn.commit()
    conn.close()

    return redirect(url_for("search"))

def process_remove_favorite(request):
    if "user_id" not in session:
        return redirect(url_for("login"))

    home_id = request.form["home_id"]

    conn = db.get()
    conn.execute(
        "DELETE FROM Favorites WHERE user_id = ? AND home_id = ?",
        (session["user_id"], home_id),
    )
    conn.commit()
    conn.close()

    return redirect(url_for("favorites"))

def process_logout():
    session.clear()
    return redirect(url_for("login"))

def process_admin_login():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("admin_home.html", user_id=session["user_id"])

def process_login(request):
    if request.method == "POST":
        user_id = request.form["user_id"]
        password = request.form["password"]   
        conn = db.get()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM UserInformation WHERE UserID = ? AND Password = ?",
            (user_id, password),
        )
        row = cur.fetchone()
        conn.close()
        
        if row:
            session["user_id"] = user_id
            status = row["Status"]
            session["status"] = status 
            if status == "Admin":
                return redirect(url_for("admin_home"))
            return redirect(url_for("home"))
        else:
            return render_template("login.html", error="Invalid credentials")

    return render_template("login.html", error=None)

def process_register(request):
    if request.method == "POST":
        user_id = request.form["user_id"]
        password = request.form["password"]
        status = request.form["status"]

        conn = db.get()
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

def process_add_listing(request):
    if request.method == "POST":
        title = request.form["title"]
        address = request.form["address"]
        ptype = request.form["type"]
        beds = request.form["beds"]           # FIX: was "status"
        baths = request.form["baths"]
        sqrft = request.form["sqrft"]
        price = request.form["price"]
        lat = request.form["lat"]
        long = request.form["long"]
        county = request.form["county"]

        conn = db.get()
        cur = conn.cursor()

        # Dup check: address
        cur.execute("SELECT 1 FROM NYHouseDataset WHERE FORMATTED_ADDRESS = ?", (address,))
        if cur.fetchone():
            conn.close()
            return render_template("add_listing.html", error="Property already exists at that address.")

        # Dup check: lat/long
        cur.execute("SELECT 1 FROM NYHouseDataset WHERE LATITUDE = ? AND LONGITUDE = ?", (lat, long))
        if cur.fetchone():
            conn.close()
            return render_template("add_listing.html", error="Property already exists at that Latitude and Longitude.")

        # Next ID (start at 1 if table empty)
        cur.execute("SELECT ID FROM NYHouseDataset ORDER BY ID DESC LIMIT 1")
        row2 = cur.fetchone()
        next_id = (row2["ID"] if row2 else 0) + 1

        # Insert (18 columns -> 18 placeholders)
        cur.execute(
            """
            INSERT INTO NYHouseDataset
            (ID, BROKERTITLE, TYPE, PRICE, BEDS, BATH, PROPERTYSQFT, FORMATTED_ADDRESS,
             LATITUDE, LONGITUDE, COUNTY, total_crimes, felonies, misdemeanors,
             crime_severity, school_id, school_distance_miles, school_band)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                next_id, title, ptype, price, beds, baths, sqrft, address,
                lat, long, county, 0, 0, 0, "NA", 0, 0, "NA",
            ),
        )
        conn.commit()
        conn.close()
        return redirect(url_for("admin_home"))

    # GET
    return render_template("add_listing.html", user_id=session["user_id"])