import json
import os
import shutil
import configparser
import ast

def load_data(data_input):
    """
    Loads data from a JSON file if a file path is provided,
    or returns the data if it's already a dictionary.
    """
    if isinstance(data_input, str):
        # Assume it's a file path
        if os.path.isfile(data_input):
            with open(data_input, 'r', encoding='utf-8') as file:
                return json.load(file)
        else:
            raise FileNotFoundError(f"The file {data_input} does not exist.")
    elif isinstance(data_input, dict):
        # Data is already a dictionary
        return data_input
    else:
        raise ValueError("Data must be a dictionary or a valid file path.")

def create_parameter_condition(parameter, operator, value):
    """
    Creates a leaf condition for a parameter comparison.
    :param parameter: The name of the parameter (e.g., 'run').
    :param operator: The comparison operator (e.g., '=', '!=', '>', '<=').
    :param value: The value to compare against.
    :return: A dictionary representing the parameter condition.
    """
    return {
        "parameter": parameter,
        "operator": operator,
        "value": value
    }

def create_logical_condition(operator, operands):
    """
    Creates a logical condition that combines multiple conditions.
    :param operator: The logical operator ('AND' or 'OR').
    :param operands: A list of conditions (parameter conditions or nested logical conditions).
    :return: A dictionary representing the logical condition.
    """
    return {
        "operator": operator,
        "operands": operands
    }

def create_machine_status_condition(status, conditions):
    """
    Creates a machine status condition dictionary.
    :param status: The status name (e.g., 'Maintenance Required').
    :param conditions: The conditions dict (created using create_logical_condition or create_parameter_condition).
    :return: A dictionary representing the machine status condition.
    """
    return {
        "status": status,
        "conditions": conditions
    }


def add_machine_status_condition(data_input, img_temp_id, new_condition):
    """
    Adds a new machine status condition to the specified image if it doesn't already exist,
    and saves the data back to the JSON file if a file path is provided.
    """
    # Load the data
    data = load_data(data_input)
 
    # Get the image data
    image = data.get("images", {}).get(str(img_temp_id))
    if not image:
        print(f"Error: No data found for image template ID: {img_temp_id}")
        return data  # Return data unchanged

    # Get or initialize the machine_status_conditions list
    machine_status_conditions = image.setdefault("machine_status_conditions", [])

    # Append the new condition if it is not already present
    if new_condition not in machine_status_conditions:
        machine_status_conditions.append(new_condition)
    else:
        print("The condition already exists in the list.")

    # Save the updated data back to the JSON file if data_input is a file path
    if isinstance(data_input, str):
        with open(data_input, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
    else:
        print("Warning: data_input is not a file path. Changes not saved to file.")

    # Return the updated data
    return data



def get_possible_statuses(data_input, img_temp_id):
    """
    Returns a list of possible machine statuses for the given image template ID.
    :param data_input: Dictionary or path to JSON file containing the data.
    :param img_temp_id: The image template ID (e.g., '40000').
    :return: List of possible statuses.
    """
    data = load_data(data_input)
    image = data.get("images", {}).get(str(img_temp_id))
    if not image:
        print(f"No data found for image template ID: {img_temp_id}")
        return []
    
    machine_status_conditions = image.get("machine_status_conditions")
    if not machine_status_conditions:
        # machine_status_conditions does not exist or is empty
        return []
    
    statuses = [condition["status"] for condition in machine_status_conditions]
    return statuses


def remove_machine_status_condition(data_input, img_temp_id, status_name):
    """
    Removes a machine status condition from the specified image based on the status name.
    :param data_input: Dictionary or path to JSON file containing the data.
    :param img_temp_id: The image template ID from which the condition will be removed.
    :param status_name: The name of the status to remove.
    """
    data = load_data(data_input)
    image = data.get("images", {}).get(str(img_temp_id))
    if not image:
        print(f"No data found for image template ID: {img_temp_id}")
        return
    
    machine_status_conditions = image.get("machine_status_conditions", [])
    if not machine_status_conditions:
        print(f"No machine status conditions found for image {img_temp_id}.")
        return

    original_length = len(machine_status_conditions)
    machine_status_conditions = [
        condition for condition in machine_status_conditions
        if condition["status"] != status_name
    ]
    image["machine_status_conditions"] = machine_status_conditions

    if len(machine_status_conditions) < original_length:
        print(f"Removed condition '{status_name}' from image {img_temp_id}.")
    else:
        print(f"No condition with status '{status_name}' found in image {img_temp_id}.")

    return data  # Return the updated data

def update_machine_status_condition(data_input, img_temp_id, status_name, updated_condition):
    """
    Updates an existing machine status condition for the specified image.
    :param data_input: Dictionary or path to JSON file containing the data.
    :param img_temp_id: The image template ID where the condition will be updated.
    :param status_name: The name of the status to update.
    :param updated_condition: A dictionary representing the updated condition.
    """
    data = load_data(data_input)
    image = data.get("images", {}).get(str(img_temp_id))
    if not image:
        print(f"No data found for image template ID: {img_temp_id}")
        return

    machine_status_conditions = image.get("machine_status_conditions", [])
    for i, condition in enumerate(machine_status_conditions):
        if condition["status"] == status_name:
            machine_status_conditions[i] = updated_condition
            print(f"Updated condition '{status_name}' in image {img_temp_id}.")
            return data  # Return the updated data

    print(f"No condition with status '{status_name}' found in image {img_temp_id}.")
    return data  # Return the data unchanged

def list_machine_status_conditions(data_input, img_temp_id):
    """
    Lists all machine status conditions for the specified image.
    :param data_input: Dictionary or path to JSON file containing the data.
    :param img_temp_id: The image template ID whose conditions will be listed.
    :return: A list of machine status conditions.
    """
    data = load_data(data_input)
    image = data.get("images", {}).get(str(img_temp_id))
    if not image:
        print(f"No data found for image template ID: {img_temp_id}")
        return []
    
    machine_status_conditions = image.get("machine_status_conditions", [])
    return machine_status_conditions


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



if __name__ == "__main__":
    print(get_possible_statuses(r'ConfigFiles\mde_config.json','40000'))
    # Create the new condition
    operand1 = create_parameter_condition("error_code", "=", "E101")
    operand2 = create_parameter_condition("run", "!=", "running")
    conditions = create_logical_condition("AND", [operand1, operand2])
    new_condition = create_machine_status_condition("Maintenance Required", conditions)
    #print(f"new_condition:{new_condition}")
    add_machine_status_condition(r'ConfigFiles\mde_config.json', '40000', new_condition)