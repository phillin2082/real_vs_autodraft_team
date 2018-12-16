
#%%
import requests
import xmltodict
import json
import pandas as pd
import datetime as dt
from copy import deepcopy
from os import listdir
from yahoo_oauth import OAuth2

import yahoo_fantasy_api.config as config
import yahoo_fantasy_api.dailys as dailys
import yahoo_fantasy_api.weeklys as weeklys
import yahoo_fantasy_api.outputs as outputs
import yahoo_fantasy_api.django_automation as da
from yahoo_fantasy_api.workers.celery_config import app
from yahoo_fantasy_api.utils.yahoo_utils import YahooUtils
from yahoo_fantasy_api.utils.base_utils import BaseUtils

config.global_vars()
sport = config.sport
sport_year = config.sport_year
gameid = config.gameid
leagueid = config.leagueid
league_code = config.league_code
nba_year = config.league_code


def get_dates_teams(y):
    today = dt.datetime.today()
    date = y.convert_date(today)
    latest_y_teams = y.get_list_of_teams_json()
    auto_teams = y.load_json('yahoo_fantasy_api/data/' + league_code + '/auto_draft_roster.json')
    return today, date, latest_y_teams, auto_teams


@app.task
def create_team_list_file():
    y_session = config.yahoo_session()
    y = YahooUtils(y_session, sport, sport_year, gameid, leagueid)
    yahoo_teams = y.get_list_of_teams_json()
    y.create_json(yahoo_teams, 'yahoo_fantasy_api/data/' + league_code + '/yahoo_teams.json') #write to file


@app.task
def create_daily_files():   
    try:
        y_session = config.yahoo_session()
        y = YahooUtils(y_session, sport, sport_year, gameid, leagueid)
        today, date, latest_y_teams, auto_teams = get_dates_teams(y)
        dailys.update_todays_stats(y, today, latest_y_teams, auto_teams)
    except:
        pass

@app.task
def update_previous_files():   
    try:
        days_ago = -15
        y_session = config.yahoo_session()
        y = YahooUtils(y_session, sport, sport_year, gameid, leagueid)
        today, date, latest_y_teams, auto_teams = get_dates_teams(y)
        dailys.update_previous_stats(y, today, days_ago, latest_y_teams, auto_teams)
    except:
        pass
 
