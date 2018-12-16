#%%
import config
from requests import get
import datetime as dt
import json, os
from yahoo_oauth import OAuth2

from yahoo_fantasy_api.utils.player_utils import PlayerUtils
from yahoo_fantasy_api.utils.draft_utils import DraftUtils
from yahoo_fantasy_api.utils.yahoo_utils import YahooUtils


config.global_vars()
sport = config.sport
sport_year = config.sport_year
gameid = config.gameid
leagueid = config.leagueid
league_code = config.league_code
nba_year = config.league_code
season_start_date = config.season_start_date


y_session = config.yahoo_session()
y = YahooUtils(y_session, sport, sport_year, gameid, leagueid)

p = PlayerUtils(nba_year)
d = DraftUtils(nba_year)
os.makedirs('yahoo_fantasy_api/data/' + nba_year + '/raw', exist_ok=True)
os.makedirs('yahoo_fantasy_api/data/' + nba_year + '/logs', exist_ok=True)
os.makedirs('yahoo_fantasy_api/data/' + nba_year + '/daily', exist_ok=True)
os.makedirs('yahoo_fantasy_api/data/' + nba_year + '/weekly', exist_ok=True)
os.makedirs('yahoo_fantasy_api/data/' + nba_year + '/outputs', exist_ok=True)

# get yahoo xranks and create summary xrank - might have to download manually
uri = 'https://pub-api.fantasysports.yahoo.com/fantasy/v3/players/nba/' + str(leagueid) + '?format=rawjson'
resp = get(uri)
resp_json = json.loads(resp.text)
y.create_json(resp_json, 'yahoo_fantasy_api/data/' + nba_year + '/raw/yahoo_rank.json')
json_file = 'yahoo_fantasy_api/data/' + nba_year + '/raw/yahoo_rank.json'
d.create_xrank(json_file)
#d.create_xrank_simple_csv(json_file) #used for draft day only

# get real draft results
draft_result = y.get_draft_results() # get yahoo api json
y.create_json(draft_result, 'yahoo_fantasy_api/data/' + nba_year + '/raw/draft_result.json') #write to file
draft_result = y.load_json('yahoo_fantasy_api/data/' + nba_year + '/raw/draft_result.json')
    
# create summary draft
xrank = d.load_json('yahoo_fantasy_api/data/' + nba_year + '/yahoo_xrank.json') #run once
summary_draft = y.get_summary_draft(xrank)
y.create_json(summary_draft, 'yahoo_fantasy_api/data/' + nba_year + '/summary_draft.json') #write to file

# create full draft
full_draft_json = d.create_full_draft_teams_json(xrank, summary_draft) #run once
draft = d.load_json('yahoo_fantasy_api/data/' + nba_year + '/full_draft.json') #full_draft_json = 'yahoo_fantasy_api/data/2018/full_draft.json'

# create auto draft
auto_draft_json = d.create_auto_draft_teams_json(xrank, draft) #run once to create json
auto_draft = d.load_json('yahoo_fantasy_api/data/' + nba_year + '/auto_draft.json') #auto_draft_json = 'yahoo_fantasy_api/data/2018/auto_draft.json'

# create auto_draft_roster.json
auto_draft_roster = y.create_y_auto_draft_roster_file(auto_draft)
y.create_json(auto_draft_roster, 'yahoo_fantasy_api/data/' + nba_year + '/auto_draft_roster.json') #write to file

# create fantasy_weeks.json
#season_start_date = '2017-10-16' #2017
dt_date = dt.datetime.strptime(season_start_date, '%Y-%m-%d').date()
weeks = y.get_fantasy_weeks(dt_date)
y.create_json(weeks, 'yahoo_fantasy_api/data/' + nba_year + '/fantasy_weeks.json') #write to file

# create list of teams file
yahoo_teams = y.get_list_of_teams_json()
y.create_json(yahoo_teams, 'yahoo_fantasy_api/data/' + league_code + '/yahoo_teams.json') #write to file

# create league settings file for stat id to name mapping
yahoo_settings = y.get_league_settings()
y.create_json(yahoo_settings, 'yahoo_fantasy_api/data/' + league_code + '/yahoo_settings.json') #write to file

#TO DO get yahoo xrank using API
#https://developer.yahoo.com/fantasysports/guide/players-collection.html
#uri = 'https://fantasysports.yahooapis.com/fantasy/v2/league/' + str(league_code) + '/players;sort=OR'
#y.get_y_json(uri)['fantasy_content']['league']['players']
