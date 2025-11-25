import math
import sqlite3
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "home_explorer.db"
CLEANED = ROOT / "data" / "cleaned"

MILES_PER_DEG = 69.0 


def crime_severity_label(total_crimes: int) -> str:
    """Map total crimes to Low / Medium / High."""
    if total_crimes <= 166:
        return "Low"
    elif total_crimes <= 625:
        return "Medium"
    else:
        return "High"


def get_crime_counts(conn, lat, lon, radius_miles=0.6):
    radius_deg = radius_miles / MILES_PER_DEG
    lat_min = lat - radius_deg
    lat_max = lat + radius_deg
    lon_min = lon - radius_deg
    lon_max = lon + radius_deg

    cur = conn.cursor()

    cur.execute(
        """
        SELECT Latitude, Longitude, LAW_CAT_CD
        FROM NYPDArrestData
        WHERE Latitude BETWEEN ? AND ?
          AND Longitude BETWEEN ? AND ?
        """,
        (lat_min, lat_max, lon_min, lon_max),
    )

    total = 0
    felonies = 0
    misdemeanors = 0
    radius_sq = radius_deg * radius_deg

    for c_lat, c_lon, law_cat in cur:
        dlat = c_lat - lat
        dlon = c_lon - lon
        if dlat * dlat + dlon * dlon > radius_sq:
            continue

        total += 1
        if law_cat == "F":
            felonies += 1
        elif law_cat == "M":
            misdemeanors += 1

    return total, felonies, misdemeanors


def get_nearest_school(conn, lat, lon, search_radius_miles=2.0):
    radius_deg = search_radius_miles / MILES_PER_DEG
    lat_min = lat - radius_deg
    lat_max = lat + radius_deg
    lon_min = lon - radius_deg
    lon_max = lon + radius_deg

    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            ID,
            school_name,
            borough,
            overall_score,
            performance_level,
            lat,
            long
        FROM NYSchoolDataset
        WHERE lat BETWEEN ? AND ?
          AND long BETWEEN ? AND ?
        """,
        (lat_min, lat_max, lon_min, lon_max),
    )
    rows = cur.fetchall()

    if not rows:
        cur.execute(
            """
            SELECT
                ID,
                school_name,
                borough,
                overall_score,
                performance_level,
                lat,
                long
            FROM NYSchoolDataset
            """
        )
        rows = cur.fetchall()
        if not rows:
            return None, None

    best_row = None
    best_dist_sq = None
    for row in rows:
        s_lat = row["lat"]
        s_lon = row["long"]
        dlat = s_lat - lat
        dlon = s_lon - lon
        dist_sq = dlat * dlat + dlon * dlon
        if best_row is None or dist_sq < best_dist_sq:
            best_row = row
            best_dist_sq = dist_sq

    return best_row, best_dist_sq


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    with open(Path(__file__).parent / "schema.sql", "r") as f:
        conn.executescript(f.read())

    cur.execute("DELETE FROM NYHouseDataset")
    cur.execute("DELETE FROM NYPDArrestData")
    cur.execute("DELETE FROM NYSchoolDataset")
    conn.commit()

    houses = pd.read_csv(CLEANED / "NY-House-Dataset-Cleaned.csv")
    houses.to_sql("NYHouseDataset", conn, if_exists="append", index=False)

    crime = pd.read_csv(CLEANED / "NYPD-Arrest-Data-Cleaned.csv")
    crime.to_sql("NYPDArrestData", conn, if_exists="append", index=False)

    schools = pd.read_csv(CLEANED / "Schools+Locations-Cleaned.csv")
    schools.to_sql("NYSchoolDataset", conn, if_exists="append", index=False)

    print("Precomputing crime & school stats into NYHouseDataset...")

    cur.execute("SELECT ID, LATITUDE, LONGITUDE FROM NYHouseDataset")
    house_rows = cur.fetchall()

    for h in house_rows:
        hid = h["ID"]
        lat = h["LATITUDE"]
        lon = h["LONGITUDE"]

        total, fel, mis = get_crime_counts(conn, lat, lon)
        crime_sev = crime_severity_label(total)

        school_row, dist_sq = get_nearest_school(conn, lat, lon)
        if school_row:
            school_id = school_row["ID"]
            distance_miles = (
                math.sqrt(dist_sq) * MILES_PER_DEG if dist_sq is not None else None
            )
            perf_text = school_row["performance_level"] or ""
            if perf_text:
                school_band = perf_text.split()[0].capitalize()
            else:
                school_band = "Medium"
        else:
            school_id = None
            distance_miles = None
            school_band = "Medium"

        cur.execute(
            """
            UPDATE NYHouseDataset
            SET total_crimes          = ?,
                felonies              = ?,
                misdemeanors          = ?,
                crime_severity        = ?,
                school_id             = ?,
                school_distance_miles = ?,
                school_band           = ?
            WHERE ID = ?
            """,
            (total, fel, mis, crime_sev,
             school_id, distance_miles, school_band, hid),
        )

    conn.commit()
    conn.close()
    print("Done! Database with precomputed stats at", DB_PATH)


if __name__ == "__main__":
    main()