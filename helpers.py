
import shutil
import json
import os
from PIL import Image


def add_item_to_template(template_id, category, item_data, config_data):
    """
    Adds an item to the specified category in the template if it does not already exist.

    Parameters:
    - template_id (str): The ID of the template.
    - category (str): Either 'parameters' or 'features'.
    - item_data (dict): The data of the item to be added.

    Returns:
    - str: The ID of the newly added item, or None if the item already exists.
    """
     
    template = config_data["images"][str(template_id)][category]
    
    # Check if item_data already exists in the template
    if item_data in template.values():
        print(f"[Debug] {(category)[:-1]} with name '{item_data.get('name')}' already exists in template '{template_id}'")
        return None  # Return None if item already exists

    # Add the new item
    item_id = get_next_available_id(template)#str(len(template) + 1)
    template[item_id] = item_data
    print(f"[Debug] Added new {(category)[:-1]} with name '{item_data.get('name')}' to template '{template_id}'.")
    return item_id


def get_next_available_id(items_dict):
    """
    Calculates the next available ID from a dictionary of items.
    
    Args:
        items_dict (dict): A dictionary where keys are IDs represented as strings.
    
    Returns:
        str: The next available ID as a string, or "1" if the dictionary is empty.
    """
    try:
        if items_dict:
            return str(int(max(map(int, items_dict.keys())))+1)
        else:
            return "1"
    except Exception as e:
        print(f"Error: {e}")
        return None


def save_template_image(img_path, templates_dir, new_template_id):
    """Saves the template image to the templates directory with its original extension."""
    # Extract the file extension from the original image path
    _, ext = os.path.splitext(img_path)
    # If no extension is found, default to '.png'
    if not ext:
        ext = '.tiff' 
    # Construct the new template image name with the original extension
    template_image_name = f"template_{new_template_id}{ext}"
    
    # Define the full path for the new template image
    template_image_path = os.path.join(templates_dir, template_image_name)
    
    # Open the original image and save it with the new name and extension
    img = Image.open(img_path)
    img.save(template_image_path)
    
    return template_image_name

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
                with open(file_path, 'w', encoding='utf-8') as file:
                    json.dump({"images": {}}, file, ensure_ascii=False, indent=2)  # Added ensure_ascii=False
                print(f"JSON file '{file_path}' was empty. Updated successfully.")
            else:
                print(f"JSON file '{file_path}' is not empty. No updates needed.")
        else:
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump({"images": {}}, file, ensure_ascii=False, indent=2)  # Added ensure_ascii=False
            print(f"JSON file '{file_path}' didn't exist. Created successfully with initial structure.")
    except Exception as e:
        print(f"Error occurred while processing '{file_path}': {e}")

def get_temp_img_details(config_data, temp_img_id):
    """
    Retrieves parameters, features, machine status conditions, size, and path 
    from the JSON configuration for a given image ID.

    Parameters:
    - config_data (str or dict): 
        - If `str`, it's treated as the file path to the JSON configuration.
        - If `dict`, it's treated as the JSON configuration data directly.
    - temp_img_id (int or str): The image ID to retrieve data for.

    Returns:
    - tuple: A tuple containing five items: 
        - parameters (dict)
        - features (dict)
        - machine_status_conditions (list)
        - size (dict or None)
        - path (str or None)
      If the image ID is not found, returns empty dictionaries and None for size and path.
    """
    try:
        # Determine the type of config_data and load data accordingly
        if isinstance(config_data, str):
            # config_data is a file path; attempt to open and load JSON data
            with open(config_data, 'r', encoding='utf-8') as file:
                json_data = json.load(file)
        elif isinstance(config_data, dict):
            # config_data is already a dictionary; use it directly
            json_data = config_data
        else:
            # Invalid type for config_data
            raise TypeError("config_data must be either a file path (str) or a dictionary (dict).")

        parameters = {}
        features = {}
        machine_status_conditions = []
        size = None
        path = None

        # Convert temp_img_id to string to ensure consistency with JSON keys
        temp_img_id_str = str(temp_img_id)

        # Check if 'images' key exists and contains the temp_img_id
        if "images" in json_data and temp_img_id_str in json_data["images"]:
            image_data = json_data["images"][temp_img_id_str]

            # Retrieve parameters if available
            if "parameters" in image_data and isinstance(image_data["parameters"], dict):
                parameters = image_data["parameters"]

            # Retrieve features if available
            if "features" in image_data and isinstance(image_data["features"], dict):
                features = image_data["features"]

            # Retrieve machine status conditions if available
            if "machine_status_conditions" in image_data and isinstance(image_data["machine_status_conditions"], list):
                machine_status_conditions = image_data["machine_status_conditions"]

            # Retrieve size if available
            if "size" in image_data and isinstance(image_data["size"], dict):
                size = image_data["size"]

            # Retrieve path if available
            if "path" in image_data and isinstance(image_data["path"], str):
                path = image_data["path"]

        else:
            print(f"[WARNING] Image ID '{temp_img_id}' not found in the configuration.")

        return parameters, features, machine_status_conditions, size, path

    except Exception as e:
        print(f"[ERROR] An error occurred: {e}")
        return {}, {}, [], None, None

