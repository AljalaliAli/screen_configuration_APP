import configparser
import ast

class ConfigManager:
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
