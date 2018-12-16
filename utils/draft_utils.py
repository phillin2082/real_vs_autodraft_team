from requests import get
import json, re
from yahoo_fantasy_api.utils.base_utils import BaseUtils

# TO DO create draft results json
#uri = 'https://fantasysports.yahooapis.com/fantasy/v2/league/' + league_code + '/draftresults'

#class DraftUtils():
class DraftUtils(BaseUtils):
    """A class for getting player information"""
    def __init__(self, nba_year):
        """Initialize"""
        super().__init__(nba_year)
        self.nba_year = nba_year

    def create_xrank(self, json_file):
        """Creates a file yahoo_xrank.json" which is a subset of information
        provided by yahoo rankings. Download the json locally during draft
        time
        Run once per season
        uri = 'https://pub-api.fantasysports.yahoo.com/fantasy/v3/players/nba/2203249?format=rawjson'
        """        
        self.json_file = json_file
        with open(json_file) as f:
            yahoo_rank = json.load(f)
        xrank_unsorted = []
        for player in yahoo_rank['service']['player_list']:
            rank = {
                'firstname': player['fname'],
                'lastname': player['lname'],
                'xrank': player['o_rank'],
                'fantasy_pos': player['pos'],
                'display_pos': player['display_pos'],
                'primary_pos': player['primary_pos'],
                "y_id": player['id'],
                "y_player_key": player['player_key']
            }
            if rank['xrank'] != 0:
                xrank_unsorted.append(rank)

        def sort_key(xrank_unsorted):      
            return xrank_unsorted['xrank']       
        xrank_simple = sorted(xrank_unsorted, key=sort_key, reverse=False)

        output_file = 'yahoo_fantasy_api/data/' + self.nba_year + '/yahoo_xrank.json'
        with open(output_file, 'w') as f:
            json.dump(xrank_simple, f)        
        return output_file

    def create_xrank_simple_csv(self, json_file):
        """used for draft day
        """        
        self.json_file = json_file
        with open(json_file) as f:
            yahoo_rank = json.load(f)
        xrank_unsorted = []
        for player in yahoo_rank['service']['player_list']:
            rank = {
                'R#': player['o_rank'],                
                'PLAYER': player['fname'] + ' ' + player['lname'],
            }
            if rank['R#'] != 0:
                xrank_unsorted.append(rank)

        def sort_key(xrank_unsorted):      
            return xrank_unsorted['R#']       
        xrank_simple = sorted(xrank_unsorted, key=sort_key, reverse=False)

        output_file = 'yahoo_fantasy_api/data/' + self.nba_year + '/yahoo_xrank_simple.csv'
        self.convert_json_data_csv(xrank_simple, output_file)

        return output_file

    def create_full_draft_teams_json(self, xrank, draft_temp):
        self.draft_temp = draft_temp
        self.xrank = xrank
        draft = draft_temp
        full_draft = []
        for pick in draft:
            yahoo_xrank = None
            first_name = None
            last_name = None
            fantasy_pos = []
            primary_pos = None 
            for rank in self.xrank:
                if self.names_match(rank['firstname'], rank['lastname'], pick['Player']):
                    yahoo_xrank = rank['xrank']
                    first_name = rank['firstname']
                    last_name = rank['lastname']
                    fantasy_pos = rank['fantasy_pos']
                    primary_pos = rank['primary_pos']
                    y_player_id = rank['y_id']
                    y_player_key = rank['y_player_key']

            player_info = {
                'YahooXRank': yahoo_xrank,
                'Pick': pick['Pick'],        
                'Round': pick['Round'],
                #'RoundPick': pick['RoundPick'],
                'Player': pick['Player'],
                'FirstName': first_name,
                'LastName': last_name,
                'YahooPlayerID': y_player_id,
                'YahooPlayerKey': y_player_key,
                'FantasyPos': fantasy_pos,
                'PrimaryPos': primary_pos,
                'Nickname': pick['Nickname'],
                'TeamID': pick['TeamID']
            }
            full_draft.append(player_info)
            output_file = 'yahoo_fantasy_api/data/' + self.nba_year + '/full_draft.json'

        with open(output_file, 'w') as f:
            json.dump(full_draft, f)        
        return output_file            

    def create_auto_draft_teams_json(self, xrank, draft):
        """Creates file auto_draft.json file. Auto draft is the top xrank available"""
        self.xrank = xrank
        self.draft = draft
        available = self.xrank.copy()
        auto_draft = []

        for draft_index, pick in enumerate(self.draft):
            top_pick = 0          
            #LEFT OFF HERE
            for auto_pick in auto_draft:        
                if available[top_pick]['y_player_key'] == auto_pick['YahooPlayerKey'] and pick['TeamID'] == auto_pick['TeamID']:
                    top_pick = top_pick + 1

            first_name = available[top_pick]['firstname']
            last_name = available[top_pick]['lastname']                    
            top_available_player = available[top_pick]['firstname'] + ' ' + available[top_pick]['lastname']
            
            auto_pick_player = {
                'YahooXRank': available[top_pick]['xrank'],
                'Pick': pick['Pick'],
                'Round': pick['Round'],
                #'RoundPick': pick['RoundPick'],
                'Player': top_available_player,
                'FirstName': first_name,
                'LastName': last_name,     
                'YahooPlayerID': available[top_pick]['y_id'],
                'YahooPlayerKey': available[top_pick]['y_player_key'],
                'FantasyPos': available[top_pick]['fantasy_pos'],
                'PrimaryPos': available[top_pick]['primary_pos'],
                'Nickname': pick['Nickname'],
                'TeamID': pick['TeamID']
            }
            auto_draft.append(auto_pick_player)            
            for available_index, rank in enumerate(available[:]):
                #p_player = pick['Player']
                #first_name_strip = ''.join(e for e in rank['firstname'].lower() if e.isalnum())
                #last_name_strip = ''.join(e for e in rank['lastname'].lower() if e.isalnum())
                #player_strip = ''.join(e for e in p_player.lower() if e.isalnum())

                if rank['y_player_key'] == pick['YahooPlayerKey']:
                    available.remove(rank)
                #if re.findall(first_name_strip, player_strip) and re.findall(last_name_strip, player_strip):
                #    available.remove(rank)

        output_file = 'yahoo_fantasy_api/data/' + self.nba_year + '/auto_draft.json'

        with open(output_file, 'w') as f:
            json.dump(auto_draft, f, ensure_ascii=False)        
        return output_file

    def get_required_positions(self, team_name, auto_draft):
        self.team_name = team_name
        self.auto_draft = auto_draft

        required_positions = ['PG', 'SG', 'G', 'SF', 'PF', 'F', 'C', 'C']
        auto_draft_team = []
        for player in self.auto_draft:
            if player['Nickname'] == self.team_name:
                auto_draft_team.append(player)

        for team_player in auto_draft_team:
            for pos in team_player['FantasyPos']:
                if pos in required_positions:
                    required_positions.remove(pos)        
                    #print(pos + team_player['Player'])
                    break
        return required_positions

    def create_draft_summary_json(self, json_data):
        self.json_data = json_data
        #draft = self.json_data
        pick_list = []
        for pick in self.json_data:
            pick_row = {   
                'Pick': pick['Pick'],
                'Round': pick['Round'],
                'Player': pick['Player'],
                'Team': pick['Nickname']
            }
            pick_list.append(pick_row)
        return pick_list

