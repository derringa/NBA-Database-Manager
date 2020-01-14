import requests
from bs4 import BeautifulSoup


#################################################
# Teams SQL table management
#################################################


def format_team_list(teamList):
    ''' 
    Converts format of from and to year for a team on the team list
    Param:  List of strings characterizing an NBA team
            list[3] = year started YYYY-YY
            list[4] = year ended YYYY-YY
    Output: Both indeces loose the middle 2 digits and hypen
            list[3] = YYYY
            list [4] = YYYY
    '''
    teamList[3] = teamList[3][0:2] + teamList[3][5:7] #Convert to year
    teamList[4] = teamList[4][0:2] + teamList[4][5:7] #Convert to year

    #Fix the only found inconsistency in team naming on page to date
    if teamList[1] == 'NO/Ok. City Hornets':
        teamList[1] = 'New Orleans/Oklahoma City Hornets'
    if teamList[1] == 'Providence Steam Rollers':
        teamList[1] = 'Providence Steamrollers'

    return(teamList)


def get_teams_headers(tableHeadTag):
    '''
    Iterates through and grabs desired strings from HTML orgamized
    into an object by beautiful soup library.
    Param:  Beautiful soup object iterable by HTML tags
    Output: Python list of strings for desired column titles.
    '''
    columnTitles = []
    #Iterate to each th in tHead to and append to list of column headers
    for child in tableHeadTag:
        string = child.string
        if '\n' not in string and '\xa0' not in string: #Disregard strings containing undesired information
            columnTitles.append(string)
    columnTitles.insert(0, "Total") #Add title to beginning for franchise total column
    columnTitles.append("Current") #Add title to end for current franchise identifier name

    return columnTitles


def get_teams_list(teamsPage):
    '''
    Iterates through and grabs desired strings to create a comprehensive list
    of NBA franchises and their characteristics from HTML organized into an 
    object by beautiful soup library.
    Param: String URL for basketball-reference.com teams page
    Output: Python list of strings for desired team data
            ["tid", "total", "franchise", "league", "date_from", "date_to", "current"]
    '''
    #fetch the desired page
    page = requests.get(teamsPage)
    #Create a beautifulSoup object
    soup = BeautifulSoup(page.text, 'html.parser')

    #Create a tag from desired table of data from active teams within HTML
    activeTableTag = soup.find(id='teams_active')
    #Tag of tbody with desired rows of active team data.
    activeBodyTag = activeTableTag.contents[6]
    #Create a tag from desired table of data from defunct teams within HTML
    defunctTableTag = soup.find(id='teams_defunct')
    #Tag of tbody with desired rows of defunct team data.
    defunctBodyTag = defunctTableTag.contents[6]
    
    tags_list = [activeBodyTag, defunctBodyTag]
    teamsList = []

    for tag in tags_list:
        list_length = len(list(tag))
        #Goes through each team in range of html table using length of object tags
        for team in range(1, list_length, 2):
            teamTag = tag.contents[team] #Assign current team to tag
            teamStats = [] #initialize empty list for team stats
            franchiseTotal = 'False' #Identifier of whether row represents all-time total franchise stats

            if teamTag.has_attr('class') and teamTag['class'][0] == 'full_table': #Catches all rows representating all time total franchise stats
                currentFranchise = teamTag.contents[0] #Variable holds name of most recently iterated all time total franchise
                franchiseTotal = 'True' #Marks the current iterating team as representing all time total franchise stats

            #If that particular tr has class='thead' we don't want it.
            if teamTag.has_attr('class') and teamTag['class'][0] == 'thead':
                continue
            else:
                teamStats.append(franchiseTotal) #Append false unless current row identified as all time totals
                #For loop iterates through each td to append string value
                for child in teamTag:
                    teamStats.append(child.string) #Append each td within tr to list
                if franchiseTotal == 'True': #If list represents all time team total then value is NUULL
                    teamStats.append('NULL')
                else: 
                    teamStats.append(currentFranchise.string) #Else append name of current franchise this line is associated with to end of list
                teamsList.append(format_team_list(teamStats)) #Format current list and append to greater list of teams

    return(teamsList)


