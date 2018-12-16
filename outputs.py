
# %%
import datetime as dt
import pandas as pd
from copy import deepcopy

import yahoo_fantasy_api.config as config
from yahoo_fantasy_api.utils.base_utils import BaseUtils

config.global_vars()
sport = config.sport
sport_year = config.sport_year
gameid = config.gameid
leagueid = config.leagueid
league_code = config.league_code
nba_year = config.league_code


def convert_date(date):
    return date.strftime('%Y-%m-%d')

def search_fantasy_week(b, date): 
    fantasy_weeks = b.load_json('yahoo_fantasy_api/data/' + league_code + '/fantasy_weeks.json')
    for w in fantasy_weeks:
        for d in w['dates']:
            if date == d:
                return w

def search_team_name(team_key, yahoo_teams):
    """search for team name from team_key
    team_key = yahoo team key
    yahoo_teams = yahoo_teams.json file"""
    for team in yahoo_teams:
        if team['team_key'] == team_key:
            return team['managers']['manager']['nickname']

def search_stat_name(stat_id, yahoo_settings):
    for sid in yahoo_settings['settings']['stat_categories']['stats']['stat']:
        if sid['stat_id'] == stat_id:
            return sid['display_name']

def assign_team_type(i, match, matchup_type):
    if matchup_type == 'real':
        team_type = 'Real Team'
    elif matchup_type == 'ta':
        if i == 0:
            team_type = 'Auto Draft team'
        elif i == 1:
            team_type = 'Real Team'
    elif matchup_type == 'ba':
        if i == 0:
            team_type = 'Real Team'
        elif i == 1:
            team_type = 'Auto Draft team'
    return team_type

def organize_matchup_data(matchup, matchup_type, yahoo_teams, yahoo_settings):
    #%%
    #matchup = real_winners[0]
    #matchup_type = 'real'

    organize_matchup = []
    for i, match in enumerate(matchup['teams']):
        m = {}    
        team_type = assign_team_type(i, match, matchup_type)
        team_name = search_team_name(match['team_key'], yahoo_teams)
        m = {
            'Week': matchup['week'],            
            'Type': team_type,            
            'Team': team_name
        }
        for stat in match['team_stats']['stats']['stat']:
            stat_display_name = search_stat_name(stat['stat_id'], yahoo_settings)
            m.update({stat_display_name: stat['value']})
        
        m.update({'Score': match['team_points']['total']})        

        organize_matchup.append(m)
    #organize_matchup
    #%%
    return organize_matchup

def get_header_values(any_matchup, yahoo_settings):      
    m = {
        'Week': 'Week',
        'Type': 'Type',
        'Team': 'Team'
    }
    for stat in any_matchup['teams'][0]['team_stats']['stats']['stat']:
        stat_display_name = search_stat_name(stat['stat_id'], yahoo_settings)
        m.update({stat_display_name: stat_display_name})
    m.update({'Score': 'Score'})        
    return m

def get_blank_values(any_matchup, yahoo_settings):    
    blank_value = ' '  
    m = {
        'Week': blank_value,
        'Type': blank_value,
        'Team': blank_value
    }
    for stat in any_matchup['teams'][0]['team_stats']['stats']['stat']:
        stat_display_name = search_stat_name(stat['stat_id'], yahoo_settings)
        m.update({stat_display_name: blank_value})
    m.update({'Score': blank_value})        
    return m


def get_auto_draft_output(b):
    auto_draft_output = []
    auto_draft_file = b.load_json('yahoo_fantasy_api/data/' + league_code + '/auto_draft.json')
    yahoo_teams = b.load_json('yahoo_fantasy_api/data/' + league_code + '/yahoo_teams.json')
    for p in auto_draft_file:
        team_key = league_code + '.t.' + p['TeamID']
        team_name = search_team_name(team_key, yahoo_teams)

        p_sub ={
            "YahooXRank": int(p['YahooXRank']),
            "Pick": int(p['Pick']),
            "Round": int(p['Round']),
            "Player": p['Player'],
            "Team": team_name
        }
        auto_draft_output.append(p_sub)

    def sort_key(d):
        return d['Team']

    return sorted(auto_draft_output, key=sort_key, reverse=False)


def get_team_records(b):
    yahoo_teams = b.load_json('yahoo_fantasy_api/data/' + league_code + '/yahoo_teams.json')
    all_matchups = b.load_json('yahoo_fantasy_api/data/' + league_code + '/outputs/all_matchups.json')

    today = dt.datetime.today()
    date = b.convert_date(today)
    week = search_fantasy_week(b, date)['week']

    #teams = ['phillip']
    team_types = ['Real Team', 'Auto Draft team'] # ['Real Team', 'Auto Draft team']
    team_records = []
    total_wlt = (int(week) - 1) * 9
    for team_info in yahoo_teams:    
        team = search_team_name(team_info['team_key'], yahoo_teams)
        for team_type in team_types:
            real_wins = 0
            real_losses = 0        
            ad_wins = 0
            ad_losses = 0                
            for index, entry in enumerate(all_matchups):
                if (entry['Week'] != str(week)):
                    if (entry['Team'] == team):
                        if all_matchups[index-1]['Team'] != ' ' and all_matchups[index-1]['Team'] != 'Team':                
                            if entry['Type'] == 'Real Team' and all_matchups[index-1]['Type'] == 'Real Team':
                                #print(all_matchups[index-1])
                                #print(entry)
                                real_wins = real_wins + int(entry['Score'])
                                real_losses = real_losses + int(all_matchups[index-1]['Score'])
                            elif entry['Type'] == 'Auto Draft team' and all_matchups[index-1]['Type'] == 'Real Team':
                                #print(all_matchups[index-1])
                                #print(entry)
                                ad_wins = ad_wins + int(entry['Score'])
                                ad_losses = ad_losses + int(all_matchups[index-1]['Score'])
                        elif all_matchups[index+1]['Team'] != ' ' and all_matchups[index+1]['Team'] != 'Team':           
                            if entry['Type'] == 'Real Team' and all_matchups[index+1]['Type'] == 'Real Team':
                                #print(entry)
                                #print(all_matchups[index+1])
                                real_wins = real_wins + int(entry['Score'])
                                real_losses = real_losses + int(all_matchups[index+1]['Score'])
                            elif entry['Type'] == 'Auto Draft team' and all_matchups[index+1]['Type'] == 'Real Team':
                                #print(all_matchups[index+1])
                                #print(entry)
                                ad_wins = ad_wins + int(entry['Score'])
                                ad_losses = ad_losses + int(all_matchups[index+1]['Score'])                            
        real_ties = total_wlt - (real_wins + real_losses)
        ad_ties = total_wlt - (ad_wins + ad_losses)
        real_pct = (real_wins + (real_ties * 0.5)) / total_wlt
        ad_pct = (ad_wins + (ad_ties * 0.5)) / total_wlt
        record ={
            "Team": team,
            #"Type": team_type,
            "Real W-L-T": str(real_wins) + '-' + str(real_losses) + '-' + str(real_ties),
            "Real Pct": '%.3f' % real_pct,
            "Auto Draft W-L-T": str(ad_wins) + '-' + str(ad_losses) + '-' + str(ad_ties),
            "Auto Draft Pct": '%.3f' % ad_pct
        }
        team_records.append(record)

    def sort_key(d):
        return d['Real Pct']

    return sorted(team_records, key=sort_key, reverse=True)
