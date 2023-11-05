import os
import csv
import json
import sys
import toml
import argparse
from pathlib import Path
from datetime import datetime
from requests_oauthlib import OAuth1Session

class FileWriter:
    @staticmethod
    def flatten_json(y):
        """Recursively flattens a nested JSON."""
        out = {}

        def flatten(x, name=''):
            if type(x) is dict:
                for a in x:
                    flatten(x[a], f"{name}{a}_")
            elif type(x) is list:
                for i, a in enumerate(x):
                    flatten(a, f"{name}{i}_")
            else:
                out[name[:-1]] = x

        flatten(y)
        return out

    @staticmethod
    def json_to_csv(data, output_filename):
        """Takes a JSON (with possible nested dictionaries) and exports to a single CSV file."""

        # First, flatten the JSON data
        flat_data = [FileWriter.flatten_json(item) for item in data]

        # Writing to CSV
        keys = set().union(*(d.keys() for d in flat_data))
        with open(output_filename, 'w', newline='') as output_file:
            dict_writer = csv.DictWriter(output_file, keys)
            dict_writer.writeheader()
            dict_writer.writerows(flat_data)


class Config:
    def __init__(self, path):
        if path is None:
            path = "config.toml"
        self.data = toml.load(path, _dict=dict)

class Bricklink:
    # OAuth Credentials
    def __init__(self, config):
        self.config:Config = config
        self.setup_keys()
        self.auth_session()

    def setup_keys(self):
        for item in self.config["API"].values():
            if item == "" or item == []:
                print("Missing configuration data!")
                sys.exit()

        self.CONSUMER_KEY:str = config["API"]["CONSUMER_KEY"]
        self.CONSUMER_SECRET:str = config["API"]["CONSUMER_SECRET"]
        self.TOKEN_VALUE:str = config["API"]["TOKEN_VALUE"]
        self.TOKEN_SECRET:str = config["API"]["TOKEN_SECRET"]
        self.INVENTORIES:list = self.config["API"]["INVENTORIES"]

    def auth_session(self):
        self.oauth = OAuth1Session(
            self.CONSUMER_KEY,
            client_secret=self.CONSUMER_SECRET,
            resource_owner_key=self.TOKEN_VALUE,
            resource_owner_secret=self.TOKEN_SECRET
        )

    def fetch_inventory(self, id):
        response = self.oauth.get(f'https://api.bricklink.com/api/store/v1/inventories/{id}')

        if response.status_code != 200:
            print(f"Error: {response.text}")
        
        return response.json()["data"]

    def save_all_inventories(self):
        if self.config["API"]["INVENTORIES"] == []:
            print("No inventories found!")

        for inv in self.config["API"]["INVENTORIES"]:
            data = self.fetch_inventory(inv)

            Path(self.config['EXPORT']['PATH']).mkdir(parents=True, exist_ok=True)
            filename = os.path.normpath(f"{self.config['EXPORT']['PATH']}/{datetime.now()} - ID {inv}.csv")

            FileWriter.json_to_csv(data, filename)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A simple script to backup bricklink store inventories.",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-c", "--config", help="set custom config name.")
    args = vars(parser.parse_args())

    config = Config(args["config"])
    store = Bricklink(config)
    store.save_all_inventories()
