import os
import threading
from tkinter import filedialog, messagebox
import cv2

from painter import Painter
from pattern_detection import ImageMatcher  # Import the ImageMatcher class
from helpers import (
    load_config_data,

  
    add_item_to_template,
    get_next_template_id,
    save_template_image)
from helpers import get_machine_status_from_temp_img_id

class ButtonFunctions:
    """
    The ButtonFunctions class handles the actions associated with the buttons in the GUI,
    such as loading images, adding parameters, and features.
    """

    def __init__(self, img_canvas, mde_config_dir, mde_config_file_name, templates_dir_name, config_tool):
        """
        Initializes the ButtonFunctions class.

        Parameters:
        - img_canvas (Canvas): The canvas where images and drawings are displayed.
        - mde_config_dir (str): Directory path for the configuration files.
        - mde_config_file_name (str): Name of the configuration file.
        - templates_dir_name (str): Name of the directory containing image templates.
        - config_tool (ConfigurationTool): Reference to the main ConfigurationTool instance.
        """
        self.img_canvas = img_canvas
        self.mde_config_dir = mde_config_dir
        self.mde_config_file_name = mde_config_file_name
        self.templates_dir_name = templates_dir_name

        self.mde_config_file_path = os.path.join(mde_config_dir, mde_config_file_name)
        self.templates_dir = os.path.join(mde_config_dir, templates_dir_name)
        self.config_tool = config_tool
        self.img_path = None  # Store the image path globally
        self.selected_key = None
        self.temp_img_id = None  # Initialize temp_img_id

        # Ensure the config directory, templates directory, and config.json file exist
        self.ensure_directories_and_config(
            mde_config_dir, self.templates_dir, self.mde_config_file_path
        )

        # Load configuration data once
      #  self.config_data = load_config_data(self.mde_config_file_path)
        # Use the config_data from config_tool
        self.config_data = config_tool.config_data

        # Threading lock for config_data
        self.config_data_lock = threading.Lock()

        # Create ImageMatcher object for image comparison
        self.matcher = ImageMatcher(mde_config_dir, mde_config_file_name, templates_dir_name)

        # Initialize the painter class
        #print(f"##################################self.config_data ={self.config_data}################################")
        self.painter = Painter(img_canvas, self.config_data)

    def ensure_directories_and_config(self, config_dir, templates_dir, config_file):
        """
        Ensure that the config directory, templates directory, and config.json file exist.
        Create them if they don't exist.

        Parameters:
        - config_dir (str): Path to the configuration directory.
        - templates_dir (str): Path to the templates directory.
        - config_file (str): Path to the configuration JSON file.
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
        Opens a file dialog for the user to select an image file.
        Processes the selected image to match with existing templates.

        Returns:
        - tuple: A tuple containing the image path and temporary image ID.
        """
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
        Draws rectangles and names/IDs of the parameters and features for the matched template,
        with different colors for parameters and features. The positions are scaled according to
        the resized image dimensions.

        Parameters:
        - resize_percent_width (float): Scaling factor for width.
        - resize_percent_height (float): Scaling factor for height.
        - param_color (str): Color for parameter rectangles.
        - feature_color (str): Color for feature rectangles.
        """
        # Use the Painter class to draw the parameters and features on the image
        self.painter.draw_rectangle(
            self.temp_img_id, resize_percent_width, resize_percent_height, param_color, feature_color
        )

    def add_template(self, img_path, img_size):
        """
        Adds the selected image as a new template in the config.json file.
        Returns the template ID to be used later when adding features.

        Parameters:
        - img_path (str): Path to the image file.
        - img_size (dict): Dictionary containing image width and height.

        Returns:
        - int: The new template ID.
        """
        # Get the selected key from the dropdown
       # selected_name = self.config_tool.selected_option.get()
        #self.selected_key = self.config_tool.name_to_key.get(selected_name, None)

        #if self.selected_key is None:
            # If no dropdown option is selected, change the dropdown field background to red
         #   self.config_tool.dropdown.config(foreground='black', background='red')
          #  return None
        #print(f"self.selected_key......................................................{self.selected_key}")
        # Reset the dropdown style if everything is fine
        #self.config_tool.dropdown.config(foreground='black', background='white')

        # Retrieve the range from choices_dict using the selected key
        #choices_dict = self.config_tool.choices_dict
        #image_id_range = choices_dict[self.selected_key]["range"]

        # Get the next template ID
        new_template_id = get_next_template_id(self.config_data)

        # Save the image to the templates directory
        template_image_name = save_template_image(img_path, self.templates_dir, new_template_id)

        # Add the template metadata to config_data
        self.config_data["images"][str(new_template_id)] = {
            "path": template_image_name,
            "size": {"width": img_size["width"], "height": img_size["height"]},
            "parameters": {},
            "features": {}
        }

        # Save the updated config_data to the file
       # save_config_data(config_data, self.mde_config_file_path)

        print(f"New template ID = {new_template_id}")
        self.temp_img_id = new_template_id  # Update self.temp_img_id

        # Synchronize with config_tool
        self.config_tool.temp_img_id = self.temp_img_id

        return new_template_id

    def add_parameter_threaded(self, resize_percent_width, resize_percent_height, box_color):
        """
        Adds a parameter to the image in a separate thread.

        Parameters:
        - resize_percent_width (float): Scaling factor for width.
        - resize_percent_height (float): Scaling factor for height.
        - box_color (str): Color for the parameter box.
        """

        def add_parameter_thread():
            print(f"[DEBUG] 'Add New Parameter' button clicked. self.temp_img_id = {self.temp_img_id}")
            if self.config_tool.original_image is None:
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
                self.add_parameter(self.temp_img_id, par_name, par_pos)
                print(f"[DEBUG] Parameter '{par_name}' added to template ID: {self.temp_img_id}")
                # Notify ConfigurationTool that parameter addition is complete
                self.config_tool.on_parameter_addition_complete()
            else:
                print("[ERROR] No valid template ID found for adding parameter.")

        thread = threading.Thread(target=add_parameter_thread)
        thread.start()

    def add_screen_feature_threaded(self, img_size, resize_percent_width, resize_percent_height, box_color):
        """
        Adds a screen feature to the image in a separate thread.

        Parameters:
        - img_size (dict): Dictionary containing image width and height.
        - resize_percent_width (float): Scaling factor for width.
        - resize_percent_height (float): Scaling factor for height.
        - box_color (str): Color for the feature box.
        """

        def add_screen_feature_thread():
            print("[DEBUG] 'Add Screen Feature' button clicked.")
            if not self.img_path:
                messagebox.showerror("Error", "Image path is not valid. Please select a valid image.")
                return

            # Activate drawing mode with the specific color for features
            self.painter.activate_drawing(
                add_screen_feature_but_clicked=True,
                resize_percent_width=resize_percent_width,
                resize_percent_height=resize_percent_height,
                box_color=box_color
            )

            while self.painter.last_rectangle == {}:
                pass

            # Get the feature name and position
            feature_name, feature_pos = self.painter.last_rectangle.popitem()
            if self.config_tool.temp_img_id is None:
                 print("[ERROR] Failed to add screen feature due to invalid template ID.")
                 return
            elif self.config_tool.temp_img_id == -1:
                 # Add new template and get its ID
                 self.config_tool.temp_img_id = self.add_template(self.img_path, img_size)
            print(f"[DEBUG][add_screen_feature_thread]  insert feature to the configuration ... self.config_tool.temp_img_id ={self.config_tool.temp_img_id}  feature_name={feature_name} ,feature_pos={feature_pos}")
            self.add_feature_to_config(self.config_tool.temp_img_id, feature_name, feature_pos)
            # Notify ConfigurationTool that screen feature addition is complete
            self.config_tool.on_screen_feature_addition_complete()
            '''if self.config_tool.temp_img_id is not None:
                if self.config_tool.temp_img_id == -1:
                    # Add new template and get its ID
                    self.config_tool.temp_img_id = self.add_template(self.img_path, img_size)
                print(f'+#++########+++++++++++++++#############+++++++++ self.config_tool.temp_img_id = {type(self.config_tool.temp_img_id)}')
                self.add_feature_to_config(self.config_tool.temp_img_id, feature_name, feature_pos)
                print(f"[DEBUG] Feature '{feature_name}' added to template ID: {self.config_tool.temp_img_id}")

                # Store the template_id (temp_img_id) in the config_tool for later use
                print(f"[DEBUG] Stored current template ID (temp_img_id): {self.config_tool.temp_img_id}")

                # Refresh/reload the config_data after adding the feature
                self.reload_config_data()
                print("[DEBUG] config_data reloaded after adding screen feature.")

                # Notify ConfigurationTool that screen feature addition is complete
                self.config_tool.on_screen_feature_addition_complete()
            else:
                print("[ERROR] Failed to add screen feature due to invalid template ID.")'''

        thread = threading.Thread(target=add_screen_feature_thread)
        thread.start()

    def add_parameter(self, template_id, par_name, par_pos):
        """
        Adds a parameter to the config.json file for the given template_id.

        Parameters:
        - template_id (str): The ID of the template.
        - par_name (str): The name of the parameter.
        - par_pos (dict): The position of the parameter.
        """
        config_data = self.config_data
 
        param_data = {"name": par_name, "position": par_pos}
        add_item_to_template(template_id, "parameters", param_data, config_data)
       # save_config_data(config_data, self.mde_config_file_path)

    def add_feature_to_config(self, template_id, feature_name, feature_pos):
        """
        Adds a feature to the config.json file for the given template_id.

        Parameters:
        - template_id (str): The ID of the template.
        - feature_name (str): The name of the feature.
        - feature_pos (dict): The position of the feature.
        """
        
  
        feature_data = {"name": feature_name, "position": feature_pos}
        add_item_to_template(template_id, "features", feature_data, self.config_data)
       # save_config_data(config_data, self.mde_config_file_path)

    def clear_canvas(self, img_canvas, img_item):
        """
        Clears the canvas except for the loaded image.

        Parameters:
        - img_canvas (Canvas): The canvas to clear.
        - img_item: The image item to keep.
        """
        self.config_tool.update_dropdown("")  # No valid status, clear the dropdown
        for item in img_canvas.find_all():
            if item != img_item:
                img_canvas.delete(item)

    def reload_config_data(self):
        """
        Reloads the configuration data from the JSON file.
        """
        self.config_data = load_config_data(self.mde_config_file_path)

    def reload_config(self):
        """
        Reloads the configuration by reinitializing the matcher, painter, and config_data.
        """
        # Reinitialize the matcher and painter
        self.matcher = ImageMatcher(
            self.mde_config_dir, self.mde_config_file_name, self.templates_dir_name
        )
        self.painter = Painter(self.img_canvas, self.mde_config_file_path)

        # Reload configuration data
        self.reload_config_data()