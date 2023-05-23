# Rainmaker
## Video Demo:  https://youtu.be/pyTOten6tMI
## Description:
Rainmaker is a website for gambling on weather, specifically on whether there will be precipitation within certain timeframe at certain location. Its backend is built with Django and SQLite while the front-end with JavaScript. The website can automatically fetch weather data from an external API to determine the outcome of each betting pool and update relevant users' account balance. It also allows users to inquire the chance of precipitation at a particular GPS coordinate, maintain a watchlist of betting pools, search for pools by keywords, and add funds to their accounts.

## Distinctiveness and Complexity:
Rainmaker is **distinct** from the Network project because the interactions among Rainmaker's users are much more than mere text exchanges; users of Rainmakers can create betting pools for other users to bet against and the settlement requires no human interaction whatsoever. 

The aforementioned auto-settlement feature is also what distinguishes Rainmaker from the Commerce project. In the Commerce project, even the highest bids may not win the listing because the listing's creator has the discretion to close or not to close a listing, but Rainmaker takes such human discretion away; the outcome of each betting pool is determined by weather data obtained from a supposedly neutral third-party (Open-Meteo) and the relevant users' account balances are debited/credited in a real-time manner.

The **complexity** of Rainmaker lies in the following three factors:
1. Whenever a page is loaded, Rainmaker obtains weather data from Open-Meteo to determine the outcome of each betting pool shown on the page, and then updates the pools' cosmetics and contents as well as the user's balance (if applicable) **without** re-loading the page.

2. Besides frontend validation enforced by the forms, Rainmaker includes comprehensive backend validation to ensure that only valid bets (i.e., within max bet and not exceeding the user's balance) from eligible users (i.e., users who are authenticated, _didn't_ create the pool, and have sufficient funds in their accounts) are accepted.

3. To provide a seamless user experience, Rainmaker doesn't require page reloading when a user places a bet, updates their watchlist or obtains a forecast of precipitation.

## Functions:
Unauthenticated users have access to the following functions:
- Active Pools
- Search
- Odds

In addition to the above, authenticated users have access to the functions below:
- New Pool
- Bet
- Maintain watchlist
- Profile

### Active Pools
Active Pools shows all betting pools of which the outcomes remain undetermined, in reverse chronological order, thus helping users efficiently find a pool to bet their life savings on.

### Search
Users can search for betting pools by key words, such as the latitude, longitude and date shown in the pools' details as well as the pools' creators (i.e., the houses/bankers).

### Odds
By inputting a GPS coordinate and a timeslot, users can inquire how likely a particular place at a particular time is going to rain. This function's purpose in life is to help Rainmaker users make better gambling decisions.

### New Pool
An authenticated user can create a new pool. Each pool is basically a prediction - at so & so location at so & so time it will rain. Each pool has its own odds and max bet. Only users with non-negative account balances can create a new pool and the max bet is automatically enforced to check each bet placed by other users. Once Rainmaker determines the pool's outcome, it will credit or debit the pool's creator (i.e., the house/banker) automatically.

### Bet
Authenticated users can place bet on other users' pools, but not their own. Once a bet is made, the user's account is debited and can be found in the user's profile page. Once Rainmaker determines the pool's outcome, it will credit winning punters' accounts automatically.

### Maintain watchlist
Authenticated users can add betting pools to their watchlists, or remove them later on. The number of items in their watchlists is shown in the navigation bar and updated without reloading the webpage.

### Profile
The Profile page has three sub-functions:
1. allowing users to add funds to their accounts, which requires valid credit card information,
2. showing the list of bets the users have placed wagers on, and
3. redirecting users to the list of betting pools created by themselves.
If the user has a negative account balance, a nice, threatening message is displayed at the top to remind users that they need to pay up.

## Project Files:
There is only one app, called gambling. Inside its folder are the following files/folders:

### views.py
It contains the functions that validate transactions and render webpages.

### helpers.py
This file contains a few functions that were factored out from views.py, as they are used by multiple views' functions to sort and process data extracted from the database.

### models.py
It essentially defines the schema of Rainmaker's database.

### urls.py
It basically maps the URLs with the functions defined in views.py.

### static folder
CSS style sheet and JavaScript script that handle the webpages' cosmetics and make the webpage interactive.

### templates folder
The folder contains all the html files that will be rendered when users execute the aforementioned functions.

### others
The other files contained in the gambling folder were generated by default when the Django project folder was created. The same is true for the files and folder contained in the capstone folder.

Inside of the main directory, there are manage.py, a text file called requirements.txt and this README. The former was, again, created by default. The text file lists out the dependencies of the Rainmaker project.