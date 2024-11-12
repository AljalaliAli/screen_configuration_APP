import sys
import os
import shutil
import subprocess

# --------------------- Determine if Module Should Be Downloaded ---------------------

def should_download_module():
    """Determine whether to download the module based on the running program's extension."""
    script_name = os.path.basename(sys.argv[0])
    script_ext = os.path.splitext(script_name)[1].lower()
    if script_ext in ['.exe', '.bit'] or getattr(sys, 'frozen', False):
        return False
    else:
        return True

# --------------------- Download and Preload Module ---------------------

def download_and_preload_module():
    """Downloads the required module using Git and preloads it into sys.modules before any imports."""
    # Import configparser locally to avoid conflicts
    import configparser
    config = configparser.ConfigParser()
    config.read('config.ini')

    try:
        script_name = config.get('Scripts', 'pattern_detection_script_name')
        repo_url = config.get('Scripts', 'pattern_detection_repo_url')
        print(f"🔍 Configuration Loaded: Script Name = '{script_name}', Repository URL = '{repo_url}'")
    except Exception as e:
        print(f"❌ Error reading script configuration: {e}")
        sys.exit(1)

    # Directory to clone the repository
    repo_dir = 'pattern_detection_repo'

    # Check if the script already exists in the current directory
    if not os.path.isfile(script_name):
        print(f"🔄 '{script_name}' not found. Attempting to clone or update the repository...")

        # Check if the repository directory exists
        if not os.path.isdir(repo_dir):
            # Clone the repository
            print(f"🔄 Cloning repository from {repo_url}...")
            try:
                subprocess.check_call(['git', 'clone', repo_url, repo_dir])
                print(f"✅ Repository cloned successfully.")
            except subprocess.CalledProcessError as e:
                print(f"❌ Error cloning repository: {e}")
                sys.exit(1)
        else:
            # Pull the latest changes
            print(f"🔄 Repository already exists. Pulling latest changes...")
            try:
                subprocess.check_call(['git', '-C', repo_dir, 'pull'])
                print(f"✅ Repository updated successfully.")
            except subprocess.CalledProcessError as e:
                print(f"❌ Error updating repository: {e}")
                sys.exit(1)

        # Copy the required script to the current directory
        src_script_path = os.path.join(repo_dir, script_name)
        if os.path.isfile(src_script_path):
            try:
                shutil.copy(src_script_path, script_name)
                print(f"✅ '{script_name}' copied to current directory.")
            except Exception as e:
                print(f"❌ Error copying '{script_name}': {e}")
                sys.exit(1)
        else:
            print(f"❌ '{script_name}' not found in the repository.")
            sys.exit(1)
    else:
        print(f"✅ '{script_name}' already exists. No download needed.")

    # Dynamically import the module and preload it into sys.modules
    module_name = os.path.splitext(script_name)[0]
    module_path = os.path.abspath(script_name)
    if module_name in sys.modules:
        print(f"🟢 Module '{module_name}' already in sys.modules.")
    else:
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            if spec is None:
                print(f"❌ Cannot find spec for module '{module_name}'.")
                sys.exit(1)
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module  # Preload into sys.modules
            spec.loader.exec_module(module)
            print(f"🟢 Successfully imported '{module_name}' and added to sys.modules.")
        except Exception as e:
            print(f"❌ Error importing '{module_name}': {e}")
            sys.exit(1)

# Call the function before any other imports if needed
if should_download_module():
    download_and_preload_module()
else:
    print("🔒 Running as an executable or bit file. Skipping module download.")

# --------------------- Proceed with Other Imports ---------------------

from config_manager import AppConfigManager
from ui_components import ConfigurationTool

# --------------------- Main Application Code ---------------------

def main():
    # Initialize configuration manager with config.ini
    config_manager = AppConfigManager('config.ini')

    # Extract paths and settings from other config sections
    try:
        config_files_dir = config_manager.get_config('Paths', 'configFiles_dir')
        config_file = config_manager.get_config('Paths', 'config_file')
        templates_dir = config_manager.get_config('Paths', 'templates_dir')
        choices_dict = config_manager.get_choices_dict()
        print("🔧 Paths and settings extracted successfully.")
    except Exception as e:
        print(f"❌ Error reading paths or choices configuration: {e}")
        sys.exit(1)

    # Initialize and run the ConfigurationTool
    try:
        config_tool = ConfigurationTool(
            mde_config_dir=config_files_dir,
            mde_config_file_name=config_file,
            templates_dir_name=templates_dir,
            choices_dict=choices_dict
        )
        print("🟢 Configuration Tool initialized successfully. Launching UI...")
        config_tool.mainloop()
    except Exception as e:
        print(f"❌ Failed to initialize Configuration Tool: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