#################################################
# Games SQL table management
#################################################


def get_seasons_list(teamsPage):
    '''
    Uses basketball-reference teams page to find the URL of every NBA
    team page active and defunct. It passes the page on so that it can
    be scraped for all links to that franchises individual seasons which
    are then returned to concaternate one master list. That list can be used
    To build a python list of list of formatted data for sql database input.
    PARAM:  URL - basketball-reference total teams page
    OUTPUT: Python list - URL to every individual season in NBA history.
    '''
    #fetch the desired page
    page = requests.get(teamsPage)
    #Create a beautifulSoup object
    soup = BeautifulSoup(page.text, 'html.parser')

    #Create a tag from desired table of data from active teams within HTML
    activeTableTag = soup.find(id='teams_active')
    #Tag of tbody with desired rows of active team data.
    activeBodyTag = activeTableTag.contents[6]
    #Create a tag from desired table of data from defunct teams within HTML
    defunctTableTag = soup.find(id='teams_defunct')
    #Tag of tbody with desired rows of active team data.
    defunctBodyTag = defunctTableTag.contents[6]
    
    tags_list = [activeBodyTag, defunctBodyTag] #list to iterate through current and old teams
    league_seasons_list = []

    for tag in tags_list: #Iterate through current and old teams in tags_list
        for link in tag.find_all('a'): #Reduce tags list to only 'a' tags
            address = link.get('href') #Only get those that are links to web pages
            team_page = "https://www.basketball-reference.com" + address
            league_seasons_list += get_team_seasons(team_page) #Concaternate one large list of NBA seasons

    return league_seasons_list


def get_team_seasons(team_page):
    '''
    Receives NBA team page and scraped for every team season page in team history returned as a python list.
    PARAM:  URL - basketball-reference single NBA team page
    OUTPUT: Python list - URL for every individual season data in team history.
    '''
    #Need team abbreviation found in every URL to find needed HTML tag later
    page_id = "div_" + team_page[-4:-1]
    #fetch the desired page
    page = requests.get(team_page)
    #Create a beautifulSoup object
    soup = BeautifulSoup(page.text, 'html.parser')

    #Create a tag from desired table of data from all seasons meta-data within HTML
    activeTableTag = soup.find(id=page_id)
    #Tag of tbody with desired rows of season data.
    activeBodyTag = activeTableTag.contents[1]
    
    team_seasons_list = []
    for link in activeBodyTag.find_all('a'): #Reduce tags list to only 'a' hyperlink tags
        address = link.get('href') #Only get link from a tag
        if "teams" in address and link.parent.name == 'th': #Multiple tags with the same URL, only grab first in table header
            team_page = "https://www.basketball-reference.com" + address[0:-5] + "_games.html" #reformat to make season games URL
            team_seasons_list.append(team_page)

    return team_seasons_list


def format_season_stats (team_game_list):
    '''
    Receives python list of a single game from a team's season. Strips
    Undesired information and converts it to be SQL ready.
    PARAM:  Python list -
            [game, date, time, NULL, page's team, away indicator, opponent,
            W/L indicator, OT indicator, win count, loss count, streak, notes]
    OUTPUT: Python list -
            [date(YYYY-MM-DD), time(HH:MM:SS), home-team, away-team,
            Overtime bool, home-score, away-score]
    '''
    team_game_list.pop(14) #Remove notes
    team_game_list.pop(13) #Remove streak
    team_game_list.pop(12) #Remove team loss
    team_game_list.pop(11) #Remove team win
    team_game_list.pop(7) #Remove W/L indicator
    team_game_list.pop(3) #Remove spacing column
    team_game_list.pop(0) #Remove game count

    #We want home team followed by away. If @ symbol present
    #then second team is home, so we swap column values for
    #team names and scores.
    if team_game_list[3] == '@':
        temp = team_game_list[2]
        team_game_list[2] = team_game_list[4]
        team_game_list[4] = temp

        temp = team_game_list[6]
        team_game_list[6] = team_game_list[7]
        team_game_list[7] = temp
    team_game_list.pop(3) #Remove home/away indicator

    #Convert overtime indicator to true/false for each entity
    if team_game_list[4] == 'OT':
        team_game_list[4] = 'True'
    else:
        team_game_list[4] = 'False'

    #Convert game start time to SQL friendly format
    
    if team_game_list[1] != 'NULL':
        hour = int(team_game_list[1][0:-4])
        if team_game_list[1][-1] == 'p':
            hour += 12
        team_game_list[1] = str(hour) + team_game_list[1][-4:-1] + ':00'

    return team_game_list


