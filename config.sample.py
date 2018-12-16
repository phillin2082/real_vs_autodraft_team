from yahoo_oauth import OAuth2

def global_vars(): 
    global sport, sport_year, gameid, leagueid, league_code, season_start_date
    sport = 'nba'
    sport_year = '2018'
    gameid = 385  # 385=nba,2018; 380=nfl,2018; 375=nba,2017
    leagueid = 132161 
    league_code = str(gameid) + '.l.' + str(leagueid)
    season_start_date = '2018-10-15'  # 2018

def yahoo_session():   
    oauth = OAuth2(None, None, from_file='yahoo_fantasy_api/oauth2.json')
    if not oauth.token_is_valid():
        oauth.refresh_access_token()
    return oauth

