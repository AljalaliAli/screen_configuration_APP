from tkinter import *
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from button_actions import ButtonFunctions
from styles import configure_style  # Import the style configuration function
from helpers import get_machine_status_from_temp_img_id

class ConfigurationTool:
    def __init__(self, mde_config_dir, mde_config_file_name, templates_dir_name, choices_dict):
        self.mde_config_dir = mde_config_dir
        self.mde_config_file_name = mde_config_file_name
        self.templates_dir_name = templates_dir_name
        self.choices_dict = choices_dict
        self.blinking_active = False  # Initialize blinking state
        self.current_template_id = None  # Store the template ID (temp_img_id)

        # Initialize the root window
        self.root = Tk()
        self.root.title('Configuration Tool')

        # Disable window resizing
        self.root.resizable(False, False)

        # Get the screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Set the main window geometry to fit the screen, minus the taskbar (with a small margin)
        self.root.geometry(f"{screen_width}x{screen_height-40}")  # full screen minus a margin

        self.sidebar_width = 200  # Fixed sidebar width

        # Initialize style
        self.style = ttk.Style()
        configure_style(self.style)  # Apply the styles defined in styles.py
       # print("[DEBUG] Styles configured using 'styles.py'.")

        # Initialize blinking variables
        self.blinking = False  # Indicates whether blinking is active
        self.blink_on = False  # Indicates current blink state
        self.image_selected = False  # Indicates whether an image is selected
        self.blink_id = None  # Holds the after id for cancelling blinking

        self.resized_img= None
        self.original_image= None
        self.status_info=None
        self.create_ui(screen_width, screen_height)
    
    def get_current_template_id(self): 
        """
        Retrieves the current template ID based on temp_img_id or dropdown selection.
        """
        if self.current_template_id:
            # print("[DEBUG] Retrieved stored template ID (temp_img_id): {self.current_template_id}")
            return self.current_template_id
        
        # Fallback to using dropdown selection if no temp_img_id is available
        selected_name = self.selected_option.get()  # Get the current dropdown selection
        selected_key = self.name_to_key.get(selected_name, None)  # Map name to key (template ID)
        
        if selected_key is not None:
            # print("[DEBUG] Retrieved template ID from dropdown: {selected_key}")
            return selected_key
        else:
            print("[ERROR] No valid template ID found from the dropdown or temp_img_id.")
            return None
    def create_ui(self, screen_width, screen_height):
        # Main container that holds both the image and the sidebar
        self.main_container = Frame(self.root)
        self.main_container.pack(fill=BOTH, expand=1)
       # print("[DEBUG] Main container created.")

        # Create the Image Container (left side, takes the remaining screen width after sidebar)
        img_container_width = screen_width - self.sidebar_width
        self.img_container = Frame(self.main_container, width=img_container_width, height=screen_height, bg='#4E4E6E')
        self.img_container.pack(side=LEFT, fill=BOTH, expand=1)
       # print("[DEBUG] Image container created with width:", img_container_width)

        # Create the Canvas to display the image
        self.img_canvas = Canvas(self.img_container, bg='#4E4E6E', cursor="cross")
        self.img_canvas.pack(fill=BOTH, expand=1)
       # print("[DEBUG] Image canvas created.")

        # Pass self to ButtonFunctions
        self.but_functions = ButtonFunctions(self.img_canvas, self.mde_config_dir, self.mde_config_file_name, self.templates_dir_name, self)
       # print("[DEBUG] ButtonFunctions initialized.")

        # Create the Sidebar (right side)
        self.side_bar = Frame(self.main_container, width=self.sidebar_width, bg='#000')
        self.side_bar.pack(side=RIGHT, fill=Y)
       # print("[DEBUG] Sidebar created with width:", self.sidebar_width)

        # Add buttons and dropdown to the sidebar
        self.add_sidebar_widgets()

    def add_sidebar_widgets(self):
        # Create padding for widgets in the sidebar
        pad_options = {'padx': 10, 'pady': 5}
       # print("[DEBUG] Adding sidebar widgets.")

        # Button to select an image
        select_img_but = Button(self.side_bar, text="Select Image", command=self.select_image)
        select_img_but.pack(fill=X, **pad_options)
       # print("[DEBUG] 'Select Image' button added.")

        # Button to add a new parameter
        add_par_but = Button(self.side_bar, text="Add New Parameter", command=self.add_parameter)
        add_par_but.pack(fill=X, **pad_options)
       # print("[DEBUG] 'Add New Parameter' button added.")

        # Button to add screen feature
        add_screen_feature_but = Button(self.side_bar, text="Add Screen Feature", command=self.add_screen_feature)
        add_screen_feature_but.pack(fill=X, **pad_options)
       # print("[DEBUG] 'Add Screen Feature' button added.")

        # Button to clear the canvas
        clear_canvas_but = Button(self.side_bar, text="Clear Canvas", command=self.clear_canvas)
        clear_canvas_but.pack(fill=X, **pad_options)
       # print("[DEBUG] 'Clear Canvas' button added.")

        # Separator
        separator = Frame(self.side_bar, height=2, bd=1, relief=SUNKEN)
        separator.pack(fill=X, padx=5, pady=10)
       # print("[DEBUG] Separator added to sidebar.")

        # Dropdown list (Combobox) for selecting options
        options_list = [value['name'] for key, value in self.choices_dict.items()]
        self.name_to_key = {value['name']: key for key, value in self.choices_dict.items()}
        self.selected_option = StringVar()
       # print("[DEBUG] Dropdown options loaded:", options_list)

        # Create a frame to hold the label and Combobox
        self.dropdown_frame = Frame(self.side_bar, bg='#000')
        self.dropdown_frame.pack(fill=X, padx=10, pady=5)
       # print("[DEBUG] Dropdown frame created.")

        # Create the label for the dropdown inside the frame
        self.dropdown_label = Label(self.dropdown_frame, text="Select machine status", bg='#000', fg='white')
        self.dropdown_label.pack(anchor='w')
       # print("[DEBUG] Dropdown label added.")

        # Create dropdown (Combobox) with initial style
        self.dropdown = ttk.Combobox(
            self.dropdown_frame,
            textvariable=self.selected_option,
            values=options_list,
            state='readonly',  # Start in readonly state
            style='Custom.TCombobox'  # Set initial style
        )
        self.dropdown.pack(fill=X)
       # print("[DEBUG] Combobox created with 'Custom.TCombobox' style.")

        # Bind dropdown selection to a function
        self.dropdown.bind("<<ComboboxSelected>>", self.on_option_select)
       # print("[DEBUG] Combobox selection event bound to 'on_option_select'.")

    def update_dropdown(self, status_name):
        """
        Updates the dropdown list to display the given status name.
        If the status name is None or empty, it will clear the dropdown and set the background to red.
        If a status is provided, it will stop blinking and set the dropdown to the status.
        """
        print(f"[DEBUG..............update_dropdown (f)......] Called update_dropdown with status_name: '{status_name}', image_selected: {self.image_selected}")  # Debug statement

        if status_name:
            # Stop blinking if active and set the dropdown to the status name
            self.stop_blinking()
            self.dropdown.configure(state='normal')  # Change to 'normal' to update
            self.dropdown.set(status_name)  # Set the dropdown to the status name
            self.dropdown.configure(style='Custom.TCombobox', state='readonly')  # Reset to normal style and 'readonly' state
            #print(f"[DEBUG..............update_dropdown (f)......] Dropdown set to: {status_name}. Blinking stopped if it was active.")  # Debug statement
        else:
            # No status found, clear the dropdown and initiate blinking if an image is selected
            self.dropdown.configure(state='normal')  # Change to 'normal' to update
            self.dropdown.set('')  # Clear the dropdown
            #print(f"[DEBUG..............update_dropdown (f)......] No status name provided. Clearing Combobox and initiating blinking if image is selected.")

            if self.image_selected:
                print("[DEBUG..............update_dropdown (f)......] Image is selected and blinking is not active. Starting blinking.")
                if not self.blinking_active:
                    self.start_blinking()  # Start the blinking effect if it’s not already active
            else:
                print("[DEBUG..............update_dropdown (f)......] No image selected. Dropdown frame remains normal.")

    def start_blinking(self):
        if not self.blinking:
           # print("[DEBUG] Starting blinking effect.")
            self.blinking = True
            self.blink_on = False
            self.blink_frame()
        else:
           print("[DEBUG] Blinking is already active.")

    def stop_blinking(self):
        if self.blinking:
           # print("[DEBUG] Stopping blinking effect.")
            self.blinking = False
            if self.blink_id is not None:
                self.root.after_cancel(self.blink_id)
                self.blink_id = None
               # print("[DEBUG] Blinking 'after' callback cancelled.")
            # Ensure the frame background is set to normal
            self.dropdown_frame.configure(bg='#000')
           # print("[DEBUG] Dropdown frame background reset to normal ('#000').")
        else:
            print("[DEBUG] Blinking is not active. No action taken.")

    def blink_frame(self):
        if self.blinking:
            if self.blink_on:
                # Set frame background color to red
                self.dropdown_frame.configure(bg='red')
               # print("[DEBUG] Dropdown frame background set to red.")
            else:
                # Set frame background color to normal
                self.dropdown_frame.configure(bg='#000')
               # print("[DEBUG] Dropdown frame background set to normal ('#000').")
            self.blink_on = not self.blink_on
            # Schedule the next blink
            self.blink_id = self.root.after(500, self.blink_frame)
           # print("[DEBUG] Scheduled next blink in 500ms.")
   
    def select_image(self):
        """
        Selects and loads an image to the canvas.
        """
      
       # print("[DEBUG] 'Select Image' button clicked.")
        image_data = self.but_functions.browse_files()
        if image_data:
           # print("[DEBUG] Image data retrieved. Setting 'image_selected' to True.")
            self.image_selected = True  # Set image_selected to True before loading the image
            self.load_image(image_data)  # Load the image first
            
            self.status_info = get_machine_status_from_temp_img_id(self.but_functions.temp_img_id)        
            if self.status_info:
                status_name, _ = self.status_info
                self.update_dropdown(status_name)  # Then, call update_dropdown to trigger blinking if necessary
            else:
                self.update_dropdown('') 
        else:
           print("[DEBUG] No image data retrieved.")

    def load_image(self, image_data):
        """
        Loads the selected image and sets it as the background of the canvas.
        """
        # befor loading the image clear the cavus to be sure that there is no rectangles or image
        self.clear_canvas()
        if image_data:
            img_path, img_id = image_data
            # print("[DEBUG] Loading image from path: {img_path}, ID: {img_id}")
            try:
                # Open the image using PIL
                self.original_image = Image.open(img_path)
                original_width, original_height = self.original_image.size  # Store original image size
                # print("[DEBUG] Original image size: {original_width}x{original_height}")

                # Get canvas dimensions
                canvas_width = self.img_canvas.winfo_width()
                canvas_height = self.img_canvas.winfo_height()
                # print("[DEBUG] Canvas size: {canvas_width}x{canvas_height}")

                # Resize image to fit the canvas
                resized_image = self.original_image.resize((canvas_width, canvas_height))
                self.resized_img = ImageTk.PhotoImage(resized_image)
               # print("[DEBUG] Image resized to fit the canvas.")

                # Set the image as the background of the canvas
                self.img_canvas.create_image(0, 0, anchor=NW, image=self.resized_img, tags="bg")
               # print("[DEBUG] Image set as background on canvas.")

                # Ensure rectangles and other elements are drawn above the image
                self.img_canvas.tag_lower("bg")  # This ensures the image is in the background
               # print("[DEBUG] Image tag lowered to background.")

                # Keep a reference to avoid garbage collection
                self.img_canvas.image = self.resized_img
               # print("[DEBUG] Image reference stored to prevent garbage collection.")

                # Set the scroll region to match the image size and other canvas content
                self.img_canvas.config(scrollregion=self.img_canvas.bbox("all"))
               # print("[DEBUG] Scroll region set based on canvas content.")

                # Calculate the scaling factors based on the image resize
                self.resize_percent_width = canvas_width / original_width
                self.resize_percent_height = canvas_height / original_height
                # print("[DEBUG] Scaling factors calculated: width={self.resize_percent_width}, height={self.resize_percent_height}")

                # Draw parameters (green) and features (red) with scaling
               # print("[DEBUG] Drawing parameters and features on the image.")
                self.but_functions.draw_parameters_and_features(
                    self.resize_percent_width,
                    self.resize_percent_height,
                    param_color="#00ff00",
                    feature_color="#ff0000"
                )
            except Exception as e:
                messagebox.showerror("Error", f"Failed to display image: {e}")
                print(f"[ERROR] Exception occurred while loading image: {e}")
                
    def add_parameter(self):
        """
        Adds a new parameter to the selected image.
        Draws a green rectangle when clicked.
        """
         
       # Get the selected key from the dropdown
        selected_name = self.but_functions.config_tool.selected_option.get()  
        self.selected_key = self.but_functions.config_tool.name_to_key.get(selected_name, None) 
          
        if hasattr(self, 'original_image')and self.original_image is not None:
                if  self.but_functions.temp_img_id != -1:
                    if self.selected_key is not None:
                        self.but_functions.add_par_but_func_threaded(
                            resize_percent_width=self.resize_percent_width,
                            resize_percent_height=self.resize_percent_height,
                            img_not_none=True,
                            box_color="#00FF00"  # Green color for parameter box
                        )
                    else:
                        # Warn the user if no valid option was selected
                        messagebox.showwarning("No Selection", "Please choose an potential machine status first.")
                else:
                    messagebox.showwarning("No screenfeatures", "Please add a screen feature first.")
        else:
           # print("[DEBUG] No image loaded. Showing warning.")
            messagebox.showwarning("No Image", "Please load an image first.")


    def add_screen_feature(self):
        """
        Adds a new mode and feature to the selected image.
        Draws a red rectangle when clicked, using temp_img_id as the reference.
        """
       # Get the selected key from the dropdown
        selected_name = self.but_functions.config_tool.selected_option.get()  
        self.selected_key = self.but_functions.config_tool.name_to_key.get(selected_name, None) 
        
        # Check if an image has been loaded
        if hasattr(self, 'original_image') and self.original_image is not None:
            # Check if temp_img_id is valid
            if self.selected_key is not None:
                img_size = {"width": self.original_image.width, "height": self.original_image.height}
                
                # Activate drawing with red color for modes and features
                self.but_functions.add_screen_feature_but_func_threaded(
                    img_size=img_size,
                    resize_percent_width=self.resize_percent_width,
                    resize_percent_height=self.resize_percent_height,
                    img_not_none=True,
                    box_color="#FF0000"  # Red color for mode/feature box
                )
            else:
                # Warn the user if no valid option was selected
                messagebox.showwarning("No Selection", "Please choose an potential machine status first")
        else:
            # Warn the user if no image was loaded
            messagebox.showwarning("No Image", "Please load an image first.")

    def clear_canvas(self):
        """
        Clears the canvas except for the image.
        """
       # print("[DEBUG] 'Clear Canvas' button clicked.")
        self.but_functions.clear_canvas(self.img_canvas, self.resized_img)
       # print("[DEBUG] Canvas cleared.")

    def on_option_select(self, event):
        """
        Handles the selection from the dropdown list.
        """
        selected_name = self.selected_option.get()
        selected_key = self.name_to_key.get(selected_name, None)
        # print("[DEBUG] Combobox selection detected: '{selected_name}' (Key: {selected_key})")

        if selected_key is not None:
            # print("[DEBUG] Valid selection. Stopping blinking if active.")
            # Stop blinking if active
            if self.blinking:
                self.stop_blinking()
        else:
           # print("[DEBUG] Invalid selection detected. Starting blinking if image is selected.")
            # Start blinking if image is selected
            if self.image_selected and not self.blinking:
                self.start_blinking()
   
    def reload_config(self):
        """
        Reloads the config.json file after adding a new screen feature or parameter.
        """
       # print("[DEBUG] Reloading config.json...")
        # Reinitialize ButtonFunctions to reload the configuration file
        self.but_functions = ButtonFunctions(self.img_canvas, self.mde_config_dir, self.mde_config_file_name, self.templates_dir_name, self)
       # print("[DEBUG] config.json reloaded.")

    def mainloop(self):
        """
        Starts the Tkinter main event loop.
        """
       # print("[DEBUG] Starting Tkinter main loop.")
        self.root.mainloop()



