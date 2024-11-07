# ui_components.py

import os
import json
import glob
from tkinter import *
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from tkinter import Listbox, END
from MachineStatusConditionsManager import MachineStatusConditionsManager
from button_actions import ButtonFunctions  # Ensure this import is correct
from styles import configure_style  # Import styles from styles.py
from helpers import (
    get_temp_img_details,
    list_machine_status_conditions,
    get_all_parameters_with_templates, remove_duplicate_dicts, make_hashable
)
from parameter_selection_dialog import open_parameter_selection_dialog
from config_manager import ConfigData

class ConfigurationTool:
    """
    The ConfigurationTool class represents a Tkinter-based GUI application
    for configuring images by adding parameters and screen features.
    It allows users to load images, annotate them with parameters and features,
    and manage templates.
    """

    # ----------------------------------
    # Initialization and UI Setup
    # ----------------------------------
    def __init__(self, mde_config_dir, mde_config_file_name,
                 templates_dir_name, choices_dict):
        """
        Initializes the ConfigurationTool application.

        Parameters:
        - mde_config_dir (str): Directory path for the configuration files.
        - mde_config_file_name (str): Name of the configuration file.
        - templates_dir_name (str): Name of the directory containing image templates.
        - choices_dict (dict): Dictionary of choices for machine statuses.
        """

        # Initialize configuration paths and data
        self.mde_config_dir = mde_config_dir
        self.mde_config_file_name = mde_config_file_name
        self.templates_dir_name = templates_dir_name
        self.choices_dict = choices_dict
        self.image_data = None
        self.selected_img_path = None  # Store the image path
        self.parametrs_suggestions_but_toggle = False
        # Initialize the root window
        self.root = Tk()
        self.root.title('Configuration Tool')
        self.root.resizable(False, False)  # Disable window resizing

        # Get the screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Set the main window geometry to fit the screen, minus the taskbar
        self.root.geometry(f"{int(screen_width - (screen_width * 0.05))}x{int(screen_height - (screen_height * 0.10))}")

        # Bind the on_closing method to the window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.sidebar_width = 200  # Fixed sidebar width

        # Initialize style
        self.style = ttk.Style()
        configure_style(self.style)  # Apply the styles defined in styles.py

        self.image_selected = False  # Indicates whether an image is selected

        self.resized_img = None
        self.original_image = None

        # Initialize parameters and machine statuses
        self.parameters = []
        self.machine_statuses = []

        # Ensure the config directory, templates directory, and config.json file exist
        self.ensure_directories_and_config(
            self.mde_config_dir,
            os.path.join(self.mde_config_dir, self.templates_dir_name),
            os.path.join(self.mde_config_dir, self.mde_config_file_name)
        )

        # Load configuration data once
        self.mde_config_file_path = os.path.join(mde_config_dir, mde_config_file_name)
        #self.config_data = load_config_data(self.mde_config_file_path)
        self.config= ConfigData(self.mde_config_file_path)
        self.config_data_1 = self.config.config_data

        # Create the user interface without adding sidebar widgets yet
        self.create_ui(screen_width, screen_height)

        # Initialize ButtonFunctions with img_canvas now that it's created
        self.but_functions = ButtonFunctions(
            img_canvas=self.img_canvas,  # Pass the initialized img_canvas
            mde_config_dir=self.mde_config_dir,
            mde_config_file_name=self.mde_config_file_name,
            templates_dir_name=self.templates_dir_name,
            config_tool=self
        )
       # self.but_functions.config_data = self.config_data  # Share config_data
      #  self.but_functions.config_data_lock = threading.Lock()

        # Define your default machine_status_conditions
        default_machine_status_conditions = None

        # Mock name_to_key if not provided
        self.name_to_key = {v['name']: k for k, v in choices_dict.items()} if choices_dict else {}

        # Initialize MachineStatusConditionsManager with the callback
        self.machine_status_conditions_manager = MachineStatusConditionsManager(
            title="Machine Status Conditions Manager",
            width=800,
            height=600,
            mde_config_file_path=self.mde_config_file_path,
            but_functions=self.but_functions,
            choices_dict=self.choices_dict,
            name_to_key=self.name_to_key,
            default_conditions=default_machine_status_conditions,
            on_submit_callback=self.update_possible_machine_status  # Pass the callback
        )

        # Now add the sidebar widgets since all dependencies are initialized
        self.add_sidebar_widgets()

        self.hide_parameters_and_features_toggle=False

    def reset_matcher_and_painter(self):
        """
        Reloads the config.json file after adding a new screen feature or parameter.
        """ 
        # Call reset_matcher_and_painter method of ButtonFunctions
        self.but_functions.reset_matcher_and_painter()
        
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

    def on_closing(self):
        """
        Handles the window close event.
        Prompts the user to save the configuration before exiting.
        """
        config_changed = self.config.has_config_changed()#has_config_changed(self.config_data, self.mde_config_file_path)
       # print(f'<o o>'*30)
        #print(f"[Debud] config_changed = {config_changed}")
        #print(f"[Debud] self.config_data_1 = {self.config_data_1}")
        #print(f'<o o>'*30)

        if not self.image_selected:
            self.root.destroy()

        elif config_changed and not list_machine_status_conditions(self.config_data_1, self.but_functions.temp_img_id):
            while True:
                response = messagebox.askyesno(
                    "Machine Status Required",
                    "Machine status is not defined. Would you like to define it now?"
                )

                if response:  # If user selects 'Yes'

                    break  # Exit the loop after defining the status
                else:  # If user selects 'No'
                    warning_response = messagebox.askyesno(
                        "Confirm Exit",
                        "If you proceed without defining the machine status, the screen feature for this image will not be saved. Do you want to continue?"
                    )
                    if warning_response:  # If they confirm they want to exit without saving
                        self.delete_image_file()
                        self.root.destroy()
                        break  # Exit the loop and proceed with exit
                    # Otherwise, the loop continues, asking the user again

        elif config_changed and list_machine_status_conditions(self.config_data_1, self.but_functions.temp_img_id):
            print("[DEBUG] Configuration has changed. Saving the changes.")
            self.config.save_config_data()
           # save_config_data(self.config_data, self.mde_config_file_path)
            self.root.destroy()
        elif not config_changed:
            print("[DEBUG] Configuration has not changed. Exiting without saving.")
            self.root.destroy()

    def create_ui(self, screen_width, screen_height):
        """
        Creates the user interface components of the application.

        Parameters:
        - screen_width (int): Width of the screen.
        - screen_height (int): Height of the screen.
        """
        # Main container that holds both the image and the sidebar
        self.main_container = Frame(self.root)
        self.main_container.pack(fill=BOTH, expand=1)

        # Create the Image Container
        img_container_width = screen_width - self.sidebar_width
        self.img_container = Frame(
            self.main_container, width=img_container_width,
            height=screen_height, bg='#4E4E6E'
        )
        self.img_container.pack(side=LEFT, fill=BOTH, expand=1)

        # Create the Canvas to display the image
        self.img_canvas = Canvas(self.img_container, bg='#4E4E6E',
                                 cursor="cross")
        self.img_canvas.pack(fill=BOTH, expand=1)

        # Create the Sidebar (right side)
        self.side_bar = Frame(self.main_container, width=self.sidebar_width,
                              bg='#000')
        self.side_bar.pack(side=RIGHT, fill=Y)

    def add_sidebar_widgets(self):
        """
        Adds widgets (buttons and dropdowns) to the sidebar.
        """

        # Create padding options for widgets in the sidebar
        pad_options = {'padx': 10, 'pady': 5}

        # Button to select an image
        select_img_but = Button(self.side_bar, text="Select Image", command=self.select_image)
        select_img_but.pack(fill=X, **pad_options)

        # Button to add screen feature
        self.add_screen_feature_but = Button(self.side_bar, text="Add Screen Feature", command=self.add_screen_feature)
        self.add_screen_feature_but.pack(fill=X, **pad_options)
        self.add_screen_feature_but_default_bg = self.add_screen_feature_but.cget('bg')

        # Button to add a new parameter
        self.add_par_but = Button(self.side_bar, text="Add New Parameter", command=self.add_parameter)
        self.add_par_but.pack(fill=X, **pad_options)
        self.add_par_but_default_bg = self.add_par_but.cget('bg')

        # Separator
        separator = Frame(self.side_bar, height=2, bd=1, relief=SUNKEN)
        separator.pack(fill=X, padx=5, pady=10)

        # Button to clear the canvas
      #  clear_canvas_but = Button(self.side_bar, text="Clear Canvas", command=self.clear_canvas)
       # clear_canvas_but.pack(fill=X, **pad_options)

        # Button to delete features or parameters
        self.delete_items_but = Button(self.side_bar, text="Delete Features/Parameters", command=self.delete_items)
        self.delete_items_but.pack(fill=X, **pad_options)

        # Reset Button
        self.reset_but = Button(self.side_bar, text="Reset Template", command=self.reset_template)
        self.reset_but.pack(fill=X, **pad_options)

        # Separator
        separator = Frame(self.side_bar, height=2, bd=1, relief=SUNKEN)
        separator.pack(fill=X, padx=5, pady=10)

        # Parameter Suggestions Button
        self.param_suggestions_but = Button(self.side_bar, text="Parameter Suggestions", command=self.parametrs_suggestions_but)
        self.param_suggestions_but.pack(fill=X, **pad_options)

        # Create the button
        self.hide_parameters_and_features_button = Button(self.side_bar, text="Hide Boxes", 
                                                          command=self.hide_parameters_and_features_but_fun)
        self.hide_parameters_and_features_button.pack(fill=X, **pad_options)
        # Separator
        separator = Frame(self.side_bar, height=2, bd=1, relief=SUNKEN)
        separator.pack(fill=X, padx=5, pady=10)

        # Define machine status
        self.define_machine_status = Button(
            self.side_bar, text="Define Machine Status",
            command=lambda: self.machine_status_conditions_manager.define_machine_status()
        )
        self.define_machine_status.pack(fill=X, **pad_options)

        # Separator for machine status labels
        separator_status = Frame(self.side_bar, height=2, bd=1, relief=SUNKEN)
        separator_status.pack(fill=X, padx=5, pady=10)

        # Label for the possible machine status list (Initially hidden)
        self.dropdown_label = Label(self.side_bar, text="Possible Machine Status", bg='#000', fg='white')
        self.dropdown_label.pack(fill=X, padx=5, pady=10)
        self.dropdown_label.pack_forget()  # Hide initially

        # Create a Listbox to display the machine status options
        self.status_listbox = Listbox(self.side_bar, height=5)
        self.status_listbox.pack(fill=X, padx=5, pady=10)
        self.status_listbox.pack_forget()  # Hide initially

    def on_parameter_addition_complete(self):
        """
        Resets the 'Add New Parameter' button background color after parameter addition is complete or canceled.
        """
        self.add_par_but.config(bg=self.add_par_but_default_bg)

    def on_screen_feature_addition_complete(self):
        """
        Resets the 'Add Screen Feature' button background color after screen feature addition is complete or canceled.
        """
        self.add_screen_feature_but.config(bg=self.add_screen_feature_but_default_bg)

    def activate_button(self, button_to_activate):
        """
        Activates the specified button by setting its background to green
        and deactivates the other button by resetting its background to default.
        """
        # Reset both buttons to their default background colors
        self.add_par_but.config(bg=self.add_par_but_default_bg)
        self.add_screen_feature_but.config(bg=self.add_screen_feature_but_default_bg)

        # Activate the clicked button by setting its background to green
        button_to_activate.config(bg='green')

    # ----------------------------------
    # Image Handling
    # ----------------------------------
    def select_image(self):
        """
        Handles the selection and loading of an image to the canvas.
        """
        # Ensure that the configuration for the current image is complete before selecting a new image.
        config_changed = self.config.has_config_changed() #has_config_changed(self.config_data, self.mde_config_file_path)
        print(f'[Debug] config_changed: {config_changed}')
        if config_changed:
            if config_changed and not list_machine_status_conditions(self.config_data_1, self.but_functions.temp_img_id):
                while True:
                    response = messagebox.askyesno(
                        "Machine Status Required",
                        "Machine status is not defined. Would you like to define it now?"
                    )

                    if response:  # If user selects 'Yes'

                        break  # Exit the loop after defining the status
                    else:  # If user selects 'No'
                        warning_response = messagebox.askyesno(
                            "Confirm Exit",
                            "If you proceed without defining the machine status, the screen feature for this image will not be saved. Do you want to continue?"
                        )
                        if warning_response:  # If they confirm they want to exit without saving
                            self.reset_matcher_and_painter()# reload the configuration 
                            
                            self.delete_image_file()# delete the image file
                            
                            self._load_and_update_image()
                            break  # Exit the loop and proceed with exit
                        # Otherwise, the loop continues, asking the user again

            elif config_changed and list_machine_status_conditions(self.config_data_1, self.but_functions.temp_img_id):
                print("[DEBUG] Configuration has changed. Saving the changes.")
                self.config.save_config_data()
                #save_config_data(self.config_data, self.mde_config_file_path)
                self._load_and_update_image()

        else:
          # self.but_functions.matcher.mde_config_data = self.config_data  # update the config_data in the matcher class
           self._load_and_update_image()

    def _load_and_update_image(self):
            
            self.image_data = self.but_functions.browse_files()
            if self.image_data:
                self.image_selected = True  # Set image_selected to True before loading the image
                self.selected_img_path = self.image_data[0]  # Store the image path
                
                self.but_functions.painter.rect_history = []
                self.load_image()  # Load the image first
                self.update_possible_machine_status()
            else:
                print("[DEBUG] No image data retrieved.")

    def load_image(self, draw_parameters_and_features=True):
        """
        Loads the selected image and sets it as the background of the canvas.

        Parameters:
        - self.image_data (tuple): A tuple containing the image path and image ID.
        """
        # Before loading the image, clear the canvas to ensure there are no rectangles or images
        self.clear_canvas()
        if self.image_data:
            selected_img_path, img_id = self.image_data
            try:
                # Open the image using PIL
                self.original_image = Image.open(selected_img_path)
                original_width, original_height = self.original_image.size  # Store original image size

                # Get canvas dimensions
                self.root.update_idletasks()  # Ensure canvas size is updated
                canvas_width = self.img_canvas.winfo_width()
                canvas_height = self.img_canvas.winfo_height()

                # Resize image to fit the canvas
                resized_image = self.original_image.resize((canvas_width, canvas_height))
                self.resized_img = ImageTk.PhotoImage(resized_image)

                # Set the image as the background of the canvas
                self.img_canvas.create_image(0, 0, anchor=NW, image=self.resized_img, tags="bg")

                # Ensure rectangles and other elements are drawn above the image
                self.img_canvas.tag_lower("bg")  # This ensures the image is in the background

                # Keep a reference to avoid garbage collection
                self.img_canvas.image = self.resized_img

                # Set the scroll region to match the image size and other canvas content
                self.img_canvas.config(scrollregion=self.img_canvas.bbox("all"))

                # Calculate the scaling factors based on the image resize
                self.resize_percent_width = canvas_width / original_width
                self.resize_percent_height = canvas_height / original_height
                if draw_parameters_and_features:
                    # Draw parameters (green) and features (red) with scaling
                    self.but_functions.draw_parameters_and_features(
                        self.resize_percent_width,
                        self.resize_percent_height,
                        param_color="#00ff00",
                        feature_color="#ff0000"
                    )

            except Exception as e:
                messagebox.showerror("Error", f"Failed to display image: {e}")
                print(f"[ERROR] Exception occurred while loading image: {e}")

    def clear_canvas(self):
        """
        Clears the canvas except for the background image.
        """
        self.but_functions.clear_canvas(self.img_canvas, "bg")

        # Clear machine status conditions
        self.possible_machine_status = []
        self.machine_status_conditions_manager.machine_status_conditions = []
        self.update_possible_machine_status()
        self.dropdown_label.pack_forget()
        self.status_listbox.pack_forget()

    # ----------------------------------
    # Parameter and Screen Feature Management
    # ----------------------------------
    def add_parameter(self):
        """
        Initiates the process to add a new parameter.
        Activates the 'Add New Parameter' button.
        """
        # Activate the 'Add New Parameter' button
        if self.but_functions.temp_img_id is None:
            messagebox.showwarning("Warning", "Select an image first then add screen feature then Parameter")
            return
        if self.but_functions.temp_img_id == -1:
            messagebox.showwarning("Warning", "Add a screen feature first")
            return
        self.activate_button(self.add_par_but)

        # Start the parameter addition process
        self.but_functions.add_parameter_threaded(
            resize_percent_width=self.resize_percent_width,
            resize_percent_height=self.resize_percent_height,
            box_color="#00FF00"  # Green color for parameter box
        )

    def add_screen_feature(self):
        """
        Initiates the process to add a new screen feature.
        Activates the 'Add Screen Feature' button.
        """
        if self.but_functions.temp_img_id is None:
            messagebox.showwarning("Warning", "Select an image first ")
            return
        # Activate the 'Add Screen Feature' button
        self.activate_button(self.add_screen_feature_but)

        # Start the screen feature addition process
        self.but_functions.add_screen_feature_threaded(
            img_size={"width": self.original_image.width, "height": self.original_image.height},
            resize_percent_width=self.resize_percent_width,
            resize_percent_height=self.resize_percent_height,
            box_color="#FF0000"  # Red color for feature box
        )

    def parametrs_suggestions_but(self):
        """
        Suggests parameters by highlighting them on the image.
        Toggles the parameter selection dialog window: opens it if it's closed,
        and closes it if it's open.
        """
        # Check preconditions before proceeding
        if not self._validate_preconditions():
            return

        # If the dialog is already open, close it
        if self._is_dialog_open():
            self._close_dialog()
            return

        # Retrieve unused parameters and open the selection dialog
        unused_parameters = self._get_unused_parameters()
        if not unused_parameters:
            messagebox.showinfo("No Unused Parameters", "All parameters are already used in the current template.")
            return

        # Open the parameter selection dialog with unused parameters
        self._open_parameter_selection_dialog(unused_parameters)

    # Helper methods to modularize the main function
    def _validate_preconditions(self):
        """
        Validates the preconditions to ensure an image and screen feature have been selected.
        """
        if self.but_functions.temp_img_id is None:
            messagebox.showwarning("Warning", "Select an image first, then add a screen feature, then add parameters.")
            return False
        if self.but_functions.temp_img_id == -1:
            messagebox.showwarning("Warning", "Add a screen feature first.")
            return False
        return True

    def _is_dialog_open(self):
        """
        Checks if the parameter selection dialog is currently open.
        """
        return hasattr(self, 'parameter_selection_dialog') and self.parameter_selection_dialog is not None

    def _close_dialog(self):
        """
        Closes the parameter selection dialog and resets relevant states.
        """
        self.parameter_selection_dialog.destroy()
        self.parameter_selection_dialog = None
        self.but_functions.painter.rect_history = []
        self.load_image()  # Reload the image  
        self.update_possible_machine_status()  # Update machine status information

    def _get_unused_parameters(self):
        """
        Retrieves the list of parameters that are not used in the current template.
        """
        print(f"[Debug] _get_unused_parameters called!")
        # Retrieve all parameters from self.config_data, including template IDs
        all_parameters_dicts_list = get_all_parameters_with_templates(self.config_data_1)

        # Retrieve parameters used in the current template
        current_template_parameters, _, _, _, _ = get_temp_img_details(
            self.config_data_1, self.but_functions.temp_img_id
        )

        # Convert current template parameters to a list of dictionaries
        current_template_parameters_dics_list = list(current_template_parameters.values())

        # Create a set of hashable representations of current template parameters
        current_params_set = set(make_hashable(param) for param in current_template_parameters_dics_list)

        # Find parameters that are not used in the current template
        unused_parameters_dics_list = []
        for param in all_parameters_dicts_list:
            # Remove 'template_id' before comparison to avoid mismatches
            param_without_template_id = param.copy()
            param_without_template_id.pop('template_id', None)
            hashable_param = make_hashable(param_without_template_id)
            if hashable_param not in current_params_set:
                unused_parameters_dics_list.append(param)

        # Remove duplicate parameter dictionaries before returning
        return remove_duplicate_dicts(unused_parameters_dics_list)

    def _open_parameter_selection_dialog(self, unused_parameters):
        """
        Opens the parameter selection dialog with the list of unused parameters.
        """
        self.parameter_selection_dialog = open_parameter_selection_dialog(
            self.root,
            unused_parameters,
            self.but_functions,
            self.resize_percent_width,
            self.resize_percent_height,
            self.suggested_parameter_click_action
        )

    # ----------------------------------
    # Suggested Parameter Click Action  #################### move it to button_actions module
    # ----------------------------------
    def suggested_parameter_click_action(self, name, position, toggle_state):
        """
        Action to execute when a suggested parameter rectangle is clicked,
        allowing for custom behavior based on its toggle state.

        :param name: Name of the parameter
        :param position: Position dictionary {'x1', 'y1', 'x2', 'y2'}
        :param toggle_state: Boolean indicating the new toggle state
        """
                # Calculate original position
         
        x1_orig = float(position['x1'])  
        y1_orig = float(position['y1'])  
        x2_orig = float(position['x2'])  
        y2_orig = float(position['y2'])  

        position = {'x1': x1_orig, 'y1': y1_orig, 'x2': x2_orig, 'y2': y2_orig}
        print(f"{'Selected' if toggle_state else 'Deselected'} suggested parameter '{name}' at {position}")
        # Implement your custom behavior here

    # ----------------------------------
    # Deletion Management
    # ----------------------------------
    def delete_items(self):
        """
        Opens a dialog to select and delete features or parameters.
        """
        if self.but_functions.temp_img_id is None or self.but_functions.temp_img_id == -1:
            messagebox.showwarning("No Valid Image Selected", "There is nothing to delete!")
            return

        self.open_delete_dialog()
    
    def open_delete_dialog(self):
        """
        Opens a dialog window for deleting features or parameters.
        """
        # Create a new Toplevel window
        delete_window = Toplevel(self.root)
        delete_window.title("Delete Features/Parameters")
        delete_window.geometry("400x400")

        # Create radio buttons to select between Features and Parameters
        choice_var = StringVar(value="features")
        features_radio = Radiobutton(delete_window, text="Features", variable=choice_var, value="features")
        parameters_radio = Radiobutton(delete_window, text="Parameters", variable=choice_var, value="parameters")
        features_radio.pack(anchor=W)
        parameters_radio.pack(anchor=W)

        # Button to load the items
        load_button = Button(
            delete_window, text="Load Items",
            command=lambda: self.load_items(delete_window, choice_var.get())
        )
        load_button.pack(pady=10)

    def load_items(self, window, item_type):
        """
        Loads items (features or parameters) from the JSON configuration and displays them
        with checkboxes in the provided window for selection.

        Parameters:
        - window: The Toplevel window where items are displayed.
        - item_type (str): Type of items to load ('features' or 'parameters').
        """
        # Clear any existing widgets in the window
        for widget in window.winfo_children():
            widget.destroy()

        # Recreate the radio buttons
        choice_var = StringVar(value=item_type)
        features_radio = Radiobutton(window, text="Features", variable=choice_var, value="features")
        parameters_radio = Radiobutton(window, text="Parameters", variable=choice_var, value="parameters")
        features_radio.pack(anchor=W)
        parameters_radio.pack(anchor=W)

        # Button to load the items again if selection changes
        load_button = Button(
            window, text="Load Items",
            command=lambda: self.load_items(window, choice_var.get())
        )
        load_button.pack(pady=10)

        # Get the items from the JSON file
        items = self.get_items(item_type)

        if not items:
            messagebox.showinfo("No Items", f"No {item_type.capitalize()} found in the selected image.")
            window.destroy()
            return

        # Display the items with checkboxes
        Label(window, text=f"Select {item_type.capitalize()} to delete:").pack()

        item_vars = {}
        for item_id, item_info in items.items():
            var = BooleanVar()
            item_text = f"ID: {item_id}, Name: {item_info.get('name', 'N/A')}"
            chk = Checkbutton(window, text=item_text, variable=var)
            chk.pack(anchor=W)
            item_vars[item_id] = var

        # Button to delete selected items
        delete_button = Button(
            window, text="Delete Selected",
            command=lambda: self.confirm_delete(window, item_type, item_vars)
        )
        delete_button.pack(pady=10)

    def get_items(self, item_type):
        """
        Retrieves items of the specified type from the JSON configuration.

        Parameters:
        - item_type (str): Type of items to retrieve ('features' or 'parameters').

        Returns:
        - dict: A dictionary of items from the configuration.
        """
        image_id = str(self.but_functions.temp_img_id)
        items = self.config_data_1['images'][image_id].get(item_type, {})
        return items

    def confirm_delete(self, window, item_type, item_vars):
        """
        Confirms deletion of selected items and performs the deletion if confirmed.

        Parameters:
        - window: The Toplevel window where items are displayed.
        - item_type (str): Type of items to delete ('features' or 'parameters').
        - item_vars (dict): Dictionary of item IDs and their associated BooleanVars indicating selection.
        """
        # Get the selected item IDs
        selected_ids = [item_id for item_id, var in item_vars.items() if var.get()]

        if not selected_ids:
            messagebox.showinfo("No Selection", "No items selected to delete.")
            return

        # Confirm deletion
        result = messagebox.askyesno(
            "Confirm Deletion", f"Are you sure you want to delete the selected {item_type}?"
        )

        if result:
            # Perform deletion
            self.delete_selected_items(item_type, selected_ids)
            messagebox.showinfo("Deleted", "Selected items have been deleted.")
            window.destroy()

            # Redraw the image to reflect changes
            if self.selected_img_path and self.but_functions.temp_img_id: #after deleting check this condition
                self.but_functions.painter.rect_history = []
                self.load_image()
                self.update_possible_machine_status()
           
    def cleanup_image_deletion(self, image_id):
        """
        Cleans up all data related to an image after its features are deleted.

        Parameters:
        - image_id (str): The ID of the image to clean up.
        """
        # Delete the image entry from config_data
        del self.config_data_1['images'][image_id]       
        # Delete the physical image file
        self.delete_image_file()
        
        # Clear the canvas and reset variables
        self.clear_canvas()
        self.but_functions.temp_img_id = None
        self.selected_img_path = None
        self.original_image = None
        self.resized_img = None
        self.image_selected = False

        ##save the change to the configuration file
       # save_config_data(self.config_data, self.mde_config_file_path)
        self.config.save_config_data()
        # Reinitialize the matcher and painter
       # self.but_functions.reload_config()
        self.reset_matcher_and_painter()

    def delete_selected_items(self, item_type, item_ids):
        """
        Deletes the selected items from the in-memory config_data.

        Parameters:
        - item_type (str): Type of items to delete ('features' or 'parameters').
        - item_ids (list): List of item IDs to delete.
        """
        image_id = str(self.but_functions.temp_img_id)
       # with self.but_functions.config_data_lock:
        if image_id in self.config_data_1['images']:
            for item_id in item_ids:
                if item_id in self.config_data_1['images'][image_id][item_type]:
                    del self.config_data_1['images'][image_id][item_type][item_id]
                    ## if the temlate image has no features more delete every thing related to it
                    if self.config_data_1['images'][image_id]['features'] is None or not  self.config_data_1['images'][image_id]['features'] : 
                            self.cleanup_image_deletion(image_id) # inside thhis functio the change in the configuration will also be saved
                    else:    
                        ##save the change to the configuration file
                        #save_config_data(self.config_data, self.mde_config_file_path)
                        self.config.save_config_data()
                            
        else:
            print(f"[DEBUG] Image ID {image_id} not found in config_data.")

    # ----------------------------------
    # Template Reset Management
    # ----------------------------------
    def reset_template(self):
        """
        Deletes the current image template data from the config.json and deletes the image file.
        """
        if self.but_functions.temp_img_id is None or self.selected_img_path is None:
            messagebox.showwarning("No Image Selected", "Please select an image first.")
            return
        
        if self.but_functions.temp_img_id == -1:
            #messagebox.showwarning("")
            return

        # Confirm reset action
        result = messagebox.askyesno(
            "Confirm Reset",
            "Are you sure you want to reset this template? This will delete all associated data and the image file."
        )

        if result:
            # Delete the image file
            self.delete_image_file()   
            # Delete from config_data
            self.delete_template_data()
            # Clear the canvas and reset variables
            self.clear_canvas()
            self.but_functions.temp_img_id = None
            self.selected_img_path = None
            self.original_image = None
            self.resized_img = None
            self.image_selected = False

            # Clear machine status conditions
            self.machine_status_conditions_manager.machine_status_conditions = []
            self.update_possible_machine_status()

            # Reinitialize the matcher and painter
            #self.config_data= self.but_functions.reload_config()
            self.reset_matcher_and_painter()
            print(f'<Debug> self.config_data_1: {self.config_data_1}')

            messagebox.showinfo("Template Reset", "The template has been reset successfully.")

    def hide_parameters_and_features_but_fun(self):
        if self.but_functions.temp_img_id is None:
           # messagebox.showwarning("Warning", "Select an image first then add screen feature then Parameter")
            return
        if self.but_functions.temp_img_id == -1:
           # messagebox.showwarning("Warning", "Add a screen feature first")
            return
        # Toggle the state
        self.hide_parameters_and_features_toggle = not self.hide_parameters_and_features_toggle
       # print(f'<o o>'*30)
        #print(f"self.but_functions.temp_img_id:{self.but_functions.temp_img_id}, self.but_functions.painter.rect_history: ")
        #print(f'<o o>'*30)
        # Check the state and update button properties
        if self.hide_parameters_and_features_toggle:
            self.hide_parameters_and_features_button.config(text="Display Boxes", bg="green")
            self.but_functions.painter.rect_history = []
            self.load_image(draw_parameters_and_features=False)  # Load the image first
            self.update_possible_machine_status()
        else:
            self.hide_parameters_and_features_button.config(text="Hide Boxes", bg=self.hide_parameters_and_features_button.cget("highlightbackground"))
            self.load_image(draw_parameters_and_features=True)
            '''self.but_functions.draw_parameters_and_features(
                self.resize_percent_width,
                self.resize_percent_height,
                param_color="#00ff00",
                feature_color="#ff0000"
            )'''
        
    def delete_template_data(self):
        """
        Deletes the template data from the config_data.
        """
        image_id = str(self.but_functions.temp_img_id)
        if image_id != '-1':
           # with self.but_functions.config_data_lock:
            if image_id in self.config_data_1['images']:
                del self.config_data_1['images'][image_id]
                # save_config_data(self.config_data, self.mde_config_file_path)
                self.config.save_config_data()
        else:
            print("[DEBUG] Invalid temp_img_id (-1), no data to delete.")

    def delete_image_file(self):
        """
        Deletes the image file associated with the current template.
        Supports multiple image formats (e.g., tiff, jpg, png).
        """
        try:
            if self.but_functions.temp_img_id != -1:
                # Use glob to match any image file with the template ID
                template_image_pattern = f"template_{self.but_functions.temp_img_id}.*"
                template_image_path_pattern = os.path.join(self.but_functions.templates_dir, template_image_pattern)
                
                # Get all matching image files (e.g., tiff, jpg, png)
                matching_files = glob.glob(template_image_path_pattern)
                
                if matching_files:
                    for file_path in matching_files:
                        os.remove(file_path)
                        print(f"[DEBUG] Deleted image file: {file_path}")
                else:
                    print(f"[DEBUG] No matching image files found for pattern: {template_image_path_pattern}")
            else:
                print("[DEBUG] Invalid temp_img_id (-1), no image file to delete.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete image file: {e}")

    def update_possible_machine_status(self):
        """
        Fetches machine status options from the configuration file and updates
        the self.possible_machine_status list and the Listbox.
        Handles special characters like German umlauts correctly.
        """
        # Fetch machine status conditions from the configuration
        print(f"[Debug] update_possible_machine_status called!")
        _, _, self.machine_status_conditions_manager.machine_status_conditions, _, _ = get_temp_img_details(
            self.mde_config_file_path, self.but_functions.temp_img_id
        )

        # Update possible_machine_status based on the fetched machine status conditions
        self.possible_machine_status = [condition['status'] for condition in
                                        self.machine_status_conditions_manager.machine_status_conditions]

        if self.possible_machine_status:
            # The list has elements, show the label and listbox
            self.dropdown_label.pack(fill=X, padx=5, pady=10)
            self.status_listbox.pack(fill=X, padx=5, pady=10)

            # Clear the current listbox contents
            self.status_listbox.delete(0, END)

            # Insert the new statuses into the Listbox (German characters included)
            for status in self.possible_machine_status:
                self.status_listbox.insert(END, status)

            # Adjust the Listbox height based on the number of statuses (limit to 5 for display)
            listbox_height = min(len(self.possible_machine_status), 5)
            self.status_listbox.config(height=listbox_height)
        else:
            # The list is empty, hide the label and listbox
            self.dropdown_label.pack_forget()
            self.status_listbox.pack_forget()
  

    # ----------------------------------
    # Main Event Loop
    # ----------------------------------
    def mainloop(self):
        """
        Starts the Tkinter main event loop.
        """
        self.root.mainloop()


# Example usage
if __name__ == "__main__":
    # Mock choices_dict and name_to_key
    choices_dict = {
        'status1': {'name': 'Produktiv im Automatikbetrieb'},
        'status2': {'name': 'Läuft nicht'}
    }
    name_to_key = {
        'Produktiv im Automatikbetrieb': 'status1',
        'Läuft nicht': 'status2'
    }

    # Initialize ConfigurationTool with appropriate paths and dictionaries
    config_tool = ConfigurationTool(
        mde_config_dir="path/to/mde_config_dir",
        mde_config_file_name="mde_config.json",
        templates_dir_name="templates",
        choices_dict=choices_dict
    )

    # Start the Tkinter event loop
    config_tool.mainloop()

    # After the window is closed, you can access the updated conditions
    print("Final machine_status_conditions:")
    print(json.dumps(config_tool.machine_status_conditions_manager.machine_status_conditions, indent=4,
                     ensure_ascii=False))