@app.task
def create_weekly_files():
# %%    
    y_session = config.yahoo_session()
    y = YahooUtils(y_session, sport, sport_year, gameid, leagueid)
    today, date, latest_y_teams, auto_teams = get_dates_teams(y)
    yahoo_settings = y.load_json('yahoo_fantasy_api/data/' + league_code + '/yahoo_settings.json')
    yahoo_teams = y.load_json('yahoo_fantasy_api/data/' + league_code + '/yahoo_teams.json')

    #date = '2018-10-28'  # '2018-10-28', 2018-10-21  # use sunday dates to get previous week
    week = weeklys.search_fantasy_week(y, date)['week']  # 2, 1

    for i in reversed(range(1, week+1)):
        week = i  # week = 4    
        last_fantasy_day = weeklys.search_fantasy_days(y, week)['dates'][-1]

        if today > dt.datetime.strptime(last_fantasy_day, '%Y-%m-%d'):
            date = last_fantasy_day

        # get winners for real team, run this every day - to do: check for current and past
        scoreboard = weeklys.get_scoreboard(y, league_code, week)
        output_file = 'yahoo_fantasy_api/data/' + league_code + '/weekly/week' + str(week) + '_real_winners.json' # week2_winners_subset.json
        y.create_json(scoreboard, output_file)

        # get daily stats for auto draft team for the week, create to csv if needed
        team_type = 'auto'  # real works too but no need
        daily_stats = weeklys.get_daily_stats(y, date, team_type)
        df = pd.DataFrame(daily_stats)
        #df.to_csv('yahoo_fantasy_api/data/' + league_code + '/weekly/week' + str(week) + '_' + team_type + '_daily_stats_before_actives.csv', index=False, header=True)  # csv-file
        #df = pd.read_csv('yahoo_fantasy_api/data/' + league_code + '/weekly/week' + str(week) + '_' + team_type + '_daily_stats_before_actives.csv')
        df_actives = weeklys.check_active_players(y, df, date)
        col = ['active', 'ascii_full', 'date', 'player_key', 'sid_9004003', 'sid_5', 'sid_9007006',  'sid_8',  'sid_10', 'sid_12', 'sid_15', 'sid_16', 'sid_17', 'sid_18', 'sid_19', 'team_key']
        df_actives = df_actives[col]    
        #df_actives.to_csv('yahoo_fantasy_api/data/' + league_code + '/weekly/week' + str(week) + '_' + team_type + '_daily_stats.csv', index=False, header=True)  # csv-file

        # create weekly stat files in csv and json
        df_active_json = df_actives.to_dict(orient='records')
        weekly_stats = []
        for player in df_active_json:
            player_sub = {
                "Week": week,
                "Date": player['date'],        
                "Active": player['active'],                
                "Name": player['ascii_full'],
                "Team": outputs.search_team_name(player['team_key'], yahoo_teams)

            }
            for k,v in player.items():
                if k.startswith("sid_"):
                    stat_id = k.split("_")[1]
                    stat_name = outputs.search_stat_name(stat_id, yahoo_settings)
                    try:
                        player_sub.update({stat_name: int(v)})
                    except:
                        player_sub.update({stat_name: v}) 
            weekly_stats.append(player_sub)

        #create csv
        output_file = 'yahoo_fantasy_api/data/' + league_code + '/weekly/week' + str(week) + '_auto_daily_stats.csv'
        y.convert_json_data_csv(weekly_stats, output_file)
        #create json - for django
        output_file_json = 'yahoo_fantasy_api/data/' + league_code + '/outputs/week' + str(week) + '_auto_daily_stats.json'
        y.create_json(weekly_stats, output_file_json)

        matchups = weeklys.get_matchups(y, week)  # get subset of data from real matchups
        auto_scoreboard = weeklys.get_auto_matchup(matchups, week, df)  # from real matchups create auto team matchup

        top_auto_scoreboard = deepcopy(auto_scoreboard)  # copy only
        bottom_auto_scoreboard = deepcopy(auto_scoreboard)  # copy only

        # create scoreboard, auto team on top, real on bottom; auto team on bottom, real on top
        for i, team_auto in enumerate(auto_scoreboard[:]):
            top_auto_scoreboard[i]['teams'][1]['team_stats']['stats']['stat'] = scoreboard[i]['teams'][1]['team_stats']['stats']['stat']
            bottom_auto_scoreboard[i]['teams'][0]['team_stats']['stats']['stat'] = scoreboard[i]['teams'][0]['team_stats']['stats']['stat']

        t_auto_winners = weeklys.get_real_auto_winners(top_auto_scoreboard) # create stat winners dict
        b_auto_winners = weeklys.get_real_auto_winners(bottom_auto_scoreboard)

        t_auto_winners = weeklys.add_winner_team_key(t_auto_winners) # add winner team key
        b_auto_winners = weeklys.add_winner_team_key(b_auto_winners)

        output_file = 'yahoo_fantasy_api/data/' + league_code + '/weekly/week' + str(week) + '_top_auto_winners.json' # week2_winners_subset.json
        y.create_json(t_auto_winners, output_file)

        output_file = 'yahoo_fantasy_api/data/' + league_code + '/weekly/week' + str(week) + '_bottom_auto_winners.json' # week2_winners_subset.json
        y.create_json(b_auto_winners, output_file)

