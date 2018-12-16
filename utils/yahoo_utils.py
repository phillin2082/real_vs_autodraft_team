import json, re
import datetime as dt
import xmltodict
from time import sleep

from yahoo_fantasy_api.utils.base_utils import BaseUtils

class YahooUtils(BaseUtils):
    """A class for getting yahoo fantasy info"""
    def __init__(self, y_session, sport, sport_year, gameid=None, leagueid=None):
        """Initialize"""
        super().__init__(sport_year)
        self.y_session = y_session
        self.sport = sport
        self.sport_year = sport_year
        self.gameid = gameid
        self.leagueid = leagueid
        self.league_code = str(self.gameid) + '.l.' + str(self.leagueid)

    def get_y_json(self, uri):
        self.uri = uri
        response_xml = self.y_session.session.get(self.uri)
        response_json = xmltodict.parse(response_xml.content, dict_constructor=dict)
        
        with open('yahoo_fantasy_api/data/' + str(self.league_code) + '/logs/' + str(dt.datetime.today().day) + '_yahoo_resp.log', 'a+') as f:
            response_str = json.dumps(response_json)[0:300]
            f.write(response_str)

        return response_json

    def get_game_ids(self):
        uri = 'https://fantasysports.yahooapis.com/fantasy/v2/game/' + self.sport
        game_info = self.get_y_json(uri)['fantasy_content']['game']
        return game_info

    def get_all_game_ids(self):
        uri = 'https://fantasysports.yahooapis.com/fantasy/v2/games;game_codes=' + self.sport
        game_info = self.get_y_json(uri)['fantasy_content']['games']['game']
        return game_info

    def make_team_code(self, teamid):
        self.teamid = teamid
        return str(self.gameid) + '.l.' + str(self.leagueid) + '.t.' + str(self.teamid)        
 
    def get_league_settings(self):
        uri = 'https://fantasysports.yahooapis.com/fantasy/v2/league/' + self.league_code + '/settings'
        y_settings = self.get_y_json(uri)['fantasy_content']['league']
        return y_settings

    def get_list_of_teams_json(self):
        uri = 'https://fantasysports.yahooapis.com/fantasy/v2/league/' + self.league_code + '/teams'
        y_teams = self.get_y_json(uri)['fantasy_content']['league']['teams']['team']
        return y_teams

    def get_team_keys_list(self):
        team_keys = []
        for team in self.get_list_of_teams_json():
            team_keys.append(team['team_key'])
        return team_keys

    def get_stat_categories(self):
        uri = 'https://fantasysports.yahooapis.com/fantasy/v2/league/' + self.league_code + '/settings'
        stat_categories = self.get_y_json (uri)['fantasy_content']['league']['settings']['stat_categories']['stats']['stat']
        return stat_categories

    def get_team_rosters_json(self):
        uri = 'https://fantasysports.yahooapis.com/fantasy/v2/league/' + self.league_code + '/teams/roster/players'
        y_rosters = self.get_y_json(uri)['fantasy_content']['league']['teams']['team']
        return y_rosters
    
    def get_season_stats_json(self):
        uri = 'https://fantasysports.yahooapis.com/fantasy/v2/league/' + self.league_code + '/teams/roster/players/stats'
        y_season_stats = self.get_y_json(uri)['fantasy_content']['league']
        return y_season_stats

    def get_team_stats(self, date, team_key):
        self.date = date #'2018-01-23'
        self.team_key = team_key #'375.l.60103.t.12' #2017ffbb
        uri = 'https://fantasysports.yahooapis.com/fantasy/v2/teams;team_keys=' \
            + self.team_key + '/roster/players/stats;type=date;date=' + self.date
        y_team_stats = self.get_y_json(uri)['fantasy_content']['teams']['team']['roster']['players']['player']
        return y_team_stats

    def add_stats_names(self, y_daily_stats, stat_categories): #not used for now. use at end
        """TO DO"""
        self.y_daily_stats = y_daily_stats
        self.stat_categories = stat_categories
        #add stat name an display name to y_daily_stats
        for y_daily_stat in self.y_daily_stats:
            for stats in y_daily_stat['stats']:
                for s in stats['player_stats']['stats']['stat']:
                    for cat in stat_categories:
                        if s['stat_id'] == cat['stat_id']:          
                            s['display_name'] = cat['display_name']
                            s['name'] = cat['name']

    
    def search_y_team_data(self, team_id, y_teams):
        """Search for yahoo team data based on yahoo team id"""
        self.team_id = team_id
        self.y_teams = y_teams
        all_y_teams = self.y_teams
        for one_y_team in all_y_teams:
            if one_y_team['team_id'] == team_id:
                return one_y_team

    def search_y_player_data(self, y_player_key):    
        """Search for yahoo player data based on yahoo player key"""
        #y_player_key = '385.p.4563' #harden
        #y_player_key = '375.p.6014' #doncic
        #self.league_code = league_code
        self.y_player_key = y_player_key
        uri = 'https://fantasysports.yahooapis.com/fantasy/v2/league/' + self.league_code + '/players;player_keys=' + self.y_player_key        
        try:
            player_data = self.get_y_json(uri)['fantasy_content']['league']['players']['player']
            return player_data
        except Exception as e:
            pass

    def get_y_team_subset(self, y_team_data):
        """Get subset of yahoo team data"""
        self.y_team_data = y_team_data
        y_team = self.y_team_data
        y_team_subset = {
            'team_key': y_team['team_key'],
            'team_id': y_team['team_id'],
            'name': y_team['name'],
            'team_logos': y_team['team_logos'],
            'managers': y_team['managers']
        }
        return y_team_subset

    def get_y_stats_subset(self, date, auto_team_players):
        """Get subset of yahoo player data"""
        self.date = date
        self.auto_team_players = auto_team_players
        y_auto_team_players = self.auto_team_players
        all_player_keys = []
        for key in y_auto_team_players:
            all_player_keys.append(key['player_key'])
        all_player_keys_str = ','.join(all_player_keys)
        uri = 'https://fantasysports.yahooapis.com/fantasy/v2/league/' + self.league_code + '/players;player_keys=' \
            + all_player_keys_str + '/stats;type=date;date=' + self.date
        
        y_player_stats_subset = []

        try: 
            y_player_stats = self.get_y_json(uri)['fantasy_content']['league']['players']['player']
            for y_player_stat in y_player_stats:
                ascii_full = y_player_stat['name']['ascii_first'] + ' ' + y_player_stat['name']['ascii_last']
                y_stat = {
                    'player_key': y_player_stat['player_key'],
                    'player_id': y_player_stat['player_id'],
                    'ascii_full': ascii_full,
                    'player_stats': y_player_stat['player_stats']
                }
                y_player_stats_subset.append(y_stat)            
        except: 
            pass

        return y_player_stats_subset


    def create_y_auto_draft_roster_file(self, auto_draft):
        """ create auto draft roster organized by teams. Output in json,
        Input will be:
        league_code - league code
        auto_draft - auto draft pick order in json
        all_y_teams - league teams with yahoo's data in json   
        """
        self.auto_draft = auto_draft
        y_teams = self.get_list_of_teams_json()

        team_ids = []
        for y_team in y_teams:
            team_ids.append(str(y_team['team_id']))
        team_ids

        auto_teams = []
        for team_id in team_ids:
            auto_team_players = []    
            for pick in self.auto_draft:
                if pick['TeamID'] == team_id:
                    y_player_data = self.search_y_player_data(pick['YahooPlayerKey'])
                    #print(y_player_data)
                    if y_player_data is not None:
                        auto_team_players.append(y_player_data)          
            y_team_data = self.search_y_team_data(team_id, y_teams)
            y_team_subset = self.get_y_team_subset(y_team_data)
            #y_stats_subset = get_y_stats_subset(date, auto_team_players)
            auto_team = {
                'team': y_team_subset,
                #'stats': y_stats_subset
                'players': auto_team_players
            }
            auto_teams.append(auto_team)

        #output_file = 'yahoo_fantasy_api/data/' + self.nba_year + '/auto_draft_roster.json'
        #self.create_json(auto_teams, output_file)
        return auto_teams            

    def create_daily_auto_stats_file(self, date, auto_teams, team_type):
        """Get stats for auto draft teams for the day. Output is json file
        Input is:
        date - date
        auto_teams - team with rosters. Results from function get_y_auto_draft_roster
        """    
        self.date = date
        self.auto_teams = auto_teams
        self.team_type = team_type

        auto_team_stats = []
        for auto_team in self.auto_teams:
            y_stats_subset = self.get_y_stats_subset(self.date, auto_team['players'])
            auto_team_stat = {
                'team': auto_team['team'],
                'stats': y_stats_subset
            }    
            auto_team_stats.append(auto_team_stat)
        output_file = 'yahoo_fantasy_api/data/' + self.league_code + '/daily/' + self.date + '_' + self.team_type + '.json'
        with open(output_file, 'w') as f:
            json.dump(auto_team_stats, f)
        return output_file        

    def get_weekly_dates(self, dt_date):    
        self.dt_date = dt_date
        dates = []
        for y in range (0, 7):   
            dates.append(str(self.dt_date))
            self.dt_date += dt.timedelta(days=1)
        return dates, self.dt_date

    def get_fantasy_weeks(self, dt_date):
        self.dt_date = dt_date
        weeks = []
        for x in range(1, 25):
            weekly_dates, self.dt_date = self.get_weekly_dates(self.dt_date)
            week_data = {
                'week': x,
                'dates': weekly_dates
            }
            weeks.append(week_data)
        return weeks

    def get_draft_results(self):
        uri = 'https://fantasysports.yahooapis.com/fantasy/v2/league/' + self.league_code + '/draftresults'
        draft_result = self.get_y_json (uri)['fantasy_content']['league']['draft_results']['draft_result']
        return draft_result

    def get_summary_draft(self, xrank):
        self.xrank = xrank
        draft_result = self.get_draft_results()
        y_teams = self.get_list_of_teams_json()

        summary_draft = []       
        for dr in draft_result:
            for x in self.xrank:
                if x['y_player_key'] == dr['player_key']:
                    player_name = x['firstname'] + ' ' + x['lastname']
            for t in y_teams:
                if t['team_key'] == dr['team_key']:
                    team_name = t['name']
            draft_row = {
                'Player': player_name,
                'Pick': dr['pick'],
                'Round': dr['round'],
                'PlayerKey': dr['player_key'],
                'Nickname': team_name,
                'TeamKey': dr['team_key'],
                'TeamID': dr['team_key'].split('.')[-1]
            }
            summary_draft.append(draft_row)
        return summary_draft         