import json
import os
import shutil
import configparser
import ast


def get_max_image_id(data, image_id_range):
    """
    Returns the maximum image ID within the specified range from the configuration data.

    Parameters:
    - data (dict or str): The configuration data or path to the JSON file.
    - image_id_range (tuple): A tuple specifying the range of image IDs.

    Returns:
    - int: The maximum image ID within the range, or None if not found.
    """
    if isinstance(data, str):
        with open(data, 'r') as file:
            data = json.load(file)

    if 'images' not in data:
        raise ValueError("The provided input does not contain the 'images' key.")

    image_ids = [int(image_id) for image_id in data['images'].keys()]
    filtered_ids = [image_id for image_id in image_ids if image_id_range[0] <= image_id <= image_id_range[1]]

    return max(filtered_ids) if filtered_ids else None


def get_machine_status_from_temp_img_id(temp_img_id, config_ini_path='config.ini'):
    """
    Retrieves the machine status name and key based on the temporary image ID.

    Parameters:
    - temp_img_id (int): The temporary image ID.
    - config_ini_path (str): Path to the configuration INI file.

    Returns:
    - tuple: A tuple containing the status name and key, or None if not found.
    """
    config = configparser.ConfigParser()
    config.read(config_ini_path, encoding='utf-8')

    if 'potential_machine_status' not in config or 'choices_dict' not in config['potential_machine_status']:
        raise Exception(
            "The 'choices_dict' is not found in the 'potential_machine_status' section of the config.ini."
        )

    choices_dict_str = config['potential_machine_status']['choices_dict']

    try:
        choices_dict = ast.literal_eval(choices_dict_str)
    except Exception as e:
        raise Exception(f"Error parsing 'choices_dict' from config.ini: {e}")

    for key, value in choices_dict.items():
        range_start, range_end = value['range']
        if range_start <= temp_img_id <= range_end:
            return (value['name'], key)
    return None


def get_last_id(items_dict):
    """
    Returns the highest numeric key in the dictionary as a string.

    Parameters:
    - items_dict (dict): Dictionary of items.

    Returns:
    - str: The highest key as a string, or "0" if empty.
    """
    try:
        if items_dict:
            return str(max(map(int, items_dict.keys())))
        else:
            return "0"
    except Exception as e:
        print(f"Error: {e}")
        return None


def copy_and_rename_file(file_path, dst_dir, new_filename):
    """
    Copies and renames a file to the specified directory.

    Parameters:
    - file_path (str): Path to the source file.
    - dst_dir (str): Destination directory.
    - new_filename (str): New filename without extension.

    Returns:
    - str: New filename with extension.
    """
    try:
        src_dir, original_filename = os.path.split(file_path)
        extension = os.path.splitext(original_filename)[1]
        new_filename_with_extension = f"{new_filename}{extension}"

        dst_file_path = os.path.join(dst_dir, new_filename_with_extension)

        if os.path.exists(dst_file_path):
            os.remove(dst_file_path)

        shutil.copy2(file_path, dst_file_path)

        return new_filename_with_extension
    except Exception as e:
        print(f"Error copying and renaming file: {e}")
        return None


def check_and_update_json_config_file(file_path):
    """
    Ensures that the JSON configuration file exists and has the correct structure.

    Parameters:
    - file_path (str): Path to the JSON file.
    """
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                with open(file_path, 'w') as file:
                    json.dump({"images": {}}, file, indent=2)
                print(f"JSON file '{file_path}' was empty. Updated successfully.")
            else:
                print(f"JSON file '{file_path}' is not empty. No updates needed.")
        else:
            with open(file_path, 'w') as file:
                json.dump({"images": {}}, file, indent=2)
            print(f"JSON file '{file_path}' didn't exist. Created successfully with initial structure.")
    except Exception as e:
        print(f"Error occurred while processing '{file_path}': {e}")


def get_parameters_and_features_by_id(json_file_path, temp_img_id):
    """
    Retrieves parameters and features from the JSON configuration for a given image ID.

    Parameters:
    - json_file_path (str): Path to the JSON configuration file.
    - temp_img_id (int or str): The image ID to retrieve data for.

    Returns:
    - tuple: A tuple containing two dictionaries: parameters and features.
    """
    try:
        with open(json_file_path, 'r') as file:
            json_data = json.load(file)
        
        parameters = {}
        features = {}

        if str(temp_img_id) in json_data["images"]:
            image_data = json_data["images"][str(temp_img_id)]

            if "parameters" in image_data:
                parameters = image_data["parameters"]

            if "features" in image_data:
                features = image_data["features"]

        return parameters, features
    except Exception as e:
        print(f"Error retrieving parameters and features: {e}")
        return {}, {}
