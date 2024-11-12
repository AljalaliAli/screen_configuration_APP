import json
import os
from Image_functions_v001 import cv2, resize_image_cv2, prepare_img_for_ocr as mde_img_filter



class ImageMatcher:
    """
    ImageMatcher class is designed to match specific parts of an input image with predefined template images, identifying the best match based on similarity. It uses OpenCV for image processing and template matching, and configuration files to specify the templates and their features.

    Key Techniques Used
    Template Matching with OpenCV:

    Uses OpenCV’s matchTemplate function with TM_CCOEFF_NORMED to measure similarity between images. This method provides a normalized score where values close to 1 indicate high similarity.
    Focused Region Matching (Cropping and Resizing):

    Matches specific regions of images instead of the whole image. Each template has defined "features" (areas) for precise matching. Cropping and resizing ensure that the areas of interest are compared accurately.
    Feature-Based Matching:

    Each template is broken into multiple features (specific areas), which are compared individually. If all features match, the template is considered a match for the input image.
    Configurable JSON Templates:

    Template details (paths, feature positions, etc.) are stored in a JSON file, allowing flexibility. New templates and features can be added without code changes.
    Image Preprocessing:

    Images are preprocessed to enhance clarity, making matching more accurate. This step filters out noise and optimizes the images for comparison.
    Usage
    To use ImageMatcher, initialize it with the configuration directory, JSON config file name, and templates directory. Then, call match_images with the input image to find the best matching template.

    Attributes:
    - mde_config_file_path (str): Path to the JSON configuration file.
    - mde_config_data (dict): Loaded JSON data with template configurations.
    - templa
    """
    def __init__(self, configFiles_dir, mde_config_file_name, templates_dir_name): 
        """
        Initializes the ImageMatcher with configuration and template directories.

        Parameters:
        - configFiles_dir (str): Directory for storing configuration files.
        - mde_config_file_name (str): Name of the JSON configuration file.
        - templates_dir_name (str): Directory for storing template images.
        """    
        # Ensure the MDE config directory exists
        if not os.path.exists(configFiles_dir):
            os.makedirs(configFiles_dir)

        # Construct the path to the MDE config file
        self.mde_config_file_path = os.path.join(configFiles_dir, mde_config_file_name)

        # Load MDE config data if the config file exists
        if os.path.exists(self.mde_config_file_path):
            self.mde_config_data = self.load_mde_config_data(self.mde_config_file_path)
        else:
            self.mde_config_data = {}  # Handle case where config file doesn't exist
        # Ensure the templates directory exists within the MDE config directory
        self.templates_dir =os.path.join(configFiles_dir, templates_dir_name)
        if not os.path.exists(self.templates_dir):
            os.makedirs(self.templates_dir)

       
     
    def load_mde_config_data(self, json_file_path):
        try:
            with open(json_file_path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"File not found: {json_file_path}")
            return {}
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON in file: {json_file_path}")
            print(e)
            return {}

 
    def match_images(self, img, min_match_val=0.9): 
        """
        Matches the input image against stored templates and identifies the best match.

        Parameters:
        - img (ndarray): The input image to be matched.
        - min_match_val (float): Minimum similarity score required for a match.

        Returns:
        - tuple: (match_values, temp_img_id) if a match is found, (-1, -1) if no match.
        """

       #loop throw all image templates
        for temp_img_id, temp_img_data in  self.mde_config_data["images"].items():     
            temp_img_path = os.path.join(self.templates_dir, temp_img_data["path"])   
            #print(f"temp_img_path  .........................{temp_img_path} ")
            #print('current template image size: ', temp_img_data["size"])
            match_values=[]
            features_count=0
            match_count=0
            # loop throw all feature in the current template image
            for merkma_id, feature in temp_img_data["features"].items(): 
                features_count +=1
                position = feature["position"]
                x1, x2, y1, y2=int(position["x1"]), int(position["x2"]),int( position["y1"]),int(position["y2"])
                temp_img= cv2.imread(temp_img_path)

                #resize the image to make sure ...
                img_resized = resize_image_cv2(img,temp_img_data["size"])
                cropped_img = img_resized[y1:y2, x1:x2] 
                cropped_temp = temp_img[y1:y2, x1:x2] 

                filtered_cropped_template_img =  mde_img_filter(cropped_temp)
                filterd_cropped_img =  mde_img_filter(cropped_img)
    
                match_val = self.compute_match_value(filterd_cropped_img, filtered_cropped_template_img)
               
                match_values.append(match_val)
                if match_val>= min_match_val:
                    match_count +=1
            if match_count == features_count:
                print('*********************************************')
                print('current match_values')
                print(f"match_values ={match_values}                temp_img_id = {temp_img_id}     ")
                print('*********************************************')
                    
                return  match_values,temp_img_id
        return -1,-1
   
    
    def compute_match_value(self, filterd_cropped_img, filtered_cropped_template_img):
        """
        Computes the similarity score between a cropped section of the input image and a template.

        Parameters:
        - filterd_cropped_img (ndarray): Cropped and filtered input image.
        - filtered_cropped_template_img (ndarray): Cropped and filtered template image.

        Returns:
        - float: Similarity score between -1 and 1, where 1 indicates a perfect match.
        """

        try:
            result = cv2.matchTemplate(filterd_cropped_img, filtered_cropped_template_img, cv2.TM_CCOEFF_NORMED)
            #print(f" result[0][0] = { result[0][0]}")
            cv2.imwrite("filterd_cropped_img.jpg", filterd_cropped_img)
            cv2.imwrite("filtered_cropped_template_img.jpg", filtered_cropped_template_img)
       
            _, match_val, _, _ = cv2.minMaxLoc(result)
            print(f"match_val={match_val}")
            return match_val

        except cv2.error as cv2_error:
            print(f"OpenCV Error: {cv2_error}")
            return None

        except Exception as e:
            print(f"Error: {e}")
            return None



def main():
    """
    Main function to demonstrate the ImageMatcher class. Loads an input image,
    initializes ImageMatcher with config paths, and finds the best matching template.
    """
    configFiles_dir = 'ConfigFiles'
    mde_config_file_name = 'mde_config.json'
    templates_dir_name = 'templates'

    # Load the input image for matching
    input_image_path = r"117.tiff"
    input_img = cv2.imread(input_image_path)

    # Initialize the ImageMatcher
    matcher = ImageMatcher(configFiles_dir, mde_config_file_name, templates_dir_name)

    # Perform image matching
    match_values, temp_img_id = matcher.match_images(input_img)

    # Process the matching results
    if temp_img_id != -1:
        print(f"Best template match found: {temp_img_id}")
        print(f"Match values: {match_values}")
    else:
        print("No matching template found.")

if __name__ == "__main__":
    main()



