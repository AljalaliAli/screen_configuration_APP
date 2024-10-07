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
        self.mde_config_dir = mde_config_dir  # Store this
        self.mde_config_file_name = mde_config_file_name  # Store this
        self.templates_dir_name = templates_dir_name  # Store this

        self.mde_config_file_path = os.path.join(mde_config_dir, mde_config_file_name)
        self.templates_dir = os.path.join(mde_config_dir, templates_dir_name)
        self.config_tool = config_tool  # Store the ConfigurationTool instance
        self.img_path = None  # Store the image path globally
        self.selected_key = None
        self.temp_img_id = None  # Initialize temp_img_id

        # Ensure the config directory, templates directory, and config.json file exist
        self.ensure_directories_and_config(mde_config_dir, self.templates_dir, self.mde_config_file_path)

        # Create ImageMatcher object for image comparison
        self.matcher = ImageMatcher(mde_config_dir, mde_config_file_name, templates_dir_name)

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

                if img_cv2 is None:
                    messagebox.showerror("Error", "Failed to load image. Please select a valid image.")
                    return None

                # Compare the selected image with the templates
                match_result = self.matcher.match_images(img_cv2)
                self.temp_img_id = int(match_result[1])

                # Synchronize with config_tool
                self.config_tool.temp_img_id = self.temp_img_id

                if self.temp_img_id != -1:
                    status_info = get_machine_status_from_temp_img_id(self.temp_img_id)

                    if status_info:
                        status_name, _ = status_info
                        self.config_tool.update_dropdown(status_name)  # Update dropdown with matched status
                    else:
                        self.config_tool.update_dropdown("")  # No valid status, clear the dropdown
                else:
                    self.config_tool.update_dropdown("")  # Clear dropdown for a new template
                return file_path, self.temp_img_id

            except Exception as e:
                messagebox.showerror("Error", f"Failed to load image: {e}")
        return None
    
    def draw_parameters_and_features(self, resize_percent_width, resize_percent_height, param_color, feature_color):
        """
        Draw rectangles and names/IDs of the parameters and features for the matched template,
        with different colors for parameters and features. The positions are scaled according to
        the resized image dimensions.
        """
        # Use the Painter class to draw the parameters and features on the image
        self.painter.draw_rectangle(self.temp_img_id, resize_percent_width, resize_percent_height, param_color, feature_color)
        
    def add_new_template(self, img_path, img_size):
        """
        Adds the selected image as a new template in the config.json file.
        Returns the template ID to be used later when adding features.
        """
        with open(self.mde_config_file_path, 'r') as file:
            config_data = json.load(file)

        # Get the selected key from the dropdown
        selected_name = self.config_tool.selected_option.get()  
        self.selected_key = self.config_tool.name_to_key.get(selected_name, None) 

        if self.selected_key is None:
            # If no dropdown option is selected, change the dropdown field background to red
            self.config_tool.dropdown.config(foreground='black', background='red')
            return None

        # Reset the dropdown style if everything is fine
        self.config_tool.dropdown.config(foreground='black', background='white')

        # Retrieve the range from choices_dict using the selected key
        choices_dict = self.config_tool.choices_dict
        image_id_range = choices_dict[self.selected_key]["range"]

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
        print(f"New template ID = {new_template_id}")
        self.temp_img_id = new_template_id  # Update self.temp_img_id

        # Synchronize with config_tool
        self.config_tool.temp_img_id = self.temp_img_id

        return new_template_id

    def add_par_but_func_threaded(self, resize_percent_width, resize_percent_height, img_not_none, box_color):
        def add_par_thread():
            print(f"[DEBUG] 'Add New Parameter' button clicked. self.temp_img_id = {self.temp_img_id}")
            if not img_not_none:
                print("[ERROR] No image loaded, cannot add parameter.")
                return

            # Activate drawing mode with the specified color for parameters
            self.painter.activate_drawing(
                add_par_but_clicked=True,
                resize_percent_width=resize_percent_width,
                resize_percent_height=resize_percent_height,
                box_color=box_color
            )

            while self.painter.last_rectangle == {}:
                pass

            # Get the parameter name and position
            par_name, par_pos = self.painter.last_rectangle.popitem()

            # Retrieve temp_img_id from config_tool
            self.temp_img_id = self.config_tool.temp_img_id

            if self.temp_img_id is not None:
                self.add_parameter_to_config(self.temp_img_id, par_name, par_pos)
                print(f"[DEBUG] Parameter '{par_name}' added to template ID: {self.temp_img_id}")
                # Notify ConfigurationTool that parameter addition is complete
                self.config_tool.on_parameter_addition_complete()
            else:
                print("[ERROR] No valid template ID found for adding parameter.")

        if img_not_none:
            thread = threading.Thread(target=add_par_thread)
            thread.start()

    def add_screen_feature_but_func_threaded(self, img_size, resize_percent_width, resize_percent_height, img_not_none, box_color):
        def add_mode_thread():
            print("[DEBUG] 'Add Screen Feature' button clicked.")
            if not self.img_path:
                messagebox.showerror("Error", "Image path is not valid. Please select a valid image.")
                return

            # Activate drawing mode with the specific color for features
            self.painter.activate_drawing(
                add_feature_but_clicked=True,
                resize_percent_width=resize_percent_width,
                resize_percent_height=resize_percent_height,
                box_color=box_color
            )

            while self.painter.last_rectangle == {}:
                pass

            # Get the feature name and position
            feature_name, feature_pos = self.painter.last_rectangle.popitem()
           # print(f"[###########Debug 1 ............. self.config_tool.temp_img_id = {self.config_tool.temp_img_id}]")
            # Add new template and get its ID
            if self.config_tool.temp_img_id == -1:
                template_id = self.add_new_template(self.img_path, img_size)
            #print(f"[###########Debug 2............. self.config_tool.temp_img_id = {self.config_tool.temp_img_id}]")
            if template_id is not None:
                self.add_feature_to_config(template_id, feature_name, feature_pos)
                print(f"[DEBUG] Feature '{feature_name}' added to template ID: {template_id}")

                # Store the template_id (temp_img_id) in the config_tool for later use
                self.config_tool.temp_img_id = template_id  # Store in config_tool
                print(f"[DEBUG] Stored current template ID (temp_img_id): {template_id}")

                # Refresh/reload the config.json file after adding the feature
                self.config_tool.reload_config()
                print("[DEBUG] config.json reloaded after adding screen feature.")

                # Notify ConfigurationTool that screen feature addition is complete
                self.config_tool.on_screen_feature_addition_complete()
            else:
                print("[ERROR] Failed to add screen feature due to invalid template ID.")

        if img_not_none:
            thread = threading.Thread(target=add_mode_thread)
            thread.start()

    def add_parameter_to_config(self, template_id, par_name, par_pos):
        """
        Adds a parameter to the config.json file for the given template_id.
        """
        # Ensure template_id is a string
        template_id = str(template_id)

        with open(self.mde_config_file_path, 'r') as file:
            config_data = json.load(file)

        # Check if the template ID exists in the config_data
        if template_id not in config_data["images"]:
            print(f"[ERROR] Template ID '{template_id}' not found in config.json.")
            return

        # Ensure the 'parameters' key exists for the current template
        if "parameters" not in config_data["images"][template_id]:
            config_data["images"][template_id]["parameters"] = {}

        # Add the parameter to the selected template
        param_id = str(len(config_data["images"][template_id]["parameters"]) + 1)
        config_data["images"][template_id]["parameters"][param_id] = {
            "name": par_name,
            "position": par_pos  # Save the original image size coordinates
        }

        # Save the updated config.json
        with open(self.mde_config_file_path, 'w') as file:
            json.dump(config_data, file, indent=2)
            file.flush()  # Ensure the data is flushed to disk immediately

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

    def reload_config(self):
        """
        Reloads the configuration by reinitializing the matcher and painter.
        """
        # Reinitialize the matcher and painter
        self.matcher = ImageMatcher(self.mde_config_dir, self.mde_config_file_name, self.templates_dir_name)
        self.painter = Painter(self.img_canvas, self.mde_config_file_path)
