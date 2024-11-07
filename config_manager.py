import configparser
import ast
import json
from tkinter import messagebox


class AppConfigManager:
    def __init__(self, config_file):
        self.config = configparser.ConfigParser()
        self.config.read(config_file, encoding='utf-8')

    def get_config(self, section, option):
        return self.config.get(section, option)

    def get_choices_dict(self):
        choices_dict_str = self.config.get('potential_machine_status', 'choices_dict')
        try:
            return ast.literal_eval(choices_dict_str)
        except (ValueError, SyntaxError):
            raise ValueError("Error parsing choices_dict in config.ini")



import json
from tkinter import messagebox

class ConfigData:
    # Class-level attributes to hold shared configuration data and file path
    config_data = None
    config_file_path = None

    def __init__(self, config_file_path):
        """
        Initializes the ConfigData with a configuration file path and loads the configuration.
        """
        if ConfigData.config_file_path is None:
            ConfigData.config_file_path = config_file_path
            self.load_config_data()

    def load_config_data(self):
        """
        Loads the configuration data from the JSON file and assigns it to the class-level config_data.
        """
        try:
            with open(ConfigData.config_file_path, 'r', encoding='utf-8') as file:
                ConfigData.config_data = json.load(file)
            print("[INFO] Configuration data loaded successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load configuration: {e}")
            ConfigData.config_data = {"images": {}}  # Use a default empty structure on failure

    def save_config_data(self):
        """
        Saves the configuration data back to the JSON file.
        """
        try:
            with open(ConfigData.config_file_path, 'w', encoding='utf-8') as file:
                json.dump(ConfigData.config_data, file, ensure_ascii=False, indent=2)
                file.flush()
            print(f"[INFO] Configuration data saved successfully to {ConfigData.config_file_path}.")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to save configuration to {ConfigData.config_file_path}. Error: {e}")
            messagebox.showerror("Error", f"Failed to save configuration: {e}")
            return False

    def has_config_changed(self):
        """
        Determines whether the in-memory configuration differs from the file-based configuration.
        """
        try:
            with open(ConfigData.config_file_path, 'r', encoding='utf-8') as file:
                file_data = json.load(file)
        except FileNotFoundError:
            print(f"[WARNING] The file '{ConfigData.config_file_path}' does not exist.")
            return True  # Consider it changed if the file doesn't exist
        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to parse JSON file '{ConfigData.config_file_path}': {e}")
            return True  # Consider it changed if the JSON is invalid
        except Exception as e:
            print(f"[ERROR] An unexpected error occurred while reading '{ConfigData.config_file_path}': {e}")
            return True  # Consider it changed on unexpected errors

        return ConfigData.config_data != file_data

    @staticmethod
    def get_image_data(image_id):
        """
        Retrieves data for a specific image given an image ID.

        Parameters:
        - image_id (str): The ID of the image to retrieve data for.

        Returns:
        - A dictionary containing the image data, or None if not found.
        """
        return ConfigData.config_data.get("images", {}).get(str(image_id))



if __name__ == "__main__":
    # Assuming the config file path is 'tst.json'
    config_file_path = 'tst.json'

    # Create the first object of ConfigData
    config_data_1 = ConfigData(config_file_path)

    # Modify the configuration data through the first object
    if ConfigData.config_data is not None:
        ConfigData.config_data['images']['40000']['features']['4'] = {
            "name": "new_feature_added",
            "position": {
                "x1": 120,
                "y1": 180,
                "x2": 220,
                "y2": 280
            }
        }
        config_data_1.save_config_data()

    # Create the second object of ConfigData
    config_data_2 = ConfigData(config_file_path)

    # Print the modified configuration data through the second object
    print(config_data_2.config_data)
    print(json.dumps(ConfigData.config_data, indent=2))
