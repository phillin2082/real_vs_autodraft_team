from celery import Celery
from celery.schedules import crontab
from yahoo_oauth import OAuth2

import yahoo_fantasy_api.config as config
from yahoo_fantasy_api.workers.celery_config import app
from yahoo_fantasy_api.workers.tasks import create_daily_files, update_previous_files, create_weekly_files, create_team_list_file, create_all_matchups_file, run_django_week_update, create_team_records_file
from yahoo_fantasy_api.utils.yahoo_utils import YahooUtils


config.global_vars()
sport = config.sport
sport_year = config.sport_year
gameid = config.gameid
leagueid = config.leagueid
league_code = config.league_code
nba_year = config.league_code

#https://crontab.guru
#crontab (m/h/d/dM/MY)

@app.on_after_configure.connect
def create_team_list_file_sch(sender, **kwargs):
    sender.add_periodic_task(
        crontab(minute='0', hour='1', day_of_week='*/1'),
        create_team_list_file.s(),
        name='update daily files every day')

@app.on_after_configure.connect
def update_todays_files(sender, **kwargs):
    sender.add_periodic_task(
        crontab(minute='*/10', hour='*', day_of_week='*'),
        create_daily_files.s(),
        name='update todays files every hour')

@app.on_after_configure.connect
def update_previous_files_sch(sender, **kwargs):
    sender.add_periodic_task(
        crontab(minute='0', hour='*/6', day_of_week='*'),
        update_previous_files.s(),
        name='update daily files every day')

@app.on_after_configure.connect
def create_weekly_files_sch(sender, **kwargs):
    sender.add_periodic_task(
        crontab(minute='*/10', hour='*', day_of_week='*'),
        create_weekly_files.s(),
        name='update this weeks weekly files every hour')

@app.on_after_configure.connect
def create_all_matchups_file_sch(sender, **kwargs):
    sender.add_periodic_task(
        crontab(minute='*/10', hour='*', day_of_week='*'),
        create_all_matchups_file.s(),
        name='create all matchups file')    

@app.on_after_configure.connect
def create_team_records_file_sch(sender, **kwargs):
    sender.add_periodic_task(
        crontab(minute='*/10', hour='*', day_of_week='*'),
        create_team_records_file.s(),
        name='create team records file')    

@app.on_after_configure.connect
def run_django_week_update_sch(sender, **kwargs):
    sender.add_periodic_task(
        crontab(minute='0', hour='*/4', day_of_week='*'),
        run_django_week_update.s(),
        name='run django updates')    

