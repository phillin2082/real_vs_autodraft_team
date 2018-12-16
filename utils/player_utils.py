from requests import get
import json
from yahoo_fantasy_api.utils.base_utils import BaseUtils

#%%
#class PlayerUtils():
class PlayerUtils(BaseUtils):
    """A class for getting player information"""
    def __init__(self, nba_year):
        """Initialize"""
        super().__init__(nba_year)
        self.nba_year = nba_year

    def get_game_ids (self, date):   
        """get game ids from a single day"""
        self.date = date
        uri = 'http://data.nba.net/10s/prod/v1/' + self.date + '/scoreboard.json'        
        scoreboard = self.get_json(uri)
        game_ids = []
        for game in scoreboard['games']:
            game_ids.append(game['gameId'])
        return game_ids

    def get_active_players(self, date, game_ids):
        self.date = date
        self.game_ids = game_ids
        active_players = []
        for game_id in game_ids:
            uri = 'http://data.nba.net/10s/prod/v1/' + date + '/' + game_id + '_boxscore.json'
            boxscore = self.get_json(uri)
            boxscore_players = boxscore['stats']['activePlayers']
            for boxscore_player in boxscore_players:
                active_players.append(boxscore_player)
        return active_players

    def create_player_ids (self, uri):
        """Creates a file players_ids.json" which is a subset of information
        provied by data.nba.net.
        Run once per season
        uri = 'http://data.nba.net/10s/prod/v1/2018/players.json'
        """
        self.uri = uri
        resp = get(self.uri)
        players = json.loads(resp.text)
        player_list=[]
        for player in players['league']['standard']:    
            player_entry = {
                'firstName': player['firstName'],
                'lastName': player['lastName'],
                'personId': player['personId']
            }
            player_list.append(player_entry)

        output_file = 'yahoo_fantasy_api/data/' + self.nba_year + '/player_ids.json'
        with open(output_file, 'w') as f:
            json.dump(player_list, f)
        return output_file            

    def create_players_stats_file(self, date, player_ids, active_players):
        self.date = date
        self.player_ids = player_ids
        self.active_players = active_players
        daily_player_stats = []       
        for active_player in active_players:
            first_name = ''
            last_name = ''            
            for player_id in self.player_ids:
                #print(player_id['firstName'])
                if player_id['personId'] == active_player['personId']:
                    first_name = player_id['firstName']
                    last_name = player_id['lastName']
            player_stats = {
                'player': first_name + ' ' + last_name,
                'person_id': active_player['personId'],
                'fg_percent': active_player['fgp'],
                'ft_percent': active_player['ftp'],
                'tp_made': active_player['tpm'],
                'points': active_player['points'],        
                'tot_reb': active_player['totReb'],
                'assists': active_player['assists'],
                'steals': active_player['steals'],
                'blocks': active_player['blocks'],
                'turnovers': active_player['turnovers'],        
            }
            daily_player_stats.append(player_stats)
            #print(player_stats)
        output_file = 'yahoo_fantasy_api/data/' + self.nba_year + '/daily/players_stats_' + self.date + '.json'
        self.create_json (daily_player_stats, output_file)
        return output_file
