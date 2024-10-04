from painter import Painter
from tkinter import filedialog, messagebox
from tkinter import ttk
import threading
import os
import json
import cv2
from PIL import Image
from pattern_detection import ImageMatcher  # Import the ImageMatcher class
from helpers import get_machine_status_from_temp_img_id, get_max_image_id

class ButtonFunctions:
    def __init__(self, img_canvas, mde_config_dir, mde_config_file_name, templates_dir_name, config_tool):
        self.img_canvas = img_canvas
        self.mde_config_file_path = os.path.join(mde_config_dir, mde_config_file_name)
        self.templates_dir = os.path.join(mde_config_dir, templates_dir_name)
        self.config_tool = config_tool  # Store the ConfigurationTool instance
        self.img_path = None  # Add this line to store the image path globally

        # Ensure the config directory, templates directory, and config.json file exist
        self.ensure_directories_and_config(mde_config_dir, self.templates_dir, self.mde_config_file_path)

        # Create ImageMatcher object for image comparison
        self.matcher = ImageMatcher(self.templates_dir)

        # Initialize the painter class
        self.painter = Painter(img_canvas, self.mde_config_file_path)

    def ensure_directories_and_config(self, config_dir, templates_dir, config_file):
        """
        Ensure that the config directory, templates directory, and config.json file exist.
        Create them if they don't exist.
        """
        # Check if the config directory exists, if not create it
        if not os.path.exists(config_dir):
            print(f"Creating config directory: {config_dir}")
            os.makedirs(config_dir)

        # Check if the templates directory exists, if not create it
        if not os.path.exists(templates_dir):
            print(f"Creating templates directory: {templates_dir}")
            os.makedirs(templates_dir)

        # Check if the config.json file exists, if not create it
        if not os.path.exists(config_file):
            print(f"Creating config file: {config_file}")
            with open(config_file, 'w') as file:
                # Create an empty JSON structure
                json.dump({"images": {}}, file, indent=2)


    def browse_files(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image Files", "*.bmp *.jpg *.jpeg *.png *.tif *.tiff"), ("All Files", "*.*")]
        )
        if file_path:
            self.img_path = file_path  # Save the selected image path globally
            try:
                # Load the image using OpenCV for consistency with the matcher
                img_cv2 = cv2.imread(file_path)
                
                # Check if the image was loaded properly
                if img_cv2 is None:
                    messagebox.showerror("Error", "Failed to load image. Please select a valid image.")
                    return None

                print(f"[DEBUG] Loaded Image Properties: Shape = {img_cv2.shape}, Dtype = {img_cv2.dtype}")  # Debugging image properties
                
           

                # Compare the selected image with the templates
                match_result = self.matcher.match_images(img_cv2)
                temp_img_id = int(match_result[1])

                print(f"[DEBUG] Template matching result: {match_result}")  # Debug statement

                if temp_img_id != -1:
                    print(f"[DEBUG] Template ID found: {temp_img_id}")  # Debug statement
                    
                    # Update the dropdown list with the status of the matched template
                    status_info = get_machine_status_from_temp_img_id(temp_img_id)
                    print(f"[DEBUG] Status Info Retrieved: {status_info}")  # Debug statement
                    
                    if status_info:
                        status_name, _ = status_info
                        print(f"[DEBUG] Updating dropdown with status: {status_name}")  # Debug statement
                        self.config_tool.update_dropdown(status_name)  # Update dropdown with matched status
                    else:
                        print("[DEBUG] No valid status found. Clearing dropdown.")  # Debug statement
                        self.config_tool.update_dropdown("")  # No valid status, clear the dropdown
                else:
                    # No match, save the image as a new template
                    template_id = self.add_new_template(file_path, img_cv2.shape[:2])
                    print(f"[DEBUG] No match found. Saved as new template: {template_id}")  # Debug statement
                    self.config_tool.update_dropdown("")  # Clear the dropdown for new template
                return file_path, temp_img_id
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load image: {e}")
        return None


    
    def draw_parameters_and_features(self, temp_img_id, resize_percent_width, resize_percent_height, param_color, feature_color):
        """
        Draw rectangles and names/IDs of the parameters and features for the matched template,
        with different colors for parameters and features. The positions are scaled according to
        the resized image dimensions.
        """
        # Use the Painter class to draw the parameters and features on the image
        self.painter.draw_rectangle(temp_img_id, resize_percent_width, resize_percent_height, param_color, feature_color)


        
    def add_new_template(self, img_path, img_size):
        """
        Adds the selected image as a new template in the config.json file.
        Returns the template ID to be used later when adding features.
        """
        with open(self.mde_config_file_path, 'r') as file:
            config_data = json.load(file)

        # Get the selected key from the dropdown
        selected_name = self.config_tool.selected_option.get()  
        selected_key = self.config_tool.name_to_key.get(selected_name, None) 

        if selected_key is None:
            # If no dropdown option is selected, show an error message
            self.config_tool.dropdown.configure(style="TCombobox")
            messagebox.showerror("Selection Required", "Please select an option from the dropdown list.")
            return None

        # Retrieve the range from choices_dict using the selected key
        choices_dict = self.config_tool.choices_dict
        image_id_range = choices_dict[selected_key]["range"]

        # Get the max image ID in the selected range
        max_image_id = get_max_image_id(config_data, image_id_range)

        # If no max image ID is found, use the minimum value in the range
        if max_image_id is None:
            new_template_id = image_id_range[0]
        else:
            new_template_id = max_image_id + 1

        # Save the image to the templates directory
        template_image_name = f"template_{new_template_id}.png"
        template_image_path = os.path.join(self.templates_dir, template_image_name)
        img = Image.open(img_path)
        img.save(template_image_path)  # Save as PNG

        # Add the template metadata to config.json
        config_data["images"][str(new_template_id)] = {
            "path": template_image_name,
            "size": {"width": img_size["width"], "height": img_size["height"]},
            "parameters": {},
            "features": {}
        }

        # Save the updated config.json
        with open(self.mde_config_file_path, 'w') as file:
            json.dump(config_data, file, indent=2)

        return new_template_id
        





    def add_par_but_func_threaded(self, resize_percent_width, resize_percent_height, img_not_none, box_color):
        def add_par_thread():
            # Activate drawing mode with the specific color for parameter (green)
            self.painter.activate_drawing(
                add_par_but_clicked=True,
                resize_percent_width=resize_percent_width,
                resize_percent_height=resize_percent_height,
                box_color=box_color  # Pass the color for drawing
            )
            while self.painter.last_rectangle == {}:
                pass

            # Get the parameter name and position (already saved with original coordinates)
            par_name, par_pos = self.painter.last_rectangle.popitem()

            # Save parameter to config.json with the original image coordinates
            self.add_parameter_to_config(par_name, par_pos)

        if img_not_none:
            thread = threading.Thread(target=add_par_thread)
            thread.start()


    def add_mode_feature_but_func_threaded(self, img_size, resize_percent_width, resize_percent_height, img_not_none, box_color):
        def add_mode_thread():
            # Check if the image path is valid
            if not self.img_path:
                messagebox.showerror("Error", "Image path is not valid. Please select a valid image.")
                return

            # Activate drawing mode with the specific color for mode/feature (red)
            self.painter.activate_drawing(
                add_feature_but_clicked=True,
                resize_percent_width=resize_percent_width,
                resize_percent_height=resize_percent_height,
                box_color=box_color  # Pass the color for drawing
            )
            
            while self.painter.last_rectangle == {}:
                pass

            # Get the feature name and position
            feature_name, feature_pos = self.painter.last_rectangle.popitem()

            # Use the correct template_id for adding the feature
            template_id = self.add_new_template(self.img_path, img_size)
            if template_id is not None:
                self.add_feature_to_config(template_id, feature_name, feature_pos)

        if img_not_none:
            thread = threading.Thread(target=add_mode_thread)
            thread.start()




    def add_parameter_to_config(self, par_name, par_pos):
        """
        Adds a parameter to the config.json file.
        """
        with open(self.mde_config_file_path, 'r') as file:
            config_data = json.load(file)

        # Assuming the last selected template is the current one
        current_template_id = str(len(config_data["images"]))

        # Add the parameter to the selected template
        param_id = str(len(config_data["images"][current_template_id]["parameters"]) + 1)
        config_data["images"][current_template_id]["parameters"][param_id] = {
            "name": par_name,
            "position": par_pos  # Save the original image size coordinates
        }

        # Save the updated config.json
        with open(self.mde_config_file_path, 'w') as file:
            json.dump(config_data, file, indent=2)


    def add_feature_to_config(self, template_id, feature_name, feature_pos):
        """
        Adds a feature to the config.json file for the given template_id.
        """
        with open(self.mde_config_file_path, 'r') as file:
            config_data = json.load(file)

        # Ensure the template ID exists
        if str(template_id) not in config_data["images"]:
            messagebox.showerror("Error", f"Template ID {template_id} not found in config.json.")
            return None

        # Add the feature to the selected template
        if "features" not in config_data["images"][str(template_id)]:
            config_data["images"][str(template_id)]["features"] = {}

        # Get the next available feature ID
        feature_id = str(len(config_data["images"][str(template_id)]["features"]) + 1)

        # Add the new feature
        config_data["images"][str(template_id)]["features"][feature_id] = {
            "name": feature_name,
            "position": feature_pos
        }

        # Save the updated config.json
        with open(self.mde_config_file_path, 'w') as file:
            json.dump(config_data, file, indent=2)



    def clear_canvas(self, img_canvas, img_item):
        """
        Clears the canvas except for the loaded image.
        """
        for item in img_canvas.find_all():
            if item != img_item:
                img_canvas.delete(item)
