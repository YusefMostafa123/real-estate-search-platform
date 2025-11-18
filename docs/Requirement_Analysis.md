# Overview  
Our goal with the Home Listing and Price Explorer project is to make a data driven application that will help users explore and analyze property listings for New York City. It is designed to function as a property search tool and a dashboard for visualizing trends.

Our application will combine multiple public data sets so the user can not only see the basic information you would expect to see about a home listing like price, beds, baths, size but also have a deep understanding of the context and the surroundings of the home like nearby crime, school quality, fire department coverage, hospital accessibility, and borough demographic which will give users a richer understanding of the environment around each home.

There will be two main roles in our system: 
Program User: The buyer can utilize all the functionality like searching listings, filter results, view detailed neighborhood indicators, save favorites.
Admin: Is responsible for maintaining the data in the system. Admins can load cleaned datasets into the database, refresh them when new versions are available, and control thresholds for analytics, for example, the ranges we use to check nearby crimes.

# Data Requirements  
Our program is built around several integrated tables. The housing table is central and main one, and the other datasets will enrich each listing with neighborhood indicators.

### Housing Data (NY-Housing-Dataset-Cleaned)
For each property, we have our dataset contains:  
Id (unique listing identifier)(PK), BROKERTITLE (listing broker), TYPE (house/apartment type), PRICE (listing price), BEDS, BATH (bedroom and bathroom count), PROPERTYSQFT (property size), FORMATTED_ADDRESS (full property address), LATITUDE, LONGITUDE (location for mapping), COUNTY (borough where the home is)  
#### Purpose: This is the central table used to connect homes to the neighborhood info.  

### Crime Data (NYPD-Arrest-Data-Cleaned)  
Columns we have:  
Index, ARREST_KEY (unique identifiers) (PK), PD_DESC, OFNS_DESC (offense descriptions), LAW_CAT_CD (crime level (felony/misdemeanor)), ARREST_BORO, ARREST_PRECINCT (location info), AGE_GROUP, PERP_SEX, PERP_RACE (demographic info), Latitude, Longitude (location of arrest)  
#### Purpose: This table will be used to calculate crime density/count around each home.  

### School Data (Schools+Locations-Cleaned) 
-These are two tables that we have joined together at this point  
Each school has:  
ID (unique school identifier) (PK), school_name, borough, building_code (School info), average_math, average_reading, average_writing (exam performance), percent_tested (percent of students tested), lat, long (school location), overall_score, performance_level (school rating (we calculated it using exam performance))  
#### Purpose: This table will be used to give every home a school quality score using the closest school.  

### Fire Department Coverage (FDNY-Borough-Scores_Cleaned)  
Each borough has:  
Borough (PK), Stations (count of fire stations), SquareMiles (borough land area), FD_Score_raw (stations per square mile), FD_Score_100 (scaled fire safety score (0–100))  
#### Purpose: Used to give borough fire safety for homes in that borough.  

### Hospital Data (NY-Hospitals-Cleaned) 
Columns:  
Facility ID (PK), Facility Name (unique identifiers), Address, County/Parish (borough), Hospital overall rating (quality score), Hospital Ownership (Private/Public), Patient_Survey_Rating (satisfaction metric), Latitude, Longitude (hospital location), Hospital_Quality_Label (Low/Medium/High)  
#### Purpose: Used to calculate hospital accessibility score and performance for each home.  

### Borough Age Distribution (NYC-Population-Cleaned)
Columns:  
Borough (PK), Male %, Female %, Age groups (0-14, 15-29, 30-44, 45-59, 60-74, 75+) (in %)   
#### Purpose: Used to calculate age distribution for each borough.  

### Log In  
Columns:
User_id (PK), Password, Status (Admin/User)

### Favorites   
Columns: favorite_id (PK), user_id, home_id  

### Relationships:  
Housing - Borough:
Each home belongs to exactly one borough. Borough level tables (FDNY scores and Population/Age) provide extra attributes.  
Housing - Crime:
A home can have zero or many nearby crime incidents based on distance range. Crime counts are aggregated per home.  
Housing - Schools:
Each home is linked to one and only one school, the closest school by coordinates. A school may correspond to many homes.  
Housing - Hospitals:
Each home is linked to one and only one closest hospital. A hospital may serve many homes.  
Borough - FDNY / Population:
Each borough has one fire coverage score and one demographic row used for dashboard analytics.  


# Application Requirements 

## Functional Requirements  
User:  
* The system must allow users to search home listings by filters such as price range, beds, baths, and property type.  
* For each home listing, the user will see the Closest school + school score, the Closest hospital + quality label, Nearby crimes within 0.8 miles, the Borough fire safety score, and the Borough age group that the home is located in.  
*  Users must be able to save listings to a personal “Favorites” list.

Admin:  
*Replace cleaned datasets, detect missing coordinates, rebuild SQLite tables.

## Visual Requirements 
* Provides a smooth, responsive, styled UI with clear sections for search, results, listing details and  a dashboard. 
* Ensures consistent layout across pages: landing page, search page, results page, listing page, and admin upload page.

## Performance Requirements
* The system should return typical search results within 2–3 seconds.
* Database queries should be optimized with indexing on frequently used columns
* The system must support loading datasets up to several hundred rows without crashing or timing out

## Design Goals
* Keeps the interface simple and informative, prioritizing clarity over complexity.
* Maintains consistent styling and branding across all pages.
* Contains a visual landing page as a 'home'.


# Web Technologies 
### Client
- HTML5 – page structure
- CSS3 + Bootstrap 5 – layout + responsive styling

Handles user interaction, sends GET/POST requests to the backend, and displays enriched home listing results.

### Server
- Python
- Flask – routing, request handling, server logic

Processes all client requests, queries SQLite, performs joins and calculations (crime density, nearest school, nearest hospital, borough metrics), and returns HTML or JSON.

### Development Tools
- VS Code
- Git & GitHub
- DB Browser for SQLite / SQLiteStudio 

Used for development, dataset cleaning, debugging, and version control.



# ER Diagram 


