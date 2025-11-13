# OverView  
Our goal with the Home Listing and Price Explorer project is to make a data driven application that will help users explore and analyze property listings. It is designed to function as a property search tool and a dashboard for visualizing trends. Using our dataset, which reflects real world housing data, users will be able to look up homes, filter results based on things like price, area, number of bedrooms or bathrooms, and location, and see analytics that summarize price distributions of homes.

The main goal of the program is to give an intuitive and visually pleasing way to understand data about housing, letting users compare listings and make informed decisions. It will mix the functionality of a typical listing browser with functions, including searching and filtering, with a dashboard component, like displaying charts and averages.

There will be one main role in our system: 
Program User: can utilize all the functionality talked about, including browse, filter, and sort listings, view property details, and analyze charts. The user will also be able to list favorite listings.

We will use a real estate data set with around 2000 rows to represent a diverse and balanced scale that is big enough for realistic analytics but small enough for us to be able to have interactive filtering and fast visualization.

# Data Requirements  
Our program is built around our dataset of home listings. Each record represents one residential property and includes its main descriptive and numerical attributes.

### Listings  
for each property we have our dataset contains:  
Id (unique listing identifier)  
Area (total square footage of the property)  
Bedrooms (number of bedrooms)  
Bathrooms (number of bathrooms)  
Floors (number of floors)  
YearBuilt (the year the home was constructed)  
Location (category of area (Downtown, Suburban, Urban, or Rural))  
Condition – (rating of the home’s overall condition (Excellent, Good, Fair, Poor))  
Garage – (indicates whether a garage is available (Yes/No))  
Price – (current market listing price in USD)  

### User (for favorites and reviews)  
UserId, Name, Email, PasswordHash  

### Favorites  
Represents a many to many relationship between users and listings.  
Each record stores (UserId, ListingId)  

### Reviews  
Each review belongs to a single user and a single listing.  
Attributes include (ReviewId, UserId, ListingId, Rating [1–5], Comment)  

This data structure will support the dashboard analytics (using numerical attributes like price, area, and year built) and  app interactions (using listings, users, favorites, and reviews))  

# Application Requirements  

### User:

### Agent

### Computed Behavior



