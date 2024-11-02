# painter.py

import threading
from tkinter import simpledialog, messagebox
from helpers import get_temp_img_details

class Painter:
    def __init__(self, canvas, config_data):
        """
        Initializes the Painter class with the given canvas and configuration data.
        """
        self.canvas = canvas
        self.config_data = config_data

        # Drawing state variables
        self.drawing = False
        self.rect = None  # Current rectangle being drawn
        self.last_rectangle = {}
        self.rect_data = {}  # Dictionary to store parameter rectangle information
        self.selected_parameters_from_suggested_parameters = []
        # Interaction flags
        self.add_par_but_clicked = False
        self.add_screen_feature_but_clicked = False

        # Resizing factors and colors
        self.resize_percent_width = 1
        self.resize_percent_height = 1
        self.box_color = "#00FF00"  # Default rectangle color (green)

        # Event to signal drawing completion
        self.drawing_complete_event = threading.Event()

        # History to track the order of drawn rectangles
        self.rect_history = []  # List to store unique_tags of drawn rectangles

    # Activation/Deactivation Methods

    def activate_drawing(self, add_par_but_clicked=False, add_screen_feature_but_clicked=False,
                         resize_percent_width=1, resize_percent_height=1, box_color="#00FF00"):
        """
        Activates drawing mode and binds the necessary events.

        :param add_par_but_clicked: Boolean indicating if parameter button was clicked
        :param add_screen_feature_but_clicked: Boolean indicating if screen feature button was clicked
        :param resize_percent_width: Scaling factor for width
        :param resize_percent_height: Scaling factor for height
        :param box_color: Color for the rectangle outline
        """
        # Update state variables
        self.add_par_but_clicked = add_par_but_clicked
        self.add_screen_feature_but_clicked = add_screen_feature_but_clicked
        self.resize_percent_width = resize_percent_width
        self.resize_percent_height = resize_percent_height
        self.box_color = box_color

        self.last_rectangle = {}  # Reset the last drawing
        self.drawing_complete_event.clear()

        # Bind mouse events to canvas for drawing
        self.canvas.bind('<Button-1>', self.start_drawing)
        self.canvas.bind('<B1-Motion>', self.update_rectangle)
        self.canvas.bind('<ButtonRelease-1>', self.finish_drawing)

    def deactivate_drawing(self):
        """
        Deactivates drawing mode by removing event bindings.
        """
        self.canvas.unbind('<Button-1>')
        self.canvas.unbind('<B1-Motion>')
        self.canvas.unbind('<ButtonRelease-1>')

    # Drawing Event Methods

    def start_drawing(self, event):
        """
        Initializes the drawing process when the left mouse button is pressed.

        :param event: Tkinter event object
        """
        self.drawing = True
        self.start_x = event.x
        self.start_y = event.y
        self.rect = self.create_rectangle(event.x, event.y, event.x, event.y, self.box_color)

    def update_rectangle(self, event):
        """
        Updates the rectangle dimensions as the user drags the mouse.

        :param event: Tkinter event object
        """
        if self.drawing and self.rect:
            self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)

    def finish_drawing(self, event):
        """
        Finalizes the drawing process when the mouse button is released.
        Prompts for a name and displays it next to the rectangle.

        :param event: Tkinter event object
        """
        self.drawing = False
        end_x = event.x
        end_y = event.y
        self.canvas.coords(self.rect, self.start_x, self.start_y, end_x, end_y)

        # Scale coordinates back to original image dimensions
        original_start_x = self.start_x / self.resize_percent_width
        original_start_y = self.start_y / self.resize_percent_height
        original_end_x = end_x / self.resize_percent_width
        original_end_y = end_y / self.resize_percent_height

        # Prompt for the name of the parameter or feature
        if self.add_par_but_clicked:
            name = simpledialog.askstring("Parameter Name", "Enter the name of the parameter:")
            is_parameter = True
        elif self.add_screen_feature_but_clicked:
            name = simpledialog.askstring("Feature Name", "Enter the name of the feature:")
            is_parameter = False
        else:
            name = None
            is_parameter = False

        if name:
            # Save the scaled (original image size) coordinates
            self.last_rectangle[name] = {
                "x1": original_start_x,
                "y1": original_start_y,
                "x2": original_end_x,
                "y2": original_end_y
            }

            # Create rectangle with text and bind click events if desired
            unique_tag = self.create_rectangle_with_text(
                self.start_x,
                self.start_y,
                end_x,
                end_y,
                name,
                is_parameter=is_parameter,
                outline_color=self.box_color,
                fill_color='',        # No fill color
                text_color=self.box_color,  # Text color matches the outline
                bind_click=True       # Enable click reaction
            )

            # Remove the temporary rectangle created during drawing
            if self.rect:
                self.canvas.delete(self.rect)
            self.rect = None  # Reset the rect attribute
        else:
            # User canceled, so delete the drawn rectangle
            if self.rect:
                self.canvas.delete(self.rect)
            self.last_rectangle = {}  # Indicate cancellation

        self.deactivate_drawing()
        self.drawing_complete_event.set()  # Signal that drawing is complete

    # Helper Functions

    def create_rectangle(self, x1, y1, x2, y2, outline_color, fill_color=None, width=3):
        """
        Creates a rectangle on the canvas.

        :param x1: X-coordinate of the top-left corner
        :param y1: Y-coordinate of the top-left corner
        :param x2: X-coordinate of the bottom-right corner
        :param y2: Y-coordinate of the bottom-right corner
        :param outline_color: Color of the rectangle outline
        :param fill_color: (Optional) Fill color of the rectangle
        :param width: Width of the rectangle outline
        :return: Rectangle object ID
        """
        rect_id = self.canvas.create_rectangle(
            x1, y1, x2, y2,
            outline=outline_color,
            fill=fill_color if fill_color else '',
            width=width
        )
        return rect_id

    def create_text(self, x, y, text, anchor='w', font=("Arial", 12), fill=None):
        """
        Creates text on the canvas.

        :param x: X-coordinate for the text position
        :param y: Y-coordinate for the text position
        :param text: The text string to display
        :param anchor: Positioning anchor for the text
        :param font: Font of the text
        :param fill: Color of the text
        :return: Text object ID
        """
        text_id = self.canvas.create_text(
            x, y,
            text=text,
            anchor=anchor,
            font=font,
            fill=fill if fill else "black"
        )
        return text_id

    def assign_unique_tags(self, rect_id, text_id):
        """
        Assigns a unique tag to both the rectangle and its associated text.

        :param rect_id: Rectangle object ID
        :param text_id: Text object ID
        :return: Unique tag string
        """
        unique_tag = f"rect_{rect_id}"
        self.canvas.itemconfig(rect_id, tags=(unique_tag,))
        self.canvas.itemconfig(text_id, tags=(unique_tag,))
        return unique_tag

    def store_rectangle_data(self, unique_tag, rect_id, name, x1, y1, x2, y2, is_parameter=False):
        """
        Stores the rectangle's data in the rect_data dictionary.
        Modified to only store data if the rectangle is a parameter rectangle.

        :param unique_tag: Unique tag assigned to the rectangle and text
        :param rect_id: Rectangle object ID
        :param name: Name associated with the rectangle
        :param x1: X-coordinate of the top-left corner
        :param y1: Y-coordinate of the top-left corner
        :param x2: X-coordinate of the bottom-right corner
        :param y2: Y-coordinate of the bottom-right corner
        :param is_parameter: Boolean indicating if the rectangle is a parameter rectangle
        """
        if is_parameter:
            self.rect_data[unique_tag] = {
                'rect_id': rect_id,
                'name': name,
                "position": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
                'toggle_state': False
            }

    def bind_click_event(self, unique_tag, bind_click, click_handler=None):
        """
        Binds the click event to the rectangle and text if bind_click is True.

        :param unique_tag: Unique tag assigned to the rectangle and text
        :param bind_click: Boolean indicating whether to bind the click event
        :param click_handler: External click handler function
        """
        if bind_click and click_handler:
            self.canvas.tag_bind(unique_tag, "<Button-1>", click_handler)

    # Drawing Methods

    def create_rectangle_with_text(self, x1, y1, x2, y2, name, is_parameter=False,
                                   outline_color="#00FF00", fill_color=None, text_color=None, bind_click=False,
                                   click_handler=None):
        """
        Draws a rectangle and adds associated text to the canvas.
        Optionally binds a click event to change its color.

        :param x1: X-coordinate of the top-left corner
        :param y1: Y-coordinate of the top-left corner
        :param x2: X-coordinate of the bottom-right corner
        :param y2: Y-coordinate of the bottom-right corner
        :param name: Text to display next to the rectangle
        :param is_parameter: Boolean indicating if the rectangle is a parameter rectangle
        :param outline_color: Color of the rectangle outline
        :param fill_color: (Optional) Fill color of the rectangle
        :param text_color: (Optional) Color of the text
        :param bind_click: (Optional) If True, binds a click event to the rectangle and text
        :param click_handler: (Optional) External click handler function
        :return: Rectangle object ID
        """
        # Create the rectangle
        rect_id = self.create_rectangle(x1, y1, x2, y2, outline_color, fill_color)

        # Create the text
        text_id = self.create_text(x2 + 5, y1, name, fill=text_color if text_color else outline_color)

        # Assign unique tags to both rectangle and text
        unique_tag = self.assign_unique_tags(rect_id, text_id)

        # Store rectangle data if it is a parameter rectangle
        self.store_rectangle_data(unique_tag, rect_id, name, x1, y1, x2, y2, is_parameter=is_parameter)

        # Bind click event if required
        self.bind_click_event(unique_tag, bind_click, click_handler)

        # Track the order of rectangles
        self.rect_history.append(unique_tag)

        return rect_id

    def draw_rectangles_around_screen_features(self, screen_features_dic, resize_percent_width, resize_percent_height,
                                               feature_color="#FF0000", feature_fill_color=None, bind_click=False,
                                               click_handler=None):
        """
        Draws rectangles around screen features using the specified color.

        :param screen_features_dic: Dictionary of screen features with their details
        :param resize_percent_width: Scaling factor for width
        :param resize_percent_height: Scaling factor for height
        :param feature_color: Outline color for features
        :param feature_fill_color: Fill color for features
        :param bind_click: If True, rectangles will react to clicks
        :param click_handler: External click handler function
        """
        for feature_id, feature in screen_features_dic.items():
            self.create_rectangle_with_text(
                feature["position"]["x1"] * resize_percent_width,
                feature["position"]["y1"] * resize_percent_height,
                feature["position"]["x2"] * resize_percent_width,
                feature["position"]["y2"] * resize_percent_height,
                f"Feature {feature_id}",
                is_parameter=False,
                outline_color=feature_color,
                fill_color=feature_fill_color,
                bind_click=bind_click,
                click_handler=click_handler
            )

    def draw_rectangles_around_parameters(self, parameters_dic, resize_percent_width, resize_percent_height,
                                          param_color="#00FF00", param_fill_color=None, bind_click=False,
                                          click_handler=None):
        """
        Draws rectangles around parameters using the specified color.

        :param parameters_dic: Dictionary or list of dictionaries with parameters and their details
        :param resize_percent_width: Scaling factor for width
        :param resize_percent_height: Scaling factor for height
        :param param_color: Outline color for parameters
        :param param_fill_color: Fill color for parameters
        :param bind_click: If True, rectangles will react to clicks
        :param click_handler: External click handler function
        """
        self.resize_percent_width = resize_percent_width
        self.resize_percent_height = resize_percent_height

        # Handle different data structures
        if isinstance(parameters_dic, dict):
            items = parameters_dic.items()
        elif isinstance(parameters_dic, list):
            items = enumerate(parameters_dic)
        else:
            raise ValueError("parameters_dic should be a dictionary or a list of dictionaries")

        for par_id, parameter in items:
            self.create_rectangle_with_text(
                parameter["position"]["x1"] * resize_percent_width,
                parameter["position"]["y1"] * resize_percent_height,
                parameter["position"]["x2"] * resize_percent_width,
                parameter["position"]["y2"] * resize_percent_height,
                parameter["name"],
                is_parameter=True,
                outline_color=param_color,
                fill_color=param_fill_color,
                bind_click=bind_click,
                click_handler=click_handler
            )

    def draw_rectangles_around_parameters_and_screen_features(self, temp_img_id, resize_percent_width,
                                                              resize_percent_height, param_color="#00FF00",
                                                              param_fill_color=None, feature_color="#FF0000",
                                                              feature_fill_color=None, bind_click=False,
                                                              click_handler=None):
        """
        Draws rectangles around both parameters and screen features associated with a specific image ID.

        :param temp_img_id: Temporary image ID
        :param resize_percent_width: Scaling factor for width
        :param resize_percent_height: Scaling factor for height
        :param param_color: Outline color for parameters
        :param param_fill_color: Fill color for parameters
        :param feature_color: Outline color for features
        :param feature_fill_color: Fill color for features
        :param bind_click: If True, rectangles will react to clicks
        :param click_handler: External click handler function
        """
        # Draw rectangles for parameters
        parameters_dic, _, _, _, _ = get_temp_img_details(self.config_data, temp_img_id)
        self.draw_rectangles_around_parameters(
            parameters_dic,
            resize_percent_width,
            resize_percent_height,
            param_color,
            param_fill_color,
            bind_click=bind_click,
            click_handler=click_handler
        )

        # Draw rectangles for features
        _, screen_features_dic, _, _, _ = get_temp_img_details(self.config_data, temp_img_id)
        self.draw_rectangles_around_screen_features(
            screen_features_dic,
            resize_percent_width,
            resize_percent_height,
            feature_color,
            feature_fill_color,
            bind_click=bind_click,
            click_handler=click_handler
        )

    # New Method to Remove the Last Drawn Rectangle

    def remove_last_rectangle(self):
        """
        Removes the last drawn rectangle and its associated text from the canvas.
        """
        if not self.rect_history:
            messagebox.showinfo("Info", "No rectangles to remove.")
            return

        # Get the unique_tag of the last drawn rectangle
        unique_tag = self.rect_history.pop()

        # Delete the rectangle and text using the unique_tag
        self.canvas.delete(unique_tag)

        # Remove from rect_data if it exists
        if unique_tag in self.rect_data:
            del self.rect_data[unique_tag]

        # Optionally, remove from last_rectangle if it's the last one
        if self.last_rectangle:
            # Assuming last_rectangle stores the last rectangle by name
            # You might need to adjust this based on your implementation
            last_name = list(self.last_rectangle.keys())[-1]
            del self.last_rectangle[last_name]

        messagebox.showinfo("Success", "Last drawn rectangle has been removed.")