def get_season_games (schedule_page):
    '''
    Uses individual team season page from basketball-reference to scrape data from each game that season.
    Data specific to that team is removed so that each game can be input to SQL database as it's own entity.
    PARAM:  URL- basketball-reference single team single season
    OUTPUT: Python list - ["date", "time", "home", "away", "overtime", "home_score", "away_score"]
    '''
    #fetch the desired page
    page = requests.get(schedule_page)
    #Create a beautifulSoup object
    soup = BeautifulSoup(page.text, 'html.parser')

    #Get team name for data formatting
    name_tag = soup.find(id='info')
    franchise_name = name_tag.contents[1].contents[3].contents[1].contents[3].string

    #Create a tag from desired table of data for each season game within HTML
    activeTableTag = soup.find(id='games')
    #Tag of tbody with desired rows of game data.

    if activeTableTag == None:
        return None
    
    activeBodyTag = activeTableTag.contents[6]

    game_log = []
    list_length = len(list(activeBodyTag)) #Get length so that we only iterate through every other using range
    for game in range(1, list_length, 2):
        game_tag = activeBodyTag.contents[game] #Get HTML tag for individual game in table
        game_stats = []
        if game_tag.has_attr('class') and game_tag['class'][0] == 'thead': #Not interested in thead rows
            continue
        else:
            game_date = game_tag.contents[1]['csk'] #tag attribute csk has date format better suited for SQL so grab it
            for child in game_tag:
                string = child.string #Grab tag string to insert into list
                if string == None: #Unplayed games for a current season return None and are converted to NULL for easy SQL input.
                    string = 'NULL'
                game_stats.append(string)
            #gameStats = formatGame(gameStats)
            if game_stats[9] == 'NULL':
                continue
            else:
                game_stats[1] = game_date #Replace undesired date format with previously grabbed desired format
                game_stats[4] = franchise_name #Replace blank column for current team page with name grabbed earlier
                game_stats = format_season_stats(game_stats) #Send to formatting function for changes not requiring infor from HTML
                game_log.append(game_stats)

    return game_log


#################################################
# Player-Game SQL table management
#################################################


def formatGame (gameList):
    #This turns home or away to a bool
    #We use the scraped @ symbol telling us player is away to identify false otherwise true
    if gameList[5] == '@':
        gameList[5] = 'False'
    else:
        gameList[5] = 'True'

    #>10 stats present only when a player was designated active.
    #In the case of active games we specify status and remove others that can be calculated as needed rather than stored
    if len(gameList) > 10:
        gameList.insert(0, 'active') #Insert status at front
        gameList.pop(9) #remove active game counter
        gameList.pop(-2) #remove GmSc stat
        gameList.pop(18) #remove FT%
        gameList.pop(15) #remove 3PT%
        gameList.pop(12) #remove FG%
    #In case of inactive or DNP
    else:
        status = gameList.pop(len(gameList) - 1) #remove status from back
        gameList.insert(0, status) #apply status to front
    
    gameList.pop(2) #Remove games active total column from all
    gameList.pop(7) #remove team score differential from all
    
    return(gameList)


