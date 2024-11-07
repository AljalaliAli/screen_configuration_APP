from config_manager import AppConfigManager
from ui_components import ConfigurationTool
import sys

def main():
    # Initialize configuration
    config_manager = AppConfigManager('config.ini')
    
    # Extract paths and settings from the config
    config_files_dir = config_manager.get_config('Paths', 'configFiles_dir')
    config_file = config_manager.get_config('Paths', 'config_file')
    templates_dir = config_manager.get_config('Paths', 'templates_dir')
    choices_dict = config_manager.get_choices_dict()
    
    # Initialize and run the ConfigurationTool
    config_tool = ConfigurationTool(
        mde_config_dir=config_files_dir,
        mde_config_file_name=config_file,
        templates_dir_name=templates_dir,
        choices_dict=choices_dict
    )
    config_tool.mainloop()

if __name__ == "__main__":
    sys.exit(main())
