from requests import get
import json
import csv
import re


#%% BaseUtils
class BaseUtils():
    """A class for getting player information"""

    def __init__(self, nba_year):
        """Initialize name and age attributes."""
        self.nba_year = nba_year
    
    def get_json (self, uri):
        """get a uri and converts to json"""
        self.uri = uri
        resp = get(uri)
        resp_json = json.loads(resp.text)
        return resp_json
    
    def load_json (self, json_file):
        self.json_file = json_file
        with open(json_file) as f:
            json_object = json.load(f)
        return json_object

    def create_json (self, json_data, output_file):
        self.output_file = output_file
        self.json_data = json_data
        with open(output_file, 'w') as f:
            json.dump(json_data, f)

    def convert_csv_json(self, csv_file, json_file):
        self.csv_file = csv_file
        self.json_file = json_file

        with open(csv_file) as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        with open(json_file, 'w') as f:
            json.dump(rows, f)

    def convert_json_data_csv(self, json_data, csv_file):        
        self.json_data = json_data
        self.csv_file = csv_file
        list_data = self.json_data
        output_file = self.csv_file
        with open(output_file, 'w', encoding='utf-8-sig', newline='') as csvfile:
            wr = csv.DictWriter(csvfile, delimiter=',', fieldnames=list(list_data[0]))
            wr.writeheader()
            for row in list_data:
                #print(row)
                wr.writerow(row)

    def convert_date(self, date):
        self.date = date
        return self.date.strftime('%Y-%m-%d')

    def names_match (self, first_name, last_name, full_name):
        """takes names, removes spaces, removes non alphanumeric characters, 
        and changes to lower case. Then matches first and last names to full name
        """
        self.first_name = first_name
        self.last_name = last_name
        self.full_name = full_name
        f_name = self.first_name
        l_name = self.last_name
        player_name = self.full_name

        first_name_strip = ''.join(e for e in f_name.lower() if e.isalnum())
        last_name_strip = ''.join(e for e in l_name.lower() if e.isalnum())
        player_strip = ''.join(e for e in player_name.lower() if e.isalnum())    
        if re.findall(first_name_strip, player_strip) and re.findall(last_name_strip, player_strip):
            return True
        else:
            return False            