# NBA-Database-Manager #
This project contains a web scrapping program that gathers relevant team, game, player, and performance information from every recorded game provided by Basketball-Reference and performs CRUD operations within a personal NBA statistics SQL database.

## Web Scrapping ##
* HTML gathered using request library
* HTML parser using Beautiful Soup library
* Key pages including the \teams and \players page are sifted for all relevant URLs of individual team and player performances.
* Unique team and player data are collected into respective tables.
* Game and performance data are added with foregin reference to respective teams and players.

## Database Management ##
* Database connection managed using mysql.connector library
* Program seeks to update existing entities or insert if needed.
* Update processes can be adjusted to only sift for pages of events after a certain date to improve update speeds.

Database information scrapped for personal use only from https://www.basketball-reference.com/ 

SQL schema documented with diagraming to come.