def get_all_image_parameters(config_data):
    """
    Retrieves a list of dictionaries, each containing the 'name' and 'position' of each parameter 
    across all images in the configuration data.

    Parameters:
    - config_data (str or dict):
        - If `str`, it's treated as the file path to the JSON configuration.
        - If `dict`, it's treated as the JSON configuration data directly.

    Returns:
    - list: A list of dictionaries, each with keys 'name' and 'position'.
            Returns an empty list if no parameters are found or an error occurs.
    """
    try:
        # Load JSON data from file path or use the provided dictionary
        if isinstance(config_data, str):
            with open(config_data, 'r', encoding='utf-8') as file:
                json_data = json.load(file)
        elif isinstance(config_data, dict):
            json_data = config_data
        else:
            raise TypeError("config_data must be either a file path (str) or a dictionary (dict).")

        # Navigate to the 'images' section
        images = json_data.get("images", {})

        if not images:
            print("[WARNING] No 'images' key found or 'images' is empty in the configuration.")
            return []

        # Initialize a list to hold the 'name' and 'position' of each parameter
        image_parameters = []

        for image_id, image_data in images.items():
            # Process 'parameters'
            parameters = image_data.get("parameters", {})
            if not parameters:
                print(f"[WARNING] Image ID '{image_id}' has no 'parameters' section.")
                continue  # Skip images without 'parameters'

            for param_id, param_data in parameters.items():
                name = param_data.get("name")
                position = param_data.get("position")

                if name and position:
                    image_parameters.append({
                        "name": name,
                        "position": position
                    })
                else:
                    # Identify which fields are missing
                    missing = []
                    if not name:
                        missing.append("name")
                    if not position:
                        missing.append("position")
                    print(f"[WARNING] Image ID '{image_id}', Parameter ID '{param_id}' is missing fields: {', '.join(missing)}")
                    
                    # Decide whether to skip or include with default values
                    # Here, we'll include with default empty values
                    image_parameters.append({
                        "name": name if name else "",
                        "position": position if position else {}
                    })

        return image_parameters

    except FileNotFoundError:
        print(f"[ERROR] The file '{config_data}' was not found.")
        return []
    except json.JSONDecodeError:
        print(f"[ERROR] Failed to decode JSON from '{config_data}'. Please check the file format.")
        return []
    except Exception as e:
        print(f"[ERROR] An unexpected error occurred: {e}")
        return []

def calculate_original_position(position, resize_percent_width, resize_percent_height, operation='/'):
    """
    Calculates the original position by applying the specified operation on the resize percentages.
    Supported operations are division (default) and multiplication.
    
    :param position: Dictionary with position values ('x1', 'y1', 'x2', 'y2')
    :param resize_percent_width: Width resize percentage
    :param resize_percent_height: Height resize percentage
    :param operation: Operation to apply ('/' for division, '*' for multiplication)
    :return: Dictionary with calculated original positions
    """
    if operation == '/':
        org_x1 = float(position['x1']) / resize_percent_width
        org_y1 = float(position['y1']) / resize_percent_height
        org_x2 = float(position['x2']) / resize_percent_width
        org_y2 = float(position['y2']) / resize_percent_height
    elif operation == '*':
        org_x1 = float(position['x1']) * resize_percent_width
        org_y1 = float(position['y1']) * resize_percent_height
        org_x2 = float(position['x2']) * resize_percent_width
        org_y2 = float(position['y2']) * resize_percent_height
    else:
        raise ValueError("Unsupported operation. Use '/' for division or '*' for multiplication.")
    
    return {
        "x1": org_x1,
        "y1": org_y1,
        "x2": org_x2,
        "y2": org_y2
    }

