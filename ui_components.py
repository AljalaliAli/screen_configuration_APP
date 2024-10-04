from tkinter import *
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from button_actions import ButtonFunctions

class ConfigurationTool:
    def __init__(self, mde_config_dir, mde_config_file_name, templates_dir_name, choices_dict):
        self.mde_config_dir = mde_config_dir
        self.mde_config_file_name = mde_config_file_name
        self.templates_dir_name = templates_dir_name
        self.choices_dict = choices_dict
        
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

        self.create_ui(screen_width, screen_height)

    def create_ui(self, screen_width, screen_height):
        # Main container that holds both the image and the sidebar
        self.main_container = Frame(self.root)
        self.main_container.pack(fill=BOTH, expand=1)

        # Create the Image Container (left side, takes the remaining screen width after sidebar)
        img_container_width = screen_width - self.sidebar_width
        self.img_container = Frame(self.main_container, width=img_container_width, height=screen_height, bg='#4E4E6E')
        self.img_container.pack(side=LEFT, fill=BOTH, expand=1)

        # Create the Canvas to display the image
        self.img_canvas = Canvas(self.img_container, bg='#4E4E6E', cursor="cross")
        self.img_canvas.pack(fill=BOTH, expand=1)

        # Pass self to ButtonFunctions (modified)
        self.but_functions = ButtonFunctions(self.img_canvas, self.mde_config_dir, self.mde_config_file_name, self.templates_dir_name, self)

        # Create the Sidebar (right side)
        self.side_bar = Frame(self.main_container, width=self.sidebar_width, bg='#000')
        self.side_bar.pack(side=RIGHT, fill=Y)

        # Add buttons and dropdown to the sidebar
        self.add_sidebar_widgets()

    def add_sidebar_widgets(self):
        # Create padding for widgets in the sidebar
        pad_options = {'padx': 10, 'pady': 5}

        # Button to select an image
        select_img_but = Button(self.side_bar, text="Select Image", command=self.select_image)
        select_img_but.pack(fill=X, **pad_options)

        # Button to add a new parameter
        add_par_but = Button(self.side_bar, text="Add New Parameter", command=self.add_parameter)
        add_par_but.pack(fill=X, **pad_options)

        # Button to add mode and feature
        add_mode_feature_but = Button(self.side_bar, text="Add Mode and Feature", command=self.add_mode_feature)
        add_mode_feature_but.pack(fill=X, **pad_options)

        # Button to clear the canvas
        clear_canvas_but = Button(self.side_bar, text="Clear Canvas", command=self.clear_canvas)
        clear_canvas_but.pack(fill=X, **pad_options)

        # Separator
        separator = Frame(self.side_bar, height=2, bd=1, relief=SUNKEN)
        separator.pack(fill=X, padx=5, pady=10)

        # Dropdown list (Combobox) for selecting options
        options_list = [value['name'] for key, value in self.choices_dict.items()]
        self.name_to_key = {value['name']: key for key, value in self.choices_dict.items()}
        self.selected_option = StringVar()
        self.dropdown_label = Label(self.side_bar, text="Select Option:", bg='#000', fg='white')
        self.dropdown_label.pack(**pad_options)
        self.dropdown = ttk.Combobox(self.side_bar, textvariable=self.selected_option, values=options_list, state='readonly')
        self.dropdown.pack(fill=X, **pad_options)

        # Bind dropdown selection to a function
        self.dropdown.bind("<<ComboboxSelected>>", self.on_option_select)

    def update_dropdown(self, status_name):
        """
        Updates the dropdown list to display the given status name.
        If the status name is empty, it will clear the dropdown.
        """
        print(f"[DEBUG] Called update_dropdown with status_name: {status_name}")  # Debug statement
        if status_name:
            self.dropdown.set(status_name)  # Set the dropdown to the status name
            print(f"[DEBUG] Dropdown set to: {status_name}")  # Debug statement
        else:
            self.dropdown.set('')  # Clear the dropdown
            print("[DEBUG] Dropdown cleared.")  # Debug statement


    def select_image(self):
        """
        Selects and loads an image to the canvas.
        """
        image_data = self.but_functions.browse_files()
        if image_data:
            self.load_image(image_data)

    def load_image(self, image_data):
        """
        Loads the selected image and sets it as the background of the canvas.
        """
        if image_data:
            img_path, img_id = image_data
            try:
                # Open the image using PIL
                original_image = Image.open(img_path)
                original_width, original_height = original_image.size  # Store original image size

                # Get canvas dimensions
                canvas_width = self.img_canvas.winfo_width()
                canvas_height = self.img_canvas.winfo_height()

                # Resize image to fit the canvas
                resized_image = original_image.resize((canvas_width, canvas_height))
                self.img = ImageTk.PhotoImage(resized_image)

                # Set the image as the background of the canvas
                self.img_canvas.create_image(0, 0, anchor=NW, image=self.img, tags="bg")

                # Ensure rectangles and other elements are drawn above the image
                self.img_canvas.tag_lower("bg")  # This ensures the image is in the background

                # Keep a reference to avoid garbage collection
                self.img_canvas.image = self.img

                # Set the scroll region to match the image size and other canvas content
                self.img_canvas.config(scrollregion=self.img_canvas.bbox("all"))

                # Calculate the scaling factors based on the image resize
                self.resize_percent_width = canvas_width / original_width
                self.resize_percent_height = canvas_height / original_height

                # Draw parameters (green) and features (red) with scaling
                self.but_functions.draw_parameters_and_features(img_id, self.resize_percent_width, self.resize_percent_height, param_color="#00ff00", feature_color="#ff0000")

            except Exception as e:
                messagebox.showerror("Error", f"Failed to display image: {e}")

    def add_parameter(self):
        """
        Adds a new parameter to the selected image.
        Draws a green rectangle when clicked.
        """
        if hasattr(self, 'img'):
            # Activate drawing with green color for parameters
            self.but_functions.add_par_but_func_threaded(
                resize_percent_width=self.resize_percent_width,
                resize_percent_height=self.resize_percent_height,
                img_not_none=True,
                box_color="#00FF00"  # Green color for parameter box
            )
        else:
            messagebox.showwarning("No Image", "Please load an image first.")

    def add_mode_feature(self):
        """
        Adds a new mode and feature to the selected image.
        Draws a red rectangle when clicked.
        """
        if hasattr(self, 'img'):
            img_size = {"width": self.img.width(), "height": self.img.height()}
            # Activate drawing with red color for modes and features
            self.but_functions.add_mode_feature_but_func_threaded(
                img_size=img_size,
                resize_percent_width=self.resize_percent_width,
                resize_percent_height=self.resize_percent_height,
                img_not_none=True,
                box_color="#FF0000"  # Red color for mode/feature box
            )
        else:
            messagebox.showwarning("No Image", "Please load an image first.")


    def clear_canvas(self):
        """
        Clears the canvas except for the image.
        """
        self.but_functions.clear_canvas(self.img_canvas, self.img)

    def on_option_select(self, event):
        """
        Handles the selection from the dropdown list.
        """
        selected_name = self.selected_option.get()
        selected_key = self.name_to_key.get(selected_name, None)
        if selected_key:
            print(f"Selected option: {selected_name} (Key: {selected_key})")
            # Additional logic for when a selection is made
        else:
            print("Invalid selection.")

    def mainloop(self):
        """
        Starts the Tkinter main event loop.
        """
        self.root.mainloop()