# %%
@app.task
def create_all_matchups_file():
    b = BaseUtils(league_code)
    yahoo_settings = b.load_json('yahoo_fantasy_api/data/' + league_code + '/yahoo_settings.json')
    yahoo_teams = b.load_json('yahoo_fantasy_api/data/' + league_code + '/yahoo_teams.json')

    today = dt.datetime.today()
    date = b.convert_date(today)
    week = outputs.search_fantasy_week(b, date)['week']

    match_output = []
    for i in reversed(range(1, week+1)):
        week = i

        real_winners = b.load_json('yahoo_fantasy_api/data/' + league_code + '/weekly/' + 'week' + str(week) + '_real_winners.json')
        top_auto_winners = b.load_json('yahoo_fantasy_api/data/' + league_code + '/weekly/' + 'week' + str(week) + '_top_auto_winners.json')
        bottom_auto_winners = b.load_json('yahoo_fantasy_api/data/' + league_code + '/weekly/' + 'week' + str(week) + '_bottom_auto_winners.json')

        header_values = outputs.get_header_values(real_winners[0], yahoo_settings)
        blank_values = outputs.get_blank_values(real_winners[0], yahoo_settings)

        for index, (r, ta, ba) in enumerate(zip(real_winners, top_auto_winners, bottom_auto_winners)):    
            #r_top, r_bottom = organize_matchup_data(r)
            #match_output.append(r_top)
            #match_output.append(r_bottom)
            r_all = outputs.organize_matchup_data(r, 'real', yahoo_teams, yahoo_settings)
            ta_all = outputs.organize_matchup_data(ta, 'ta', yahoo_teams, yahoo_settings)
            ba_all = outputs.organize_matchup_data(ba, 'ba', yahoo_teams, yahoo_settings)
            match_output.append(header_values)
            for  x in r_all:
                match_output.append(x)
            match_output.append(blank_values)        
            for  x in ta_all:
                match_output.append(x)
            match_output.append(blank_values)                
            for  x in ba_all:
                match_output.append(x)    
            match_output.append(blank_values)                                   
            
    with open('yahoo_fantasy_api/data/' + league_code + '/outputs/all_matchups.json', 'w') as f:
        json.dump(match_output, f)
    match_output_df = pd.DataFrame(match_output, columns=match_output[0].keys())
    match_output_df.to_csv('yahoo_fantasy_api/data/' + league_code + '/outputs/all_matchups.csv', index=False, header=True)  # csv-file

@app.task
def create_auto_draft_teams_file():
    b = BaseUtils(league_code)
    auto_draft_output = outputs.get_auto_draft_output(b)
    with open('yahoo_fantasy_api/data/' + league_code + '/outputs/auto_draft_teams.json', 'w') as f:
        json.dump(auto_draft_output, f)

@app.task
def create_all_auto_daily_stats():
    b = BaseUtils(league_code)
    all_stats = []
    weekly_dir = "yahoo_fantasy_api/data/" + league_code + "/outputs/"
    files = listdir(weekly_dir)
    for f in files:
        if f.endswith('auto_daily_stats.json'):
            json_file = (weekly_dir + f)
            json_object = b.load_json(json_file)
            for entry in json_object:
                all_stats.append(entry)

    output_file = 'yahoo_fantasy_api/data/' + league_code + '/outputs/all_auto_daily_stats.json'
    #b.convert_json_data_csv(all_stats, output_file)
    b.create_json(all_stats, output_file)

@app.task
def create_team_records_file():
    b = BaseUtils(league_code)
    team_records = outputs.get_team_records(b)
    with open('yahoo_fantasy_api/data/' + league_code + '/outputs/team_records.json', 'w') as f:
        json.dump(team_records, f)
    team_records_df = pd.DataFrame(team_records, columns=team_records[0].keys())
    team_records_df.to_csv('yahoo_fantasy_api/data/' + league_code + '/outputs/team_records.csv', index=False, header=True)  # csv-file        


@app.task
def run_django_week_update():
    da.update_urls_file()
    da.update_views_file()
    da.update_update_urls_file()
