CREATE TABLE IF NOT EXISTS UserInformation (
    UserID      TEXT PRIMARY KEY,
    Password    TEXT NOT NULL,
    Status      TEXT NOT NULL 
);

CREATE TABLE IF NOT EXISTS NYHouseDataset (
    ID               INTEGER PRIMARY KEY,
    BROKERTITLE      TEXT,
    TYPE             TEXT,
    PRICE            INTEGER,
    BEDS             INTEGER,
    BATH             INTEGER,
    PROPERTYSQFT     INTEGER,
    FORMATTED_ADDRESS TEXT,
    LATITUDE         REAL,
    LONGITUDE        REAL,
    COUNTY           TEXT
);

CREATE TABLE IF NOT EXISTS NYPDArrestData (
    "Index"        INTEGER PRIMARY KEY,
    ARREST_KEY     INTEGER,
    ARREST_DATE    TEXT,
    PD_DESC        TEXT,
    OFNS_DESC      TEXT,
    LAW_CAT_CD     TEXT,
    ARREST_BORO    TEXT,
    ARREST_PRECINCT INTEGER,
    AGE_GROUP      TEXT,
    PERP_SEX       TEXT,
    PERP_RACE      TEXT,
    Latitude       REAL,
    Longitude      REAL,
    Location       TEXT
);

CREATE TABLE IF NOT EXISTS NYSchoolDataset (
    ID               INTEGER PRIMARY KEY,
    school_name      TEXT,
    borough          TEXT,
    building_code    TEXT,
    average_math     REAL,
    average_reading  REAL,
    average_writing  REAL,
    percent_tested   REAL,
    lat              REAL,
    long             REAL,
    overall_score    REAL,
    performance_level TEXT
);

CREATE TABLE IF NOT EXISTS Favorites (
    favorite_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     TEXT NOT NULL,
    home_id     INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES UserInformation(UserID),
    FOREIGN KEY (home_id) REFERENCES NYHouseDataset(ID),
    UNIQUE(user_id, home_id)
);

----------------------------------------added for daving local file
CREATE TABLE IF NOT EXISTS HouseStats (
    HouseID               INTEGER PRIMARY KEY,
    total_crimes          INTEGER,
    felonies              INTEGER,
    misdemeanors          INTEGER,
    crime_severity        TEXT,   -- 'Low' / 'Medium' / 'High'
    school_id             INTEGER,
    school_distance_miles REAL,
    school_band           TEXT    -- 'Low' / 'Medium' / 'High'
);

CREATE INDEX IF NOT EXISTS idx_housestats_school
    ON HouseStats (school_id);