def get_all_parameters_with_templates(config_data):
    """
    Returns a list of all parameters from all templates, including their template IDs.
    Each parameter dictionary includes the 'template_id' key.
    """
    parameters_list = []
    images = config_data.get('images', {})
    for image_id, image_data in images.items():
        parameters = image_data.get('parameters', {})
        for param_id, param_data in parameters.items():
            param_copy = param_data.copy()
            param_copy['template_id'] = image_id
            parameters_list.append(param_copy)
    return parameters_list

def make_hashable(o):
    if isinstance(o, (list, tuple)):
        return tuple(make_hashable(e) for e in o)
    elif isinstance(o, dict):
        return tuple(sorted((k, make_hashable(v)) for k, v in o.items()))
    else:
        return o

def remove_duplicate_dicts(dict_list):
    seen = set()
    unique_list = []
    for d in dict_list:
        # Create a copy of the dictionary without 'template_id'
        d_copy = d.copy()
        d_copy.pop('template_id', None)  # Remove 'template_id' key
        hashable_d = make_hashable(d_copy)
        if hashable_d not in seen:
            seen.add(hashable_d)
            unique_list.append(d)
  # print(f"[Debug.....] Paremetrs after removing the duplicate ")
    #for par in unique_list:
       # print(par)
    return unique_list



def remove_parameter(config_data, image_id, parameter_name, parameter_position):
    """
    Removes a parameter from the configuration data given image ID, parameter name, and parameter position.

    Parameters:
    - config_data: dict or str
        The configuration data as a dictionary, or a path to the JSON file.
    - image_id: str
        The ID of the image from which to remove the parameter.
    - parameter_name: str
        The name of the parameter to remove.
    - parameter_position: dict
        The position dictionary with keys 'x1', 'y1', 'x2', 'y2'.

    Returns:
    - json_data: dict
        The updated configuration data.
    """
    # Load JSON data from file path or use the provided dictionary
    if isinstance(config_data, str):
        with open(config_data, 'r', encoding='utf-8') as file:
            json_data = json.load(file)
    elif isinstance(config_data, dict):
        json_data = config_data
    else:
        raise TypeError("config_data must be either a file path (str) or a dictionary (dict).")

    # Access the images dictionary
    images = json_data.get('images', {})
    
    image_data = images.get(str(image_id))
    print(f"[Debug] image_data: {image_data}")
    if not image_data:
        print(f"Image ID '{image_id}' not found.")
        return json_data

    # Access the parameters dictionary
    parameters = image_data.get('parameters', {})
    parameter_ids = list(parameters.keys())

    # Iterate over the parameters to find a match
    for param_id in parameter_ids:
        param_data = parameters.get(param_id)
        if param_data:
            if (
                param_data.get('name') == parameter_name and
                param_data.get('position') == parameter_position
            ):
                # Remove the matching parameter
                del parameters[param_id]
                print(f"Removed parameter '{parameter_name}' with ID '{param_id}' from image ID '{image_id}'.")
                break
    else:
        print(f"No matching parameter found in image ID '{image_id}'.")

    # Save the updated configuration back to the file if a path was provided
    if isinstance(config_data, str):
        with open(config_data, 'w', encoding='utf-8') as file:
            json.dump(json_data, file, indent=2)
        print(f"Updated configuration saved to '{config_data}'.")

    return json_data



if __name__ == "__main__":
    print(get_possible_statuses(r'ConfigFiles\mde_config.json','40000'))
    # Create the new condition
    operand1 = create_parameter_condition("error_code", "=", "E101")
    operand2 = create_parameter_condition("run", "!=", "running")
    conditions = create_logical_condition("AND", [operand1, operand2])
    new_condition = create_machine_status_condition("Maintenance Required", conditions)
    #print(f"new_condition:{new_condition}")
   # add_machine_status_condition(r'ConfigFiles\mde_config.json', '40000', new_condition)
    _,_,machine_status_conditions,_,_=get_temp_img_details(r'ConfigFiles\mde_config.json', '1')
   # print(f'machine_status_conditions:{machine_status_conditions}')
    pars= get_all_image_parameters(r"ConfigFiles\mde_config.json")
    for par in pars:
        print(par)
     