# %%
import json
import xmltodict
import time
import datetime as dt
import pandas as pd
from copy import deepcopy
from requests import get
from fractions import Fraction
from yahoo_oauth import OAuth2

import yahoo_fantasy_api.config as config
from yahoo_fantasy_api.utils.yahoo_utils import YahooUtils

config.global_vars()
sport = config.sport
sport_year = config.sport_year
gameid = config.gameid
leagueid = config.leagueid
league_code = config.league_code
nba_year = config.league_code

def convert_date(date):
    return date.strftime('%Y-%m-%d')


# scoreboard real teams
def get_scoreboard(y, league_code, week):
    uri = 'https://fantasysports.yahooapis.com/fantasy/v2/league/' + league_code + '/scoreboard;week=' + str(week)
    scoreboard = y.get_y_json(uri)['fantasy_content']['league']['scoreboard']['matchups']['matchup']
    
    scoreboard_subset = []
    for s in scoreboard:
        if s.get('winner_team_key'):
            winner_team_key = s['winner_team_key']
        else:
            winner_team_key = 'current'
        match = {
            'week': s['week'],
            'week_start': s['week_start'],
            'week_end': s['week_end'],
            'status': s['status'],
            'winner_team_key': winner_team_key,
            'stat_winners': s['stat_winners'],
            'teams': s['teams']['team']
        }
        scoreboard_subset.append(match)
    return scoreboard_subset

# get stats by week, export to csv. works for real and auto
def search_fantasy_week(y, date): 
    fantasy_weeks = y.load_json('yahoo_fantasy_api/data/' + league_code + '/fantasy_weeks.json')
    for w in fantasy_weeks:
        for d in w['dates']:
            if date == d:
                return w

def search_fantasy_days(y, week):     
    fantasy_weeks = y.load_json('yahoo_fantasy_api/data/' + league_code + '/fantasy_weeks.json')
    for w in fantasy_weeks:
        if w['week'] == week:
            return w

def get_daily_stats(y, date, team_type):
    week_dates = search_fantasy_week(y, date)['dates']
    week_dates = week_dates[0:week_dates.index(date)+1]
    collection = []
    #week_dates = ['2017-10-23'] #FOR TESTING ONLY
    for d in week_dates:
        json_file = 'yahoo_fantasy_api/data/' + league_code + '/daily/' + d + '_' + team_type + '.json' # week2_winners_subset.json
        daily_stats = y.load_json(json_file)
        for ds in daily_stats:
            team_key = ds['team']['team_key']
            for ps_data in ds['stats']:
                player_key = ps_data['player_key']
                ascii_full = ps_data['ascii_full']
                date = ps_data['player_stats']['date']
                ps = ps_data['player_stats']['stats']['stat']

                num0, denom0 = ps[0]['value'].split('/')
                num2, denom2 = ps[2]['value'].split('/')

                if ps[5]['value'] == '-' or ps[5]['value'] == '-/-':
                    active = 'no'
                else:
                    active = 'yes'                    

                row = {
                    'team_key': team_key,
                    'player_key': player_key,
                    'ascii_full': ascii_full,
                    'date': date,
                    #'sid_' + ps[0]['stat_id']: num0 + '_' + denom0,
                    'sid_' + ps[0]['stat_id']: ps[0]['value'],
                    'sid_' + ps[1]['stat_id']: ps[1]['value'],
                    #'sid_' + ps[2]['stat_id']: num2 + '_' + denom2,
                    'sid_' + ps[2]['stat_id']: ps[2]['value'],
                    'sid_' + ps[3]['stat_id']: ps[3]['value'],
                    'sid_' + ps[4]['stat_id']: ps[4]['value'],
                    'sid_' + ps[5]['stat_id']: ps[5]['value'],
                    'sid_' + ps[6]['stat_id']: ps[6]['value'],
                    'sid_' + ps[7]['stat_id']: ps[7]['value'],
                    'sid_' + ps[8]['stat_id']: ps[8]['value'],
                    'sid_' + ps[9]['stat_id']: ps[9]['value'],
                    'sid_' + ps[10]['stat_id']: ps[10]['value'],
                    'active': active
                }
                collection.append(row)    
    return collection

# get weekly stats by team key and df
def get_weekly_team_stats(team_df):
    team_df = team_df.loc[team_df['active'] == 'yes']
    stat = []
    for column in team_df:
        if column.startswith("sid"):
            sid = column.split('_')[1]
            if (sid == '9004003' or sid == '5' or sid == '9007006' or sid == '8'):  # check if fraction          
                if (sid == '9004003' or sid == '9007006'):
                    num = team_df[column].str.split('/').str[0]
                    denom = team_df[column].str.split('/').str[1]
                    sum_num = int(pd.to_numeric(num, errors='coerce').sum())
                    sum_denom = int(pd.to_numeric(denom, errors='coerce').sum())
                    if sum_denom is not 0:
                        sum_sid = round(sum_num/sum_denom, 4)
                    s = {
                        "stat_id": sid,
                        "value": str(sum_num) + "/" + str(sum_denom)
                    }
                    stat.append(s)
                    if sid == '9004003':
                        stat_id = "5"
                    elif sid == '9007006':
                        stat_id = "8"
                    s = {
                        "stat_id": stat_id,
                        "value": str(sum_sid)
                    }        
                    stat.append(s)
            else:    
                sum_sid = pd.to_numeric(team_df[column], errors='coerce').sum()  #  sum a column/sid
                s = {
                    "stat_id": sid,
                    "value": str(sum_sid)
                }        
                stat.append(s)
    return stat

