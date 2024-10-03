import json
import os
import shutil
import configparser
import ast

def get_max_image_id(data, image_id_range):
    if isinstance(data, str):
        with open(data, 'r') as file:
            data = json.load(file)

    if 'images' not in data:
        raise ValueError("The provided input does not contain the 'images' key.")

    image_ids = [int(image_id) for image_id in data['images'].keys()]
    filtered_ids = [image_id for image_id in image_ids if image_id_range[0] <= image_id <= image_id_range[1]]

    return max(filtered_ids) if filtered_ids else None

def get_machine_status_from_temp_img_id(temp_img_id, config_ini_path='config.ini'):
    config = configparser.ConfigParser()
    config.read(config_ini_path, encoding='utf-8')

    if 'potential_machine_status' not in config or 'choices_dict' not in config['potential_machine_status']:
        raise Exception("The 'choices_dict' is not found in the 'potential_machine_status' section of the config.ini.")

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

def get_last_id(images_dict):
    try:
        if images_dict:
            return str(max(map(int, images_dict.keys())))
        else:
            return "0"
    except Exception as e:
        print(f"Error: {e}")
        return None

def add_new_image(images_dict, size, img_path, templates_dir):
    try:
        last_id = get_last_id(images_dict)
        new_id = str(int(last_id) + 1)
        new_img_path = copy_and_rename_file(img_path, templates_dir, new_id)
        images_dict[new_id] = {
            "size": size,
            "path": new_img_path,
            "features": {},
            "parameters": {}
        }
        return new_id
    except Exception as e:
        print(f"Error adding new image: {e}")
        return None

def add_new_feature(images_dict, temp_img_id, img_path, templates_dir, img_size, position, value='', sypol=''):
    try:
        if temp_img_id == -1:
            temp_img_id = add_new_image(images_dict, img_size, img_path, templates_dir)

        last_feature_id = get_last_id(images_dict[temp_img_id]["features"])
        new_feature_id = str(int(last_feature_id) + 1)

        old_template_img_path = os.path.join(templates_dir, images_dict[temp_img_id]["path"])
        if os.path.abspath(img_path) != os.path.abspath(old_template_img_path):
            shutil.copy2(img_path, old_template_img_path)

        images_dict[temp_img_id]["parameters"] = {}
        images_dict[temp_img_id]["features"][new_feature_id] = {
            "position": position,
            "value": value,
            "sypol": sypol
        }

        return temp_img_id, new_feature_id
    except Exception as e:
        print(f"Error adding new feature: {e}")
        return None

def add_new_parameter(images_dict, temp_img_id, position, name):
    try:
        last_parameter_id = get_last_id(images_dict[temp_img_id]["parameters"])
        new_parameter_id = str(int(last_parameter_id) + 1)

        images_dict[temp_img_id]["parameters"][new_parameter_id] = {
            "name": name,
            "position": position
        }

        return new_parameter_id
    except Exception as e:
        print(f"Error adding new parameter: {e}")
        return None

def get_parameters_and_features_by_id(json_file_path, temp_img_id):
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

def add_attributes_to_json(json_file_path, id, path, features, parameters):
    try:
        if os.path.exists(json_file_path):
            with open(json_file_path, 'r') as file:
                data = json.load(file)
        else:
            data = {"images": []}

        new_attributes = {
            "id": id,
            "path": path,
            "features": features,
            "parameters": parameters
        }

        data["images"].append(new_attributes)

        with open(json_file_path, 'w') as file:
            json.dump(data, file, indent=2)
    except Exception as e:
        print(f"Error adding attributes to JSON file: {e}")

def copy_and_rename_file(file_path, dst_dir, new_filename):
    try:
        src_dir, original_filename = os.path.split(file_path)
        extension = os.path.splitext(original_filename)[1]
        new_filename_with_extension = f"{new_filename}{extension}"

        if os.path.exists(os.path.join(dst_dir, new_filename_with_extension)):
            os.remove(os.path.join(dst_dir, new_filename_with_extension))

        shutil.copy2(os.path.join(src_dir, original_filename), os.path.join(dst_dir, new_filename_with_extension))

        return new_filename_with_extension
    except Exception as e:
        print(f"Error copying and renaming file: {e}")
        return None

def check_and_update_json_config_file(file_path):
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
