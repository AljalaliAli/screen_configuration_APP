from painter import Painter
from tkinter import filedialog, messagebox
import threading
import os
import json
import cv2
from PIL import Image
from pattern_detection import ImageMatcher  # Import the ImageMatcher class

class ButtonFunctions:
    def __init__(self, img_canvas, mde_config_dir, mde_config_file_name, templates_dir_name):
        self.img_canvas = img_canvas
        self.mde_config_file_path = os.path.join(mde_config_dir, mde_config_file_name)
        self.templates_dir = os.path.join(mde_config_dir, templates_dir_name)

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
        """
        Browse and load an image, save it as a template if no match is found.
        """
        file_path = filedialog.askopenfilename(
            filetypes=[("Image Files", "*.bmp *.jpg *.jpeg *.png *.tif *.tiff"), ("All Files", "*.*")]
        )
        if file_path:
            try:
                # Load the image using PIL.Image
                img = Image.open(file_path)
                img_cv2 = cv2.imread(file_path)  # Convert PIL image to OpenCV format

                # Compare the selected image with the templates
                temp_img_id = int(self.matcher.match_images(img_cv2)[1])

                if temp_img_id != -1:
                    # Get canvas size and image size
                    canvas_width = self.img_canvas.winfo_width()
                    canvas_height = self.img_canvas.winfo_height()
                    img_width, img_height = img.size

                    # Calculate resize percentages
                    resize_percent_width = canvas_width / img_width
                    resize_percent_height = canvas_height / img_height

                    print(f"Canvas size: {canvas_width}x{canvas_height}, Image size: {img_width}x{img_height}")
                    print(f"Resize percentages: width = {resize_percent_width}, height = {resize_percent_height}")

                    messagebox.showinfo("Match Found", f"Matching template found: Template ID {temp_img_id}")
                    
                    # Draw parameters (green) and features (red) on the matched image
                    self.draw_parameters_and_features(temp_img_id, resize_percent_width, resize_percent_height, param_color="#00ff00", feature_color="#ff0000")
                    
                    return file_path, temp_img_id
                else:
                    # No match, save the image as a new template
                    template_id = self.add_new_template(file_path, img.size)
                    messagebox.showinfo("New Template", f"No match found. Saved as new template: Template ID {template_id}")
                    return file_path, template_id  # Return image path and new template ID
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
        Add the selected image as a new template in the config.json file.
        """
        with open(self.mde_config_file_path, 'r') as file:
            config_data = json.load(file)

        # Get the new template ID
        template_id = str(len(config_data["images"]) + 1)

        # Save the image to the templates directory
        template_image_name = f"template_{template_id}.png"
        template_image_path = os.path.join(self.templates_dir, template_image_name)
        img = Image.open(img_path)
        img.save(template_image_path)  # Save as PNG

        # Add the template metadata to config.json
        config_data["images"][template_id] = {
            "path": template_image_name,
            "size": {"width": img_size[0], "height": img_size[1]},
            "parameters": {},
            "features": {}
        }

        # Save the updated config.json
        with open(self.mde_config_file_path, 'w') as file:
            json.dump(config_data, file, indent=2)

        return template_id

    def add_par_but_func_threaded(self, resize_percent_width, resize_percent_height, img_not_none):
        def add_par_thread():
            # Activate drawing with the resize percentages
            self.painter.activate_drawing(add_par_but_clicked=True, resize_percent_width=resize_percent_width, resize_percent_height=resize_percent_height)
            while self.painter.last_rectangle == {}:
                pass

            # Get the parameter name and position (already saved with original coordinates)
            par_name, par_pos = self.painter.last_rectangle.popitem()

            # Save parameter to config.json with the original image coordinates
            self.add_parameter_to_config(par_name, par_pos)

        if img_not_none:
            thread = threading.Thread(target=add_par_thread)
            thread.start()

    # Do the same for mode and feature
    def add_mode_feature_but_func_threaded(self, img_path, img_size, resize_percent_width, resize_percent_height, img_not_none):
        def add_mode_thread():
            # Activate drawing with the resize percentages
            self.painter.activate_drawing(add_feature_but_clicked=True, resize_percent_width=resize_percent_width, resize_percent_height=resize_percent_height)
            while self.painter.last_rectangle == {}:
                pass

            # Get the feature name and position (already saved with original coordinates)
            feature_name, feature_pos = self.painter.last_rectangle.popitem()

            # Save feature to config.json with the original image coordinates
            self.add_feature_to_config(feature_name, feature_pos)

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

    def add_feature_to_config(self, feature_name, feature_pos):
        """
        Adds a feature to the config.json file.
        """
        with open(self.mde_config_file_path, 'r') as file:
            config_data = json.load(file)

        # Assuming the last selected template is the current one
        current_template_id = str(len(config_data["images"]))

        # Add the feature to the selected template
        feature_id = str(len(config_data["images"][current_template_id]["features"]) + 1)
        config_data["images"][current_template_id]["features"][feature_id] = {
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
