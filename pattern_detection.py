import json
import cv2
import os
from image_processing import resize_image_cv2, convert_to_grayscale

class ImageMatcher:
    def __init__(self, mde_config_dir, mde_config_file_name, templates_dir_name):
        self.mde_config_file_path = f'{mde_config_dir}/{mde_config_file_name}'
        if not os.path.exists(self.mde_config_file_path):
            self.mde_config_data = {}
        else:
            self.mde_config_data = self.load_mde_config_data(self.mde_config_file_path)

        self.templates_dir = f'{mde_config_dir}/{templates_dir_name}'

    def load_mde_config_data(self, json_file_path):
        try:
            with open(json_file_path, 'r') as file:
                return json.load(file)
        except Exception as e:
            print(f"Error: {e}")
            return {}

    def match_images(self, img, min_match_val=0.9):
        for temp_img_id, temp_img_data in self.mde_config_data["images"].items():
            temp_img_path = f'{self.templates_dir}/{temp_img_data["path"]}'
            match_values = []
            features_count, match_count = 0, 0
            temp_img = cv2.imread(temp_img_path)

            for feature_id, feature in temp_img_data["features"].items():
                features_count += 1
                pos = feature["position"]
                x1, y1, x2, y2 = int(pos["x1"]), int(pos["y1"]), int(pos["x2"]), int(pos["y2"])

                img_resized = resize_image_cv2(img, temp_img_data["size"])
                cropped_img = img_resized[y1:y2, x1:x2]
                cropped_temp = temp_img[y1:y2, x1:x2]

                match_val = self.compute_match_value(convert_to_grayscale(cropped_img), convert_to_grayscale(cropped_temp))
                if match_val >= min_match_val:
                    match_count += 1

            if match_count == features_count:
                return match_values, temp_img_id
        return -1, -1

    def compute_match_value(self, img_gray, template):
        try:
            result = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)
            return cv2.minMaxLoc(result)[1]
        except Exception as e:
            print(f"Error: {e}")
            return None
