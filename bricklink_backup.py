import csv
import unicodedata
import re
import sys
import toml
import argparse
import textwrap
from pathlib import Path
from datetime import datetime
from requests_oauthlib import OAuth1Session

class StringManipulation:
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
    def escape_xml(str_xml):
        ''' Random function I found that I am too lazy to change. '''
        if type(str_xml) != str:
            return str_xml
        str_xml = str_xml.replace("&", "&amp;")
        str_xml = str_xml.replace("<", "&lt;")
        str_xml = str_xml.replace(">", "&gt;")
        str_xml = str_xml.replace("\"", "&quot;")
        str_xml = str_xml.replace("'", "&apos;")
        return str_xml
    
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
    def json_to_xml(data, output_filename, path, categories):
        """Takes a JSON (with possible nested dictionaries) and exports to a single CSV file."""
        print("Writing data into a BrickStore .xml file....")
        # As it's a changeable path, check and make directory if doesn't exist
        Path(path).mkdir(parents=True, exist_ok=True)

        output_filename = StringManipulation.slugify(output_filename)

        items_xml = ""
        for item in data:
            for key in item.keys():
                item_type = type(item[key])
                if item_type == dict:
                    for sub_key in item[key]:
                        item[key][sub_key] = StringManipulation.escape_xml(item[key][sub_key])
                else:
                    item[key] = StringManipulation.escape_xml(item[key])

            items_xml += f"""
                <ITEM>
                    <ITEMID>{item["item"]['no']}</ITEMID>
                    <ITEMTYPEID>{item["item"]['type'][0]}</ITEMTYPEID>
                    <COLORID>{item["color_id"]}</COLORID>
                    <ITEMNAME>{item["item"]['name']}</ITEMNAME>
                    <ITEMTYPENAME>{item["item"]['type']}</ITEMTYPENAME>
                    <COLORNAME>{item['color_name']}</COLORNAME>
                    <CATEGORYID>{item["item"]['category_id']}</CATEGORYID>
                    <CATEGORYNAME>{item["item"]['category_name']}</CATEGORYNAME>
                    <STATUS>I</STATUS>
                    <BULK>{item['bulk']}</BULK>
                    <COST>{item['my_cost']}</COST>
                    <QTY>{item['quantity']}</QTY>
                    <PRICE>{item['unit_price']}</PRICE>
                    <CONDITION>{item['new_or_used']}</CONDITION>
                </ITEM>
                """
        inventory = f"""\
        <INVENTORY>
            {items_xml}
        </INVENTORY>
        """
        xml = textwrap.dedent(f"""\
        <?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE BrickStoreXML>
        {inventory}
        """)

        with open(f"{path}/{output_filename}.xml", 'w', encoding='utf-8', errors='replace') as f:
            f.write(xml)
            

class Config:
    def __init__(self, path):
        self.data = toml.load(path, _dict=dict)

class Bricklink:
    # OAuth Credentials
    def __init__(self, config):
        self.config = config.data
        self.setup_keys()
        self.auth_session()

        self.inventories = []
        self.categories = []

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
    
    def _api_call(self, end_point):
        response = self.oauth.get(f'https://api.bricklink.com/api/store/v1/{end_point}')

        if response.status_code != 200:
            print(f"Error: {response.text}")
        
        response.encoding = 'utf-8'
        
        return response.json()['data']
    
    def _set_category_names(self):
        for inv_index, inv_item in enumerate(self.inventories):
            inv_item["item"]["category_name"] = ""
            for i, dic in enumerate(self.categories):
                if dic["category_id"] == inv_item["item"]["category_id"]:
                    self.inventories[inv_index]["item"]["category_name"] = self.categories[i]["category_name"]

    
    def fetch_inventory(self):
        self.inventories = self._api_call("inventories")
        self.categories = self._api_call("categories")

    def save_all_inventories(self, file_type):
        self.fetch_inventory()
        self._set_category_names()
        filename = f"{datetime.now().strftime('%m-%d-%Y-%H-%M-%S')} - Bricklink Backup"
        path = self.config['EXPORT']['PATH']
        if file_type.lower() == "csv":
            FileWriter.json_to_csv(self.inventories, filename, path)
        else:
            FileWriter.json_to_xml(self.inventories, filename, path, self.categories)
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
