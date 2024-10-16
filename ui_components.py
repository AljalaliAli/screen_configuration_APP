import os
import json
from tkinter import *
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import threading

# Assuming ButtonFunctions, configure_style, and
# get_machine_status_from_temp_img_id are defined elsewhere
from button_actions import ButtonFunctions  # Ensure this import is correct
from styles import configure_style
from helpers import (
    get_machine_status_from_temp_img_id,
    get_parameters_and_features_by_id,load_config_data, save_config_data, has_config_changed
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

        # Initialize blinking variables
        self.blinking = False  # Indicates whether blinking is active
        self.blink_on = False  # Indicates current blink state
        self.image_selected = False  # Indicates whether an image is selected
        self.blink_id = None  # Holds the after id for cancelling blinking

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

        # Create the user interface
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
        Checks if the dropdown is empty and initiates blinking if necessary.
        """
        # Check if the in-memory config_data differs from the config file
        dropdown_value = self.selected_option.get().strip()
        config_changed = has_config_changed(self.config_data, self.mde_config_file_path)
        print(f'****************************************config_changed ={config_changed}********************************')
        print(f'****************************************self.image_selected ={self.image_selected}********************************')
        print(f'****************************************dropdown_value ={dropdown_value}********************************')
        if not self.image_selected:
            self.root.destroy()
        elif config_changed and dropdown_value=='':

            print("[DEBUG] Dropdown is empty. Initiating blinking.")
            self.start_blinking()  # Start the blinking effect
            messagebox.showwarning(
                "Incomplete Configuration",
                "Please select a machine status before exiting."
            )
            # Optionally, you can prevent closing by simply returning
           # return

        elif config_changed and dropdown_value!='':
            # Configuration has not changed, confirm exit without saving
            print("[DEBUG] Configuration has changed. save the change.") 
            save_config_data(self.config_data, self.mde_config_file_path)          
            self.root.destroy()
        elif not config_changed :
            print("[DEBUG] Configuration has changed. Prompting user for confirmation to exit without saving.")          
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

        # Add buttons and dropdown to the sidebar
        self.add_sidebar_widgets()

    def add_sidebar_widgets(self):
        """
        Adds widgets (buttons and dropdowns) to the sidebar.
        """
        # Create padding options for widgets in the sidebar
        pad_options = {'padx': 10, 'pady': 5}

        # Button to select an image
        select_img_but = Button(self.side_bar, text="Select Image",
                                command=self.select_image)
        select_img_but.pack(fill=X, **pad_options)

        # Button to add a new parameter
        self.add_par_but = Button(self.side_bar, text="Add New Parameter",
                                  command=self.add_parameter)
        self.add_par_but.pack(fill=X, **pad_options)
        self.add_par_but_default_bg = self.add_par_but.cget('bg')

        # Button to add screen feature
        self.add_screen_feature_but = Button(
            self.side_bar, text="Add Screen Feature",
            command=self.add_screen_feature
        )
        self.add_screen_feature_but.pack(fill=X, **pad_options)
        self.add_screen_feature_but_default_bg = \
            self.add_screen_feature_but.cget('bg')

        # Button to clear the canvas
        clear_canvas_but = Button(self.side_bar, text="Clear Canvas",
                                  command=self.clear_canvas)
        clear_canvas_but.pack(fill=X, **pad_options)

        # Button to delete features or parameters
        self.delete_items_but = Button(
            self.side_bar, text="Delete Features/Parameters",
            command=self.delete_items
        )
        self.delete_items_but.pack(fill=X, **pad_options)

        # Reset Button
        self.reset_but = Button(self.side_bar, text="Reset Template",
                                command=self.reset_template)
        self.reset_but.pack(fill=X, **pad_options)

        # Separator
        separator = Frame(self.side_bar, height=2, bd=1, relief=SUNKEN)
        separator.pack(fill=X, padx=5, pady=10)

        # LabelFrame to hold radio buttons with a title
        radio_label_frame = LabelFrame(
            self.side_bar,
            text="Machine Status from Combination",
            bg='#000',
            fg='white',
            padx=10,
            pady=10
        )
        radio_label_frame.pack(fill=X, padx=10, pady=5)

        # Variable to hold radio button selection
        self.status_choice = StringVar(value="No")  # Default to "No"

        # Radiobutton for "Yes"
        yes_radio = Radiobutton(
            radio_label_frame,
            text="Yes",
            variable=self.status_choice,
            value="Yes",
            bg='Black',
            fg='white',
            selectcolor='Black',
            command=self.on_status_choice
        )
        yes_radio.pack(anchor='w', pady=2)

        # Radiobutton for "No"
        no_radio = Radiobutton(
            radio_label_frame,
            text="No",
            variable=self.status_choice,
            value="No",
            bg='Black',
            fg='white',
            selectcolor='Black',
            command=self.on_status_choice
        )
        no_radio.pack(anchor='w', pady=2)

        # Dropdown list (Combobox) for selecting options
        options_list = [value['name']
                        for key, value in self.choices_dict.items()]
        self.name_to_key = {value['name']: key
                            for key, value in self.choices_dict.items()}
        self.selected_option = StringVar()

        # Create a frame to hold the label and Combobox
        self.dropdown_frame = Frame(self.side_bar, bg='#000')
        self.dropdown_frame.pack(fill=X, padx=10, pady=5)

        # Create the label for the dropdown inside the frame
        self.dropdown_label = Label(
            self.dropdown_frame, text="Select machine status",
            bg='#000', fg='white'
        )
        self.dropdown_label.pack(anchor='w')

        # Create dropdown (Combobox) with initial style
        self.dropdown = ttk.Combobox(
            self.dropdown_frame,
            textvariable=self.selected_option,
            values=options_list,
            state='readonly',
            style='Custom.TCombobox'
        )
        self.dropdown.pack(fill=X)

        # Bind dropdown selection to a function
        self.dropdown.bind("<<ComboboxSelected>>", self.on_option_select)

    # ----------------------------------
    # Event Handlers
    # ----------------------------------
    def on_status_choice(self):
        """
        Callback method when the radio button selection changes.
        Handles UI changes based on the selection.
        """
        choice = self.status_choice.get()
        if choice == "Yes":
            # Hide the dropdown
            self.dropdown_frame.pack_forget()
            # Open the parameter selection window
            self.open_parameter_window()
        else:
            # Show the dropdown
            self.dropdown_frame.pack(fill=X, padx=10, pady=5)
            # If the parameter window is open, close it
            if hasattr(self, 'param_window') and \
                    self.param_window.winfo_exists():
                self.param_window.destroy()

    def on_option_select(self, event):
        """
        Handles the selection from the dropdown list.

        Parameters:
        - event: The event object from the Combobox selection.
        """
        selected_name = self.selected_option.get()
        selected_key = self.name_to_key.get(selected_name, None)

        if selected_key is not None:
            # Stop blinking if active
            if self.blinking:
                self.stop_blinking()
        else:
            # Start blinking if image is selected
            if self.image_selected and not self.blinking:
                pass
                #self.start_blinking()

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
                self.update_dropdown(status_name)  # Update the dropdown with the status name
            else:
                self.update_dropdown('')
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

    # ----------------------------------
    # Parameter Management
    # ----------------------------------
    def add_parameter(self):
        """
        Adds a new parameter to the selected image.
        Draws a green rectangle when clicked.
        """
        # Get the selected key from the dropdown
        #selected_name = self.selected_option.get()
        #self.selected_status_key = self.name_to_key.get(selected_name, None)

        if hasattr(self, 'original_image') and self.original_image is not None:
            if self.but_functions.temp_img_id != -1:
               # if self.selected_status_key is not None:
                    # Change button background to indicate active state
                    self.add_par_but.config(bg='green')
                    self.but_functions.add_parameter_threaded(
                        resize_percent_width=self.resize_percent_width,
                        resize_percent_height=self.resize_percent_height,
                        box_color="#00FF00"  # Green color for parameter box
                    )
                #else:
                    # Warn the user if no valid option was selected
                 #   messagebox.showwarning("No Selection", "Please choose a potential machine status first.")
            else:
                messagebox.showwarning("No Screen Features", "Please add a screen feature first.")
        else:
            messagebox.showwarning("No Image", "Please load an image first.")

    def open_parameter_window(self):
        """
        Opens a new window to define machine status parameters
        with conditions.
        """
        par_data, _ = get_parameters_and_features_by_id(
            r'ConfigFiles\mde_config.json', self.but_functions.temp_img_id)
        self.parameters = [item['name'] for item in par_data.values()]

        # Prevent multiple instances
        if hasattr(self, 'param_window') and \
                self.param_window.winfo_exists():
            self.param_window.lift()
            return

        self.param_window = Toplevel(self.root)
        self.param_window.title("Define Machine Status Parameters")
        self.param_window.geometry("600x400")
        self.param_window.resizable(False, False)

        # List to keep track of condition groups
        self.condition_groups = []

        # Scrollable Frame
        container = ttk.Frame(self.param_window)
        canvas = Canvas(container)
        scrollbar = ttk.Scrollbar(container, orient="vertical",
                                  command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=self.scrollable_frame,
                             anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)

        container.pack(fill="both", expand=True)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Apply a consistent style
        style = ttk.Style()
        style.configure('TFrame', background='#f0f0f0')
        style.configure('TLabel', background='#f0f0f0',
                        font=('Arial', 10))
        style.configure('TCheckbutton', background='#f0f0f0',
                        font=('Arial', 10))
        style.configure('TEntry', font=('Arial', 10))
        style.configure('TButton', font=('Arial', 10))
        style.configure('TCombobox', font=('Arial', 10))

        # Get machine statuses from choices_dict
        self.machine_statuses = [value['name']
                                 for key, value in
                                 self.choices_dict.items()]

        # Add initial condition group
        self.add_condition_group()

        # Button Frame
        button_frame = ttk.Frame(self.param_window)
        button_frame.pack(pady=10)

        # Add Condition Group button
        add_condition_group_but = ttk.Button(
            button_frame, text="Add Condition Group",
            command=self.add_condition_group
        )
        add_condition_group_but.pack(side='left', padx=5)

        # Submit Button
        submit_but = ttk.Button(
            button_frame, text="Submit",
            command=self.submit_parameters
        )
        submit_but.pack(side='left', padx=5)

    def add_condition_group(self):
        """
        Adds a new condition group to the parameter window.
        Each group allows selecting machine status and adding
        condition rows connected with logical operators.
        """
        group = {}  # Dictionary to store group info

        # Frame for the group using standard Frame to support 'relief' and 'borderwidth'
        group_frame = Frame(self.scrollable_frame, relief='groove', borderwidth=2)
        group_frame.pack(fill='x', padx=10, pady=10, ipady=5, ipadx=5)

        # Store group frame before adding condition rows
        group['frame'] = group_frame

        # Machine status selection
        status_label = ttk.Label(group_frame, text="Machine Status:")
        status_label.pack(anchor='w')

        status_var = StringVar()
        status_dropdown = ttk.Combobox(
            group_frame,
            textvariable=status_var,
            values=self.machine_statuses,
            state='readonly',
            width=20
        )
        status_dropdown.pack(anchor='w', padx=5, pady=5)

        # Initialize group's condition rows list
        group['condition_rows'] = []

        # Function to add condition row within this group
        def add_condition_row_in_group():
            self.add_condition_row(group)

        # Add initial condition row
        add_condition_row_in_group()

        # Button to add condition row in the group
        add_condition_but = ttk.Button(
            group_frame, text="Add Condition",
            command=add_condition_row_in_group
        )
        add_condition_but.pack(anchor='w', padx=5, pady=5)

        # Store additional group info
        group['status_var'] = status_var

        # Append to the condition_groups list
        self.condition_groups.append(group)

    def add_condition_row(self, group):
        """
        Adds a new condition row to the specified group.
        Allows selecting any parameter from a dropdown list.
        """
        # Get the group's condition_rows list
        condition_rows = group['condition_rows']

        # If not the first condition, add a dropdown for logical operator
        if condition_rows:
            # Operator frame
            operator_frame = ttk.Frame(group['frame'])
            operator_frame.pack(fill='x', padx=10, pady=5)

            operator_label = ttk.Label(operator_frame, text="Operator:")
            operator_label.pack(side='left')

            operator_var = StringVar()
            operator_dropdown = ttk.Combobox(
                operator_frame,
                textvariable=operator_var,
                values=["AND", "OR"],
                state='readonly',
                width=5
            )
            operator_dropdown.current(0)  # Set default to "AND"
            operator_dropdown.pack(side='left', padx=10)

            # Store operator variable in the last condition
            condition_rows[-1]['operator_var'] = operator_var

        # Condition frame
        row_frame = ttk.Frame(group['frame'])
        row_frame.pack(fill='x', padx=10, pady=5)

        # Checkbox to enable/disable condition
        var_selected = IntVar(value=1)  # Default to selected
        chk = ttk.Checkbutton(row_frame, variable=var_selected)
        chk.pack(side='left', padx=(0, 5))

        # Dropdown for parameter name
        param_var = StringVar()
        param_dropdown = ttk.Combobox(
            row_frame,
            textvariable=param_var,
            values=self.parameters,
            state='readonly',
            width=15
        )

        if self.parameters:  # Only set current index if parameters
            param_dropdown.current(0)  # Set default to first parameter
        else:
            print("No parameters available for the dropdown.")

        param_dropdown.pack(side='left', padx=5)

        # Dropdown for operation
        operation_var = StringVar()
        operation_dropdown = ttk.Combobox(
            row_frame,
            textvariable=operation_var,
            values=["=", ">", "<", "<=", ">="],
            state='readonly',
            width=5
        )
        operation_dropdown.current(0)  # Set default to "="
        operation_dropdown.pack(side='left', padx=5)

        # Entry for parameter value
        entry = ttk.Entry(row_frame, width=10)
        entry.pack(side='left', padx=5)

        # Store variables
        condition = {
            'selected': var_selected,
            'param_var': param_var,
            'operation_var': operation_var,
            'value': entry,
        }
        condition_rows.append(condition)

    def submit_parameters(self):
        """
        Collects the selected parameters, their values, and operations
        from all condition groups.
        """
        all_selected_params = []
        for group in self.condition_groups:
            group_data = {}
            status_name = group['status_var'].get()
            if not status_name:
                messagebox.showwarning(
                    "Input Error",
                    "Please select a machine status for each group."
                )
                return
            group_data['status'] = status_name
            selected_params = []
            condition_rows = group['condition_rows']
            for idx, condition in enumerate(condition_rows):
                if condition['selected'].get() == 1:
                    param_name = condition['param_var'].get()
                    operation = condition['operation_var'].get()
                    value = condition['value'].get()
                    operator_var = condition.get('operator_var', None)
                    if not param_name or not operation or not value:
                        messagebox.showwarning(
                            "Input Error",
                            "Please ensure all fields are filled."
                        )
                        return
                    condition_dict = {
                        'param': param_name,
                        'operation': operation,
                        'value': value,
                    }
                    if idx > 0 and operator_var:
                        condition_dict['operator'] = operator_var.get()
                    selected_params.append(condition_dict)
            if not selected_params:
                messagebox.showwarning(
                    "No Selection",
                    "No parameters selected in one of the groups."
                )
                return
            group_data['conditions'] = selected_params
            all_selected_params.append(group_data)

        # Now process all_selected_params as needed
        print("All Selected Parameters:")
        for group_data in all_selected_params:
            print(f"Machine Status: {group_data['status']}")
            conditions = group_data['conditions']
            for i, cond in enumerate(conditions):
                if i > 0 and 'operator' in cond:
                    print(f"{cond['operator']} {cond['param']} "
                          f"{cond['operation']} {cond['value']}")
                else:
                    print(f"{cond['param']} {cond['operation']} "
                          f"{cond['value']}")
            print("---")

        # Integrate the selected parameters into your application logic here
        # For example, you might want to store them in config_data

        # Example Integration:
        with self.but_functions.config_data_lock:
            for group_data in all_selected_params:
                status_name = group_data['status']
                # Find the corresponding key
                status_key = self.name_to_key.get(status_name)
                if not status_key:
                    continue
                # Assume each status corresponds to a template; you might need to adjust based on your logic
                # For example, you might map status to a specific template_id
                # Here, we'll add parameters to the current temp_img_id
                
                if self.but_functions.temp_img_id is None:
                    continue
                for condition in group_data['conditions']:
                    param_name = condition['param']
                    param_pos = {}  # Define how to get position; this is just a placeholder
                    self.but_functions.add_parameter(template_id, param_name, param_pos)

        # Close the parameter window
        self.param_window.destroy()

    # ----------------------------------
    # Screen Feature Management
    # ----------------------------------
    def add_screen_feature(self):
        """
        Adds a new screen feature to the selected image.
        Draws a red rectangle when clicked.
        """
        # Get the selected key from the dropdown
        selected_name = self.selected_option.get()
        self.selected_status_key = self.name_to_key.get(selected_name, None)

        # Check if an image has been loaded
        if hasattr(self, 'original_image') and self.original_image is not None:
            #if self.selected_status_key is not None:
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
        #    else:
                # Warn the user if no valid option was selected
              #  messagebox.showwarning("No Selection", "Please choose a potential machine status first")
        else:
            # Warn the user if no image was loaded
            messagebox.showwarning("No Image", "Please load an image first.")

    # ----------------------------------
    # Deletion Management
    # ----------------------------------
    def delete_items(self):
        """
        Opens a dialog to select and delete features or parameters from the selected image.
        """
        if self.but_functions.temp_img_id is None:
            messagebox.showwarning("No Image Selected", "Please select an image first.")
            return

        # Open the delete dialog
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
            status_name, _ = self.status_info
            self.update_dropdown(status_name)

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
                print(f"[DEBUG] Deleted {item_type} with IDs {item_ids} from config_data.")
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

        # Confirm reset action
        result = messagebox.askyesno(
            "Confirm Reset",
            "Are you sure you want to reset this template? This will delete all associated data and the image file."
        )

        if result:
            # Delete from config_data
            self.delete_template_data()

            # Delete the image file
            self.delete_image_file()


            # Clear the canvas and reset variables
            self.clear_canvas()
            self.but_functions.temp_img_id = None
            self.selected_img_path = None
            self.original_image = None
            self.resized_img = None
            self.image_selected = False

            # Reset the dropdown and radio buttons
            self.status_choice.set("No")
            self.dropdown_frame.pack(fill=X, padx=10, pady=5)
            self.dropdown.set('')
            self.stop_blinking()

            # If the parameter window is open, close it
            if hasattr(self, 'param_window') and self.param_window.winfo_exists():
                self.param_window.destroy()

            # Reinitialize the matcher and painter
            self.but_functions.reload_config()

            messagebox.showinfo("Template Reset", "The template has been reset successfully.")

    def delete_template_data(self):
        """
        Deletes the template data from the config_data.
        """
        image_id = str(self.but_functions.temp_img_id)
        with self.but_functions.config_data_lock:
            if image_id in self.config_data['images']:
                del self.config_data['images'][image_id]
                #update the mde_config_file content
                save_config_data(self.config_data, self.mde_config_file_path)
                print(f"[DEBUG] Template data for image ID {image_id} deleted from config_data.")
            else:
                print(f"[DEBUG] Image ID {image_id} not found in config_data.")

    def delete_image_file(self):
        """
        Deletes the image file associated with the current template.
        """
        try:
            # The image is stored in the templates directory with a name like "template_{id}.png"
            template_image_name = f"template_{self.but_functions.temp_img_id}.png"
            template_image_path = os.path.join(self.but_functions.templates_dir, template_image_name)

            if os.path.exists(template_image_path):
                os.remove(template_image_path)
                print(f"[DEBUG] Image file {template_image_path} deleted.")
            else:
                print(f"[DEBUG] Image file {template_image_path} does not exist.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete image file: {e}")

    # ----------------------------------
    # Blinking Effect Management
    # ----------------------------------
    def start_blinking(self):
        """
        Starts the blinking effect on the dropdown frame to indicate attention is needed.
        """
        if not self.blinking:
            self.blinking = True
            self.blink_on = False
            self.blink_frame()
        else:
            print("[DEBUG] Blinking is already active.")

    def stop_blinking(self):
        """
        Stops the blinking effect on the dropdown frame.
        """
        if self.blinking:
            self.blinking = False
            if self.blink_id is not None:
                self.root.after_cancel(self.blink_id)
                self.blink_id = None
            # Ensure the frame background is set to normal
            self.dropdown_frame.configure(bg='#000')
        else:
            print("[DEBUG] Blinking is not active. No action taken.")

    def blink_frame(self):
        """
        Toggles the background color of the dropdown frame to create a blinking effect.
        """
        if self.blinking:
            if self.blink_on:
                # Set frame background color to red
                self.dropdown_frame.configure(bg='red')
            else:
                # Set frame background color to normal
                self.dropdown_frame.configure(bg='#000')
            self.blink_on = not self.blink_on
            # Schedule the next blink
            self.blink_id = self.root.after(500, self.blink_frame)

    # ----------------------------------
    # Configuration Management
    # ----------------------------------
    def update_dropdown(self, status_name):
        """
        Updates the dropdown list to display the given status name.

        If the status name is None or empty, it will clear the dropdown
        and set the background to red.
        If a status is provided, it will stop blinking and set the dropdown
        to the status.

        Parameters:
        - status_name (str): The machine status name to update the dropdown with.
        """
        print(f"[DEBUG] Called update_dropdown with status_name: "
              f"'{status_name}', image_selected: {self.image_selected}")

        if status_name:
            # Stop blinking if active and set the dropdown to the status name
            self.stop_blinking()
            if self.status_choice.get() == "No":
                self.dropdown.configure(state='normal')  # Change to 'normal' to update
                self.dropdown.set(status_name)  # Set the dropdown to the status name
                # Reset to normal style and 'readonly' state
                self.dropdown.configure(style='Custom.TCombobox', state='readonly')
        else:
            # No status found, clear the dropdown and initiate blinking if an image is selected
            if self.status_choice.get() == "No":
                self.dropdown.configure(state='normal')  # Change to 'normal' to update
                self.dropdown.set('')  # Clear the dropdown

                if self.image_selected:
                    print("[DEBUG] Image is selected and blinking is not active. Starting blinking.")
                    if not self.blinking:
                        pass
                        #self.start_blinking()  # Start the blinking effect if it’s not already active
                else:
                    print("[DEBUG] No image selected. Dropdown frame remains normal.")

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
