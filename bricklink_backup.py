import csv
import unicodedata
import re
import sys
import toml
import argparse
from json2xml import json2xml
from pathlib import Path
from datetime import datetime
from requests_oauthlib import OAuth1Session

class FileWriter:
    @staticmethod
    def slugify(value, allow_unicode=False):
        """
        Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
        dashes to single dashes. Remove characters that aren't alphanumerics,
        underscores, or hyphens. Convert to lowercase. Also strip leading and
        trailing whitespace, dashes, and underscores.
        """
        value = str(value)
        if allow_unicode:
            value = unicodedata.normalize("NFKC", value)
        else:
            value = (
                unicodedata.normalize("NFKD", value)
                .encode("ascii", "ignore")
                .decode("ascii")
            )
        value = re.sub(r"[^\w\s-]", "", value.lower())
        return re.sub(r"[-\s]+", "-", value).strip("-_")


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
    def json_to_csv(data, output_filename, path):
        """Takes a JSON (with possible nested dictionaries) and exports to a single CSV file."""
        print("Writing data into .csv file....")
        # As it's a changeable path, check and make directory if doesn't exist
        Path(path).mkdir(parents=True, exist_ok=True)

        output_filename = FileWriter.slugify(output_filename)
        # First, flatten the JSON data
        flat_data = [FileWriter.flatten_json(item) for item in data]

        # Writing to CSV
        keys = set().union(*(d.keys() for d in flat_data))
        with open(f"{path}/{output_filename}.csv", 'w', newline='', encoding="utf-8") as output_file:
            dict_writer = csv.DictWriter(output_file, keys)
            dict_writer.writeheader()
            dict_writer.writerows(flat_data)

    @staticmethod
    def json_to_xml(data, output_filename, path):
        """Takes a JSON (with possible nested dictionaries) and exports to a single CSV file."""
        print("Writing data into .xml file....")
        # As it's a changeable path, check and make directory if doesn't exist
        Path(path).mkdir(parents=True, exist_ok=True)

        output_filename = FileWriter.slugify(output_filename)
        #print(data)

        j2xml = json2xml.Json2xml(data, wrapper="sequence", pretty=True, attr_type=False).to_xml()
        j2xml.encode('utf-8')
        with open(f"{path}/{output_filename}.xml", 'w', encoding='utf-8', errors='replace') as f:
            f.write(j2xml)

class Config:
    def __init__(self, path):
        self.data = toml.load(path, _dict=dict)

class Bricklink:
    # OAuth Credentials
    def __init__(self, config):
        self.config = config.data
        self.setup_keys()
        self.auth_session()

    def setup_keys(self):
        """Setting up variables from config"""
        print("Importing API keys...")

        for item in self.config["API"].values():
            if item == "" or item == []:
                print("Missing configuration data!")
                sys.exit()

        # Better than constantly referencing the config var
        # Makes it easier to change naming etc in future.
        self.CONSUMER_KEY:str = self.config["API"]["CONSUMER_KEY"]
        self.CONSUMER_SECRET:str = self.config["API"]["CONSUMER_SECRET"]
        self.TOKEN_VALUE:str = self.config["API"]["TOKEN_VALUE"]
        self.TOKEN_SECRET:str = self.config["API"]["TOKEN_SECRET"]

    def auth_session(self):
        self.oauth = OAuth1Session(
            self.CONSUMER_KEY,
            client_secret=self.CONSUMER_SECRET,
            resource_owner_key=self.TOKEN_VALUE,
            resource_owner_secret=self.TOKEN_SECRET
        )

    def fetch_inventory(self):
        print("Getting data from the Bricklink API...")
        response = self.oauth.get(f'https://api.bricklink.com/api/store/v1/inventories')

        if response.status_code != 200:
            print(f"Error: {response.text}")
        
        response.encoding = 'utf-8'
        
        return response.json()['data']

    def save_all_inventories(self, file_type):
        data = self.fetch_inventory()
        filename = f"{datetime.now().strftime('%m-%d-%Y-%H-%M-%S')} - Bricklink Backup"

        if file_type.lower() == "csv":
            FileWriter.json_to_csv(data, filename, self.config['EXPORT']['PATH'])
        else:
            FileWriter.json_to_xml(data, filename, self.config['EXPORT']['PATH'])
        print('#' * 25)
        print("File saved!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A simple script to backup bricklink store inventories.",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-c", "--config", help="set custom config name.", default="config.toml")
    parser.add_argument("-f", "--file", help="set file type (xml or csv)", default="xml")
    args = vars(parser.parse_args())

    config = Config(args["config"])
    store = Bricklink(config)
    store.save_all_inventories(args["file"])
