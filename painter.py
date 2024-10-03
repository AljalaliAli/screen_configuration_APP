from tkinter import simpledialog
from helpers import get_parameters_and_features_by_id

class Painter:
    def __init__(self, canvas, mde_config_file_path):
        self.canvas = canvas
        self.mde_config_file_path = mde_config_file_path
        self.drawing = False
        self.last_rectangle = {}
        self.add_par_but_clicked = False
        self.add_feature_but_clicked = False
        # Add resize factors with default value 1 (no scaling)
        self.resize_percent_width = 1
        self.resize_percent_height = 1

    def activate_drawing(self, add_par_but_clicked=False, add_feature_but_clicked=False, resize_percent_width=1, resize_percent_height=1):
        """
        Activates drawing mode, binds the necessary events to start drawing rectangles.
        Also sets the resize percentages for scaling the coordinates.
        """
        self.add_par_but_clicked = add_par_but_clicked
        self.add_feature_but_clicked = add_feature_but_clicked
        self.resize_percent_width = resize_percent_width
        self.resize_percent_height = resize_percent_height

        self.canvas.bind('<Button-1>', self.start_drawing)
        self.canvas.bind('<B1-Motion>', self.update_rectangle)
        self.canvas.bind('<ButtonRelease-1>', self.finish_drawing)


    def deactivate_drawing(self):
        """
        Deactivates drawing mode, unbinds the events to stop drawing.
        """
        self.canvas.unbind('<Button-1>')
        self.canvas.unbind('<B1-Motion>')
        self.canvas.unbind('<ButtonRelease-1>')

    def start_drawing(self, event):
        """
        Initializes the drawing process when the left mouse button is pressed.
        """
        self.drawing = True
        self.start_x = event.x
        self.start_y = event.y
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, event.x, event.y, outline="green", width=2)

    def update_rectangle(self, event):
        """
        Updates the rectangle dimensions as the user drags the mouse.
        """
        if self.drawing:
            self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)

    def finish_drawing(self, event):
        """
        Finalizes the drawing process when the mouse button is released.
        """
        self.drawing = False
        end_x = event.x
        end_y = event.y
        self.canvas.coords(self.rect, self.start_x, self.start_y, end_x, end_y)
        
        # Scale coordinates back to the original image dimensions
        original_start_x = self.start_x / self.resize_percent_width
        original_start_y = self.start_y / self.resize_percent_height
        original_end_x = end_x / self.resize_percent_width
        original_end_y = end_y / self.resize_percent_height

        # Prompt for a name of the parameter or feature
        if self.add_par_but_clicked:
            name = simpledialog.askstring("Parameter Name", "Enter the name of the parameter:")
        elif self.add_feature_but_clicked:
            name = simpledialog.askstring("Feature Name", "Enter the name of the feature:")

        if name:
            # Save the scaled (original image size) coordinates
            self.last_rectangle[name] = {
                "x1": original_start_x, 
                "y1": original_start_y, 
                "x2": original_end_x, 
                "y2": original_end_y
            }

        self.deactivate_drawing()




    def draw_rectangle(self, temp_img_id, resize_percent_width, resize_percent_height, param_color="#00ff00", feature_color="#ff0000"):
        """
        Draws rectangles around parameters and features associated with a specified image ID,
        using different colors for parameters and features.
        """
        parameters, features = get_parameters_and_features_by_id(self.mde_config_file_path, temp_img_id)
        
        # Draw rectangles for parameters (use param_color)
        for par_id, parameter in parameters.items():
            self.create_rectangle_with_text(
                parameter["position"]["x1"] * resize_percent_width,
                parameter["position"]["y1"] * resize_percent_height,
                parameter["position"]["x2"] * resize_percent_width,
                parameter["position"]["y2"] * resize_percent_height,
                parameter["name"],
                color=param_color
            )

        # Draw rectangles for features (use feature_color)
        for feature_id, feature in features.items():
            self.create_rectangle_with_text(
                feature["position"]["x1"] * resize_percent_width,
                feature["position"]["y1"] * resize_percent_height,
                feature["position"]["x2"] * resize_percent_width,
                feature["position"]["y2"] * resize_percent_height,
                f"Feature {feature_id}",
                color=feature_color
            )




    def create_rectangle_with_text(self, x1, y1, x2, y2, name, color):
        """
        Draws a rectangle and adds associated text on the canvas using the specified color.
        """
        rect = self.canvas.create_rectangle(x1, y1, x2, y2, outline=color, width=3)
        text = self.canvas.create_text(x2 + 5, y1, text=name, anchor='w', font=("Arial", 12), fill=color)
        return rect, text


