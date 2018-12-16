import xmltodict
import datetime as dt
from yahoo_oauth import OAuth2

import yahoo_fantasy_api.config as config
from yahoo_fantasy_api.utils.yahoo_utils import YahooUtils


def get_all_y_teams_date(y, date, latest_y_teams):
    all_y_teams_date= []
    for y_team in latest_y_teams:
        team_key = y_team['team_key']
        uri = 'https://fantasysports.yahooapis.com/fantasy/v2/team/' + team_key + '/roster;type=date;date=' + date
        
        roster_by_date = y.get_y_json(uri)['fantasy_content']
        roster_by_date_subset = {
            'team': {
                'team_key': roster_by_date['team']['team_key'],
                'team_id': roster_by_date['team']['team_id'],
                'name': roster_by_date['team']['name'],
                'team_logos': roster_by_date['team']['team_logos'],
                'managers': roster_by_date['team']['managers'],
            },        
            'players': roster_by_date['team']['roster']['players']['player']
        }
        all_y_teams_date.append(roster_by_date_subset)
    return all_y_teams_date


def update_todays_stats(y, today, latest_y_teams, auto_teams):
    date = y.convert_date(today)
    all_y_teams_date = get_all_y_teams_date(y, date, latest_y_teams)
    y.create_daily_auto_stats_file(date, all_y_teams_date, "real")
    y.create_daily_auto_stats_file(date, auto_teams, "auto")
    return None

def update_previous_stats(y, today, days_ago, latest_y_teams, auto_teams):   
    previous_date = today + dt.timedelta(days=days_ago)
    for i in range((today - previous_date).days + 1):
        date = y.convert_date((previous_date + dt.timedelta(days=i)))
        all_y_teams_date = get_all_y_teams_date(y, date, latest_y_teams)
        y.create_daily_auto_stats_file(date, all_y_teams_date, "real")
        y.create_daily_auto_stats_file(date, auto_teams, "auto")