def get_matchups(y, week):
    matchups_file = y.load_json('yahoo_fantasy_api/data/' + league_code + '/weekly/week' + str(week) + '_real_winners.json')
    matchups_subset = []
    for m in matchups_file:
        matches = {
            'week': m['week'],
            'teams': [
                {
                    'team_key': m['teams'][0]['team_key'],
                    'team_stats': m['teams'][0]['team_stats'],
                    'team_points': m['teams'][0]['team_points'],
                },
                {
                    'team_key': m['teams'][1]['team_key'],
                    'team_stats': m['teams'][1]['team_stats'],
                    'team_points': m['teams'][1]['team_points'],
                }
            ]
        }
        matchups_subset.append(matches)
    return matchups_subset

def get_auto_matchup(matchups, week, df):
    for i, m in enumerate(matchups[:]):
        for k, t in enumerate(m['teams']):
            team_key = t['team_key'] # '375.l.60103.t.1'
            team_df = df.loc[df['team_key'] == team_key] # get rows by team key
            weekly_team_stats = get_weekly_team_stats(team_df)
            matchups[i]['teams'][k]['team_stats']['stats']['stat'] = weekly_team_stats
    return matchups


def maximum(top, bottom):        
    top_value = top['value']
    bottom_value = bottom['value']
    try:
        top_num = int(top_value)
    except:
        try:
            top_num = float(top_value)
        except:                 
            top_num = 0

    try:
        bottom_num = int(bottom_value)
    except:
        try:
            bottom_num = float(bottom_value)
        except:
            bottom_num = 0

    if top_num == bottom_num:
        return 'tied'
    elif top_num > bottom_num:    
        return 'top'
    else:
        return 'bottom'

def sort_key(d):
    return int(d['stat_id'])

def get_real_auto_winners(rva_scoreboard):
    real_auto_scoreboard = deepcopy(rva_scoreboard)
    #real_auto_scoreboard = top_auto_scoreboard
    for h, match in enumerate(real_auto_scoreboard):
        rva_scoreboard[h]['stat_winners'] = { 'stat_winner': [] }
        top_team = match['teams'][0]
        bottom_team = match['teams'][1]
        top_team['team_stats']['stats']['stat'] = sorted(top_team['team_stats']['stats']['stat'], key=sort_key, reverse=False)
        bottom_team['team_stats']['stats']['stat'] = sorted(bottom_team['team_stats']['stats']['stat'], key=sort_key, reverse=False)
        
        #calculate greater value of sids
        stat_winner = []
        for i, sid in enumerate(top_team['team_stats']['stats']['stat']):
            if (sid['stat_id'] != '9004003' and sid['stat_id'] != '9007006'):
                winner = maximum(top_team['team_stats']['stats']['stat'][i], bottom_team['team_stats']['stats']['stat'][i])
                if winner == 'tied':
                    winner_key = "is_tied"
                    winner_team_key = "1"
                elif winner == 'top':
                    winner_key = "winner_team_key"
                    winner_team_key = top_team['team_key']
                else:
                    winner_key = "winner_team_key"
                    winner_team_key = bottom_team['team_key']
                winner = {
                    "stat_id": top_team['team_stats']['stats']['stat'][i]['stat_id'],
                    winner_key: winner_team_key
                }
                stat_winner.append(winner)
        rva_scoreboard[h]['stat_winners']['stat_winner'] = stat_winner
    return rva_scoreboard

def add_winner_team_key(rva_scoreboard):
    rva_scoreboard_winner = deepcopy(rva_scoreboard)
    for w in rva_scoreboard_winner:
        t_team_key = w['teams'][0]['team_key']
        b_team_key = w['teams'][1]['team_key']
        t_score = 0
        b_score = 0
        for sid in w['stat_winners']['stat_winner']:
            if "is_tied" in sid:
                pass
            elif sid['winner_team_key'] == t_team_key:
                t_score += 1        
            elif sid['winner_team_key'] == b_team_key:
                b_score += 1                    
        
        # assign team points
        w['teams'][0]['team_points']['total'] = t_score
        w['teams'][1]['team_points']['total'] = b_score

        # assign winner team key
        if t_score == b_score:
            w['winner_team_key'] = 'tied'
        elif t_score > b_score:
            w['winner_team_key'] = t_team_key
        else:
            w['winner_team_key'] = b_team_key
        
    return rva_scoreboard_winner
 
# check number of active players on dataframe
def check_active_players(y, df, date):
    active_slots = 10
    team_keys = y.get_team_keys_list()
    week_dates = search_fantasy_week(y, date)['dates']
    week_dates = week_dates[0:week_dates.index(date)+1]

    for day in week_dates:
        for team_key in team_keys:
            team_df_day = df.loc[(df['team_key'] == team_key) & (df['date'] == day)]    
            active_players = team_df_day.loc[(team_df_day['active'] == 'yes')]    
            active_player_count = active_players.count()['active']
            if active_player_count > active_slots:
                remove_count = active_player_count - active_slots
                remove_list = active_players.tail(remove_count)['player_key'].tolist()
                for player_key in remove_list:
                    df.loc[(df['team_key'] == team_key) & (df['date'] == day) & (df['player_key'] == player_key), 'active'] = 'no'
    return df            