def seasonStats (seasonPage): 
    #fetch the desired page
    page = requests.get(seasonPage)
    #print(page)

    #Create a beautifulSoup object
    soup = BeautifulSoup(page.text, 'html.parser')
    tableTag = soup.find(id='pgl_basic')

    #Identifies thead containing desired stat labels.
    tableHeadTag = tableTag.contents[4].contents[1]
    #Identifies tbody with desired rows of game data.
    tableBodyTag = tableTag.contents[6]

    columnTitles = []
    #Iterate to each th in tHead to print string of that stat title
    for child in tableHeadTag:
        string = child.string
        if '\n' not in string and '\xa0' not in string:
            columnTitles.append(string)
    #columnTitles.insert(0, "Total") #Add title to beginning for franchise total column
    #columnTitles.append("Current") #Add title to end for current franchise identifier
    #formatTeam(columnTitles) #Remove unnecessary column titles
    columnTitles.pop(26) #Remove GmSc
    columnTitles.pop(16) #Remove FT%
    columnTitles.pop(13) #Remove 3P%
    columnTitles.pop(10) #Remove FG%
    columnTitles.pop(6) #Remove team point differential
    columnTitles.insert(5, "Home") #Add title for home game bool
    columnTitles[0] = "Status" #Add title for player status
    for header in columnTitles:
        print("{}   ".format(header), end = "  ")
    print("")

    seasonStats = []
    #Print the game stats
    #Goes through each game in range of html table using len()
    for game in range(1, len(list(tableBodyTag)), 2):
        #Assign game to it's own tag
        gameTag = tableBodyTag.contents[game]
        gameStats = []

        #If that particular tr has class='thead' we don't want it.
        if gameTag.has_attr('class') and gameTag['class'][0] == 'thead':
            continue
        else:
            #For loop iterates through each td to print string value
            for child in gameTag:
                #print(child.string)
                gameStats.append(child.string)
            #print("\n\n")
            gameStats = formatGame(gameStats)
            seasonStats.append(gameStats)

    #for x in seasonStats:
    #    print(x)

    return(seasonStats)


def careerStats (playerPage):
    page = requests.get(playerPage)
    soup = BeautifulSoup(page.text, 'html.parser')
    tableTag = soup.find(id='all_per_game')
    careerStats = []
    for link in tableTag.find_all('a'):
        address = link.get('href')
        if "players" in address:
            #print("https://www.basketball-reference.com" + address)
            careerStats += seasonStats("https://www.basketball-reference.com" + address)

    #for season in careerStats:
    #   print(season)
    return(careerStats)


def allPlayerPages (sourceURL):
    page = requests.get(sourceURL)
    soup = BeautifulSoup(page.text, 'html.parser')
    tableTag = soup.find(id='content')

    alphaPagesList = []
    for link in tableTag.find_all('a'):
        address = link.get('href')
        if ".html" not in address and "players" in address:
            alphaPagesList.append("https://www.basketball-reference.com" + address)

    playerPagesList = []
    for address in alphaPagesList:
        page = requests.get(address)
        soup = BeautifulSoup(page.text, 'html.parser')
        tableTag = soup.find(id='div_players')
        for link in tableTag.find_all('a'):
            address = link.get('href')
            if "players" in address:
                playerPagesList.append("https://www.basketball-reference.com" + address)

    #for player in playerPagesList:
    #    print(player)
    #print(len(playerPagesList))
    return(playerPagesList)


# def allSeasonPages (URL_list):
#     for player in URL_list:

#list = allPlayerPages('https://www.basketball-reference.com/players/')
#for player in list:
#   print(player)

# list = seasonStats('https://www.basketball-reference.com/players/l/lillada01/gamelog/2019/')
# for game in list:
#    print(game)

# teamList = get_teams_list('https://www.basketball-reference.com/teams/')
# for team in teamList:
#     print(team)

#get_seasons_list('https://www.basketball-reference.com/teams/')
#get_season_games('https://www.basketball-reference.com/teams/ATL/2020_games.html')

# list = get_seasons_list('https://www.basketball-reference.com/teams/')
# for season in list:
#     print(season)