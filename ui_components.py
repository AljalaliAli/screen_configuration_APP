# ConfigurationTool.py

import os
import json
from tkinter import *
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import threading
from tkinter import Listbox, END
from MachineStatusConditionsManager import MachineStatusConditionsManager
from button_actions import ButtonFunctions  # Ensure this import is correct
from styles import configure_style
from helpers import (
    get_machine_status_from_temp_img_id,
    get_temp_img_details, load_config_data, save_config_data, has_config_changed
)


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

        self.selected_img_path = None  # Store the image path

        # Initialize the root window
        self.root = Tk()
        self.root.title('Configuration Tool')
        self.root.resizable(False, False)  # Disable window resizing

        # Get the screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Set the main window geometry to fit the screen, minus the taskbar
        self.root.geometry(f"{screen_width}x{screen_height - 40}")

        # Bind the on_closing method to the window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.sidebar_width = 200  # Fixed sidebar width

        # Initialize style
        self.style = ttk.Style()
        configure_style(self.style)  # Apply the styles defined in styles.py

        self.image_selected = False  # Indicates whether an image is selected

        self.resized_img = None
        self.original_image = None
        self.status_info = None

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
        self.config_data = load_config_data(self.mde_config_file_path)

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
        self.but_functions.config_data = self.config_data  # Share config_data
        self.but_functions.config_data_lock = threading.Lock()

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
        config_changed = has_config_changed(self.config_data, self.mde_config_file_path)

        if not self.image_selected:
            self.root.destroy()
        elif config_changed and not self.machine_status_conditions_manager.is_machine_status_defined:
            print(f"#####################>>>>>>>>{config_changed} and not {self.machine_status_conditions_manager.is_machine_status_defined}")
            messagebox.showwarning(
                "Incomplete Configuration",
                "Please select a machine status before exiting."
            )
        elif config_changed and self.machine_status_conditions_manager.is_machine_status_defined:
            print("[DEBUG] Configuration has changed. Saving the changes.")
            save_config_data(self.config_data, self.mde_config_file_path)
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

        # Button to add a new parameter
        self.add_par_but = Button(self.side_bar, text="Add New Parameter", command=self.add_parameter)
        self.add_par_but.pack(fill=X, **pad_options)
        self.add_par_but_default_bg = self.add_par_but.cget('bg')

        # Button to add screen feature
        self.add_screen_feature_but = Button(self.side_bar, text="Add Screen Feature", command=self.add_screen_feature)
        self.add_screen_feature_but.pack(fill=X, **pad_options)
        self.add_screen_feature_but_default_bg = self.add_screen_feature_but.cget('bg')

        # Button to clear the canvas
        clear_canvas_but = Button(self.side_bar, text="Clear Canvas", command=self.clear_canvas)
        clear_canvas_but.pack(fill=X, **pad_options)

        # Button to delete features or parameters
        self.delete_items_but = Button(self.side_bar, text="Delete Features/Parameters", command=self.delete_items)
        self.delete_items_but.pack(fill=X, **pad_options)

        # Reset Button
        self.reset_but = Button(self.side_bar, text="Reset Template", command=self.reset_template)
        self.reset_but.pack(fill=X, **pad_options)

        # Separator
        separator = Frame(self.side_bar, height=2, bd=1, relief=SUNKEN)
        separator.pack(fill=X, padx=5, pady=10)

        # Define machine status
        self.define_machine_status = Button(
            self.side_bar, text="Define Machine Status",
            command=lambda: self.machine_status_conditions_manager.define_machine_status(self.config_data)
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
        Resets the 'Add New Parameter' button background color after parameter addition is complete.
        """
        self.add_par_but.config(bg=self.add_par_but_default_bg)

    def on_screen_feature_addition_complete(self):
        """
        Resets the 'Add Screen Feature' button background color after screen feature addition is complete.
        """
        self.add_screen_feature_but.config(bg=self.add_screen_feature_but_default_bg)

    # ----------------------------------
    # Image Handling
    # ----------------------------------
    def select_image(self):
        """
        Handles the selection and loading of an image to the canvas.
        """
        image_data = self.but_functions.browse_files()
        if image_data:
            self.image_selected = True  # Set image_selected to True before loading the image
            self.selected_img_path = image_data[0]  # Store the image path
            self.load_image(image_data)  # Load the image first

            self.status_info = get_machine_status_from_temp_img_id(
                self.but_functions.temp_img_id)
            if self.status_info:
                status_name, _ = self.status_info
                self.update_possible_machine_status()
        else:
            print("[DEBUG] No image data retrieved.")

    def load_image(self, image_data):
        """
        Loads the selected image and sets it as the background of the canvas.

        Parameters:
        - image_data (tuple): A tuple containing the image path and image ID.
        """
        # Before loading the image, clear the canvas to ensure there are no rectangles or images
        self.clear_canvas()
        if image_data:
            selected_img_path, img_id = image_data
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
        self.possible_machine_status=[]
        self.machine_status_conditions_manager.machine_status_conditions = []
        self.update_possible_machine_status()
        self.dropdown_label.pack_forget()
        self.status_listbox.pack_forget()
    # ----------------------------------
    # Parameter Management
    # ----------------------------------
    def add_parameter(self):
        """
        Adds a new parameter to the selected image.
        Draws a green rectangle when clicked.
        """
        if hasattr(self, 'original_image') and self.original_image is not None:
            if self.but_functions.temp_img_id != -1:
                # Change button background to indicate active state
                self.add_par_but.config(bg='green')
                self.but_functions.add_parameter_threaded(
                    resize_percent_width=self.resize_percent_width,
                    resize_percent_height=self.resize_percent_height,
                    box_color="#00FF00"  # Green color for parameter box
                )
            else:
                messagebox.showwarning("No Screen Features", "Please add a screen feature first.")
        else:
            messagebox.showwarning("No Image", "Please load an image first.")

    # ----------------------------------
    # Screen Feature Management
    # ----------------------------------
    def add_screen_feature(self):
        """
        Adds a new screen feature to the selected image.
        Draws a red rectangle when clicked.
        """
        # Check if an image has been loaded
        if hasattr(self, 'original_image') and self.original_image is not None:
            img_size = {"width": self.original_image.width, "height": self.original_image.height}
            # Change button background to indicate active state
            self.add_screen_feature_but.config(bg='green')
            # Activate drawing with red color for screen features
            self.but_functions.add_screen_feature_threaded(
                img_size=img_size,
                resize_percent_width=self.resize_percent_width,
                resize_percent_height=self.resize_percent_height,
                box_color="#FF0000"  # Red color for feature box
            )
        else:
            # Warn the user if no image was loaded
            messagebox.showwarning("No Image", "Please load an image first.")

    # ----------------------------------
    # Deletion Management
    # ----------------------------------
    def delete_items(self):
        """
        Opens a dialog to select and delete features or parameters.
        """
        if self.but_functions.temp_img_id is None or self.but_functions.temp_img_id == -1:
            messagebox.showwarning("No Valid Image Selected", "There is no thing to delete!")
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
        # Access shared config_data with thread safety
        with self.but_functions.config_data_lock:
            data = self.config_data

        image_id = str(self.but_functions.temp_img_id)
        items = data['images'][image_id].get(item_type, {})
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
            self.load_image((self.selected_img_path, self.but_functions.temp_img_id))

    def delete_selected_items(self, item_type, item_ids):
        """
        Deletes the selected items from the in-memory config_data.

        Parameters:
        - item_type (str): Type of items to delete ('features' or 'parameters').
        - item_ids (list): List of item IDs to delete.
        """
        image_id = str(self.but_functions.temp_img_id)
        with self.but_functions.config_data_lock:
            if image_id in self.config_data['images']:
                for item_id in item_ids:
                    if item_id in self.config_data['images'][image_id][item_type]:
                        del self.config_data['images'][image_id][item_type][item_id]
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
            self.but_functions.reload_config()

            messagebox.showinfo("Template Reset", "The template has been reset successfully.")
            
    def delete_template_data(self):
        """
        Deletes the template data from the config_data.
        """
        image_id = str(self.but_functions.temp_img_id)
        if image_id != '-1':
            with self.but_functions.config_data_lock:
                if image_id in self.config_data['images']:
                    del self.config_data['images'][image_id]
                    save_config_data(self.config_data, self.mde_config_file_path)
        else:
            print("[DEBUG] Invalid temp_img_id (-1), no data to delete.")


    def delete_image_file(self):
        """
        Deletes the image file associated with the current template.
        """
        try:
            if self.but_functions.temp_img_id != -1:
                template_image_name = f"template_{self.but_functions.temp_img_id}.png"
                template_image_path = os.path.join(self.but_functions.templates_dir, template_image_name)

                if os.path.exists(template_image_path):
                    os.remove(template_image_path)
                else:
                    print(f"[DEBUG] Image file {template_image_path} does not exist.")
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
  
    def reload_config(self):
        """
        Reloads the config.json file after adding a new screen feature or parameter.
        """
        # Call reload_config method of ButtonFunctions
        self.but_functions.reload_config()
  
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
