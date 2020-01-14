import nbadb_sifter #functions to siftweb and produce list for update
import table_headers #headers for each table in nba database
import update_urls #URLs used to grab desired data from web
from private import nba_database as my_db #database information including username and password
import mysql.connector as db


def db_connect () :
    '''
    Uses database information from an imported dictionary to attempt to establish
    and return a connection class object.
    Param:
    Output: mysql.connection class object
    '''
    try: #Attempt to connect to sql database
        new_connection = db.connect(
            user = my_db["user"],
            password = my_db["password"],
            host = my_db["host"],
            database = my_db["database"])
    except db.Error as err: #Catch error and print specific message
        if err.errno == db.errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == db.errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)

    return new_connection


def update_teams ():
    '''
    Calls web HTML sifter to create list of NBA teams including past, present, and entities representing
    a cumulative of both if the franchise name/city/league has changed. Either UPDATES or INSERTS each list
    within a list into the database table.
    PARAM:  Imported list - Table Headers
            Imported List of Lists - NBA teams
            Imported String - Basketball-reference.com URL for team page
    OUTPUT: Updates or adds to sql table 'teams' in 'nba' database.
    '''
    headers = table_headers.teams_headers #Access sql column headers for team table
    teams_list = nbadb_sifter.get_teams_list(update_urls.teams_url) #Call for creation of list of lists for NBA teams
    nba_connection = db_connect() #Connect to NBA database
    cursor = nba_connection.cursor() #Init cursor object for NBA database

    for team in teams_list: #For every team in the list of teams
        #First section takes advanage of the fact that as constructed rows whose data represents the entire history of a
        #franchise even as name/city/league changed are added first. Rows will look for the names of those franchises to
        #reassign the name of their representative current or cummulative row to the tid of the correct entity.
        try: #Query trying to find the tid of a cummulative all-time franchise row whose name matches this team's parent/current 
            query = "SELECT {} FROM teams WHERE {} = \'{}\' AND {} = {} ;".format(headers[0], headers[2], team[14], headers[1], "True")
            cursor.execute(query) 
            for tid in cursor: #If a result is found then reassign 'current' value in list to match tid of their parent fanchise row
                team[14] = tid[0] #If not found then index remains as it was, which is NULL
        except db.Error as error: #Catch and print possible error
            print("Error: {}".format(error))

        try: #Without using tid check if this unique entity is already present and try to return tid
            query = "SELECT {} FROM teams WHERE {} = \'{}\' AND {} = \'{}\' AND {} = {} ;".format(headers[0], headers[2], team[1], headers[3], team[2], headers[4], team[3])
            cursor.execute(query)
            row_count = 0
            for tid in cursor: #if select returns an entity then call UPDATE and iterate row_count to pass INSERT call
                try:
                    query = "UPDATE teams SET {} = \'{}\', {} = \'{}\', {} = \'{}\', {} = \'{}\', {} = \'{}\', {} = {} WHERE {} = \'{}\' ;".format(headers[1], team[0], headers[2], team[1], headers[3], team[2], headers[4], team[3], headers[5], team[4], headers[6], team[14], headers[0], tid)
                    cursor.execute(query)
                    nba_connection.commit()
                except db.Error as error:
                    print("Error: {}".format(error))
                row_count += 1
            if row_count == 0: #If count still 0 then no tid was returned and entity needs to be newly inserted into table
                try:
                    query = "INSERT INTO teams ({}, {}, {}, {}, {}, {}) VALUES ({}, \'{}\', \'{}\', {}, {}, \'{}\') ;".format(headers[1], headers[2], headers[3], headers[4], headers[5], headers[6], team[0], team[1], team[2], team[3], team[4], team[14])
                    cursor.execute(query)
                    nba_connection.commit()
                except db.Error as error:
                    print("Error: {}".format(error))
                
        except db.Error as error:
            print("Error: {}".format(error))

    nba_connection.close()


def update_games ():
    #headers = table_headers.games_headers #Access sql column headers for team table
    seasons_list = nbadb_sifter.get_seasons_list(update_urls.teams_url) #Call for creation of list of lists for NBA teams
    #seasons_list = ['https://www.basketball-reference.com/teams/ATL/2019_games.html']
    nba_connection = db_connect() #Connect to NBA database
    cursor = nba_connection.cursor(dictionary=True) #Init cursor object for NBA database

    fd = open('error_messages.txt', 'w')
    count = 1
    for season in seasons_list:
        print(season)
        games_list = nbadb_sifter.get_season_games(season)
        if games_list != None:
            for game in games_list:
                home_id = 0
                away_id = 0
                if int(game[0][5:7]) < 8:
                    year = int(game[0][0:4])
                else:
                    year = int(game[0][0:4]) + 1

                try:
                    query = "SELECT tid, total FROM teams WHERE franchise = \'{}\' AND date_from <= {} AND date_to >= {} ; ".format(game[2], year, year)
                    cursor.execute(query)
                    #nba_connection.commit()
                    for result in cursor:
                        if result['total'] == '0':
                            home_id = int(result['tid'])
                        else:
                            home_id = int(result['tid'])
                    query = "SELECT tid, total FROM teams WHERE franchise = \'{}\' AND date_from <= {} AND date_to >= {} ; ".format(game[3], year, year)
                    cursor.execute(query)
                    #nba_connection.commit()
                    for result in cursor:
                        if result['total'] == '0':
                            away_id = int(result['tid'])
                        else:
                            away_id = int(result['tid'])
                except db.Error as error:
                    print("Error: {}".format(error))

                gid = game[0][0:4] + game[0][5:7] + game[0][8:10] + '{:03d}'.format(home_id) + '{:03d}'.format(away_id)

                try:
                    insert = "INSERT INTO games (gid, date, time, home_id, away_id, overtime, home_score, away_score) "
                    #values = "VALUES ( {}, \'{}\', \'{}\', {}, {}, {}, {}, {} ) ".format(gid, game[0], game[1], home_id, away_id, game[4], game[5], game[6])
                    if game[1] == 'NULL':
                        values = "SELECT {}, \'{}\', {}, {}, {}, {}, {}, {} FROM dual ".format(gid, game[0], game[1], home_id, away_id, game[4], game[5], game[6])
                    else:
                        values = "SELECT {}, \'{}\', \'{}\', {}, {}, {}, {}, {} FROM dual ".format(gid, game[0], game[1], home_id, away_id, game[4], game[5], game[6])
                    #duplicate = "ON DUPLICATE KEY UPDATE date=VALUES(date), time=VALUES(time), home_id=VALUES(home_id), away_id=VALUES(away_id), overtime=VALUES(overtime), home_score=f, away_score=g ; "
                    duplicate = "WHERE NOT EXISTS (SELECT * FROM games WHERE games.gid = {}) ; ".format(gid)
                    query = insert + values + duplicate
                    #print(query)
                    cursor.execute(query)
                    nba_connection.commit()
                    #print("Success on date {}".format(game[0]))
                except db.Error as error:
                    fd.write("Error: {}\n".format(error))
                    fd.write("offendings game date was {}... home_id = {}... away_id = {}... adjusted year = {}\n".format(game[0], home_id, away_id, year))
                    print("Error: {}".format(error))
                    print("offendings game date was {}... home_id = {}... away_id = {}... adjusted year = {}".format(game[0], home_id, away_id, year))
            count += 1
    
    fd.close()



#update_teams()
update_games()
