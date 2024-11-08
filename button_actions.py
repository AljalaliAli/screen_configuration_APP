# button_actions.py

import os
import threading
from tkinter import filedialog, messagebox
import cv2
import json
from config_manager import ConfigData
from painter import Painter
from pattern_detection import ImageMatcher  # Import der ImageMatcher-Klasse
from helpers import (
    add_item_to_template,
    get_next_available_id,
    save_template_image,
    calculate_original_position,
   remove_parameter
)

class ButtonFunctions:
    """
    Die ButtonFunctions-Klasse verwaltet die Aktionen, die mit den Buttons in der GUI verknüpft sind,
    wie das Laden von Bildern, Hinzufügen von Parametern und Features.
    """

    def __init__(self, img_canvas, mde_config_dir, mde_config_file_name, templates_dir_name, config_tool):
        """
        Initialisiert die ButtonFunctions-Klasse.

        Parameter:
        - img_canvas (Canvas): Das Canvas, auf dem Bilder und Zeichnungen angezeigt werden.
        - mde_config_dir (str): Verzeichnispfad für die Konfigurationsdateien.
        - mde_config_file_name (str): Name der Konfigurationsdatei.
        - templates_dir_name (str): Name des Verzeichnisses, das Bildvorlagen enthält.
        - config_tool (ConfigurationTool): Referenz zur Haupt-ConfigurationTool-Instanz.
        """
        self.img_canvas = img_canvas
        self.mde_config_dir = mde_config_dir
        self.mde_config_file_name = mde_config_file_name
        self.templates_dir_name = templates_dir_name

        self.mde_config_file_path = os.path.join(mde_config_dir, mde_config_file_name)
        self.templates_dir = os.path.join(mde_config_dir, templates_dir_name)
        self.config_tool = config_tool
        self.img_path = None  # Speichert den Bildpfad global
        self.selected_key = None
        self.temp_img_id = None  # Initialisiert temp_img_id

        # Sicherstellen, dass das Konfigurationsverzeichnis, das Vorlagenverzeichnis und die config.json-Datei existieren
        self.ensure_directories_and_config(
            mde_config_dir, self.templates_dir, self.mde_config_file_path
        )

        # Konfigurationsdaten einmal laden
        #self.config_data = config_tool.config_data
        self.config_data_1 = ConfigData(self.mde_config_file_path).config_data

        # Threading-Lock für config_data
        #self.config_data_lock = threading.Lock()

        # ImageMatcher-Objekt für den Bildvergleich erstellen
        self.matcher = ImageMatcher(mde_config_dir, mde_config_file_name, templates_dir_name)

        # Painter-Klasse initialisieren
        self.painter = Painter(img_canvas, self.mde_config_file_path)
        
        self.lock = threading.Lock()
        

    def ensure_directories_and_config(self, config_dir, templates_dir, config_file):
        """
        Stellt sicher, dass das Konfigurationsverzeichnis, das Vorlagenverzeichnis und die config.json-Datei existieren.
        Erstellt sie, falls sie nicht existieren.

        Parameter:
        - config_dir (str): Pfad zum Konfigurationsverzeichnis.
        - templates_dir (str): Pfad zum Vorlagenverzeichnis.
        - config_file (str): Pfad zur Konfigurations-JSON-Datei.
        """
        # Überprüfen, ob das Konfigurationsverzeichnis existiert, falls nicht, erstellen
        if not os.path.exists(config_dir):
            print(f"Erstelle Konfigurationsverzeichnis: {config_dir}")
            os.makedirs(config_dir)

        # Überprüfen, ob das Vorlagenverzeichnis existiert, falls nicht, erstellen
        if not os.path.exists(templates_dir):
            print(f"Erstelle Vorlagenverzeichnis: {templates_dir}")
            os.makedirs(templates_dir)

        # Überprüfen, ob die config.json-Datei existiert, falls nicht, erstellen
        if not os.path.exists(config_file):
            print(f"Erstelle Konfigurationsdatei: {config_file}")
            with open(config_file, 'w') as file:
                # Erstelle eine leere JSON-Struktur
                json.dump({"images": {}}, file, indent=2)

    def browse_files(self):
        """
        Öffnet einen Dateidialog für den Benutzer, um eine Bilddatei auszuwählen.
        Verarbeitet das ausgewählte Bild, um es mit bestehenden Vorlagen abzugleichen.

        Rückgabe:
        - tuple: Ein Tupel, das den Bildpfad und die temporäre Bild-ID enthält.
        """
        file_path = filedialog.askopenfilename(
            filetypes=[("Bilddateien", "*.bmp *.jpg *.jpeg *.png *.tif *.tiff"), ("Alle Dateien", "*.*")]
        )
        print(f"[Debug] file_path: {file_path} ")
        if file_path:
            self.img_path = file_path  # Speichert den ausgewählten Bildpfad global
            # try:
            # Bild mit OpenCV laden, um Konsistenz mit dem Matcher zu gewährleisten
            img_cv2 = cv2.imread(file_path)

            if img_cv2 is None:
                messagebox.showerror("Fehler", "Bild konnte nicht geladen werden. Bitte wähle ein gültiges Bild aus.")
                return None

            # Vergleich des ausgewählten Bildes mit den Vorlagen
            print(f"[Debug browse_files]self.config_data_1:{self.config_data_1}")
            
            match_result = self.matcher.match_images(img_cv2)
            self.temp_img_id = int(match_result[1])

            # Synchronisieren mit config_tool
            self.config_tool.temp_img_id = self.temp_img_id

            return file_path, self.temp_img_id

            # except Exception as e:
            #     messagebox.showerror("Fehler beim Durchsuchen von Dateien", f"Bild konnte nicht geladen werden: {e}")
        return None

    def draw_parameters_and_features(self, resize_percent_width, resize_percent_height, param_color, feature_color):
        """
        Zeichnet Rechtecke und Namen/IDs der Parameter und Features für die zugeordnete Vorlage.
        """
        # Verwenden der Painter-Klasse zum Zeichnen der Parameter und Features auf dem Bild
        self.painter.draw_rectangles_around_parameters_and_screen_features(
            self.temp_img_id,
            resize_percent_width,
            resize_percent_height,
            param_color=param_color,
            feature_color=feature_color,
            bind_click=True,
            click_handler=self.on_rectangle_click  # Pass the click handler here
        )

    def add_template(self, img_path, img_size):
        """
        Fügt das ausgewählte Bild als neue Vorlage in der config.json-Datei hinzu.
        Gibt die Vorlagen-ID zurück, die später beim Hinzufügen von Features verwendet wird.

        Parameter:
        - img_path (str): Pfad zur Bilddatei.
        - img_size (dict): Wörterbuch mit Bildbreite und -höhe.

        Rückgabe:
        - int: Die neue Vorlagen-ID.
        """
        # Vorlagen-ID ermitteln
        new_template_id = get_next_available_id(self.config_data_1['images'])

        # Bild im Vorlagenverzeichnis speichern
        template_image_name = save_template_image(img_path, self.templates_dir, new_template_id)

        # Metadaten der Vorlage zur config_data hinzufügen
        self.config_data_1["images"][str(new_template_id)] = {
            "path": template_image_name,
            "size": {"width": img_size["width"], "height": img_size["height"]},
            "parameters": {},
            "features": {}
        }

        print(f"Neue Vorlagen-ID = {new_template_id}")
        self.temp_img_id = new_template_id  # Aktualisiert self.temp_img_id

        # Synchronisieren mit config_tool
        self.config_tool.temp_img_id = self.temp_img_id

        return new_template_id

    def add_parameter_threaded(self, resize_percent_width, resize_percent_height, box_color):
        """
        Adds a parameter to the image in a separate thread.
        """
        def add_parameter_thread():
            with self.lock:  # Acquire lock to secure the critical section
                print(f"[DEBUG] 'Add New Parameter' Button was clicked. self.temp_img_id = {self.temp_img_id}")
                if not hasattr(self.config_tool, 'original_image') or self.config_tool.original_image is None:
                    print("[ERROR] No image loaded, cannot add parameter.")
                    self.config_tool.on_parameter_addition_complete()
                    return

                # Activate drawing mode with the specified color for parameters
                self.painter.activate_drawing(
                    add_par_but_clicked=True,
                    resize_percent_width=resize_percent_width,
                    resize_percent_height=resize_percent_height,
                    box_color=box_color
                )

                # Wait until drawing is complete or canceled
                self.painter.drawing_complete_event.wait()

                # Check if drawing was canceled
                if not self.painter.last_rectangle:
                    print("[INFO] Drawing was canceled or no rectangle drawn.")
                    self.painter.add_par_but_clicked = False  # Reset the flag
                    self.config_tool.on_parameter_addition_complete()
                    return

                # Get the parameter name and position
                par_name, par_pos = self.painter.last_rectangle.popitem()

                # Retrieve temp_img_id from config_tool
                self.temp_img_id = self.config_tool.temp_img_id

                if self.temp_img_id is not None:
                    self.add_parameter(self.temp_img_id, par_name, par_pos)
                    print(f"[DEBUG] Parameter '{par_name}' added to template ID: {self.temp_img_id}")
                else:
                    print("[ERROR] No valid template ID found for adding parameter.")

                # Reset the flag here
                self.painter.add_par_but_clicked = False

                # Notify ConfigurationTool that parameter addition is complete
                self.config_tool.on_parameter_addition_complete()

        # Start the thread to add the parameter
        thread = threading.Thread(target=add_parameter_thread)
        thread.start()

    def add_screen_feature_threaded(self, img_size, resize_percent_width, resize_percent_height, box_color):
        """
        Adds a screen feature to the image in a separate thread.
        """
        def add_screen_feature_thread():
            with self.lock:  # Acquire lock to secure the critical section
                print("[DEBUG] 'Add Screen Feature' Button was clicked.")
                if not self.img_path:
                    messagebox.showerror("Error", "Image path is not valid. Please select a valid image.")
                    self.config_tool.on_screen_feature_addition_complete()
                    return

                # Activate drawing mode with the specific color for features
                self.painter.activate_drawing(
                    add_screen_feature_but_clicked=True,
                    resize_percent_width=resize_percent_width,
                    resize_percent_height=resize_percent_height,
                    box_color=box_color
                )

                # Wait until drawing is complete or canceled
                self.painter.drawing_complete_event.wait()

                # Check if drawing was canceled
                if not self.painter.last_rectangle:
                    print("[INFO] Drawing was canceled or no rectangle drawn.")
                    self.painter.add_screen_feature_but_clicked = False  # Reset the flag
                    self.config_tool.on_screen_feature_addition_complete()
                    return

                # Get the feature name and position
                feature_name, feature_pos = self.painter.last_rectangle.popitem()

                if self.config_tool.temp_img_id is None or self.config_tool.temp_img_id == -1:
                    # Add new template and get its ID
                    self.config_tool.temp_img_id = self.add_template(self.img_path, img_size)

                # Add feature to configuration
                self.add_feature_to_config(self.config_tool.temp_img_id, feature_name, feature_pos)
                print(f"[DEBUG] Feature '{feature_name}' added to template ID: {self.config_tool.temp_img_id}")

                # Reset the flag here
                self.painter.add_screen_feature_but_clicked = False

                # Notify ConfigurationTool that screen feature addition is complete
                self.config_tool.on_screen_feature_addition_complete()

        # Start the thread to add the screen feature
        thread = threading.Thread(target=add_screen_feature_thread)
        thread.start()


    def add_parameter(self, template_id, par_name, par_pos):   
        """
        Fügt einen Parameter zur config.json-Datei für die gegebene Vorlage hinzu.
        Verhindert das Hinzufügen von zwei Parametern mit demselben Namen zum selben Bild.
        Zeigt eine Fehlermeldung an, wenn der Parameter bereits existiert.
        """
        # Access the images dictionary
        images = self.config_data_1['images']
        image_data = images[str(template_id)]
        if not image_data:
            messagebox.showerror("Error", f"Image ID '{template_id}' not found.")
            
            return

        # Access the parameters dictionary
        parameters = image_data.get('parameters', {})
        if parameters is None:
            # If 'parameters' key doesn't exist, initialize it
            parameters = {}
            image_data['parameters'] = parameters

        # Check if a parameter with the same name already exists
        for param_id, param_data in parameters.items():
            if param_data.get('name') == par_name:
                messagebox.showerror("Error", f"Parameter with name '{par_name}' already exists in image ID '{template_id}'.")
                self.painter.remove_last_rectangle()
                return

        # If not exists, proceed to add the parameter
        param_data = {"name": par_name, "position": par_pos}
        add_item_to_template(template_id, "parameters", param_data, self.config_data_1)

    def add_feature_to_config(self, template_id, feature_name, feature_pos):
        """
        Fügt ein Feature zur config.json-Datei für die gegebene Vorlage hinzu.
        """
        feature_data = {"name": feature_name, "position": feature_pos}
        add_item_to_template(template_id, "features", feature_data, self.config_data_1)

    '''def clear_canvas(self, img_canvas, img_item):
        """
        Löscht das Canvas, außer dem geladenen Bild.
        """
        for item in img_canvas.find_all():
            if item != img_item:
                img_canvas.delete(item)'''

    def parametrs_suggestions(self, parameters_dic, resize_percent_width, resize_percent_height,
                              _param_color="#00ff00", _param_fill_color='red', _bind_click=True,
                              on_click_callback=None):
        """
        Highlights suggested parameters on the image.

        :param parameters_dic: Dictionary of parameters to suggest
        :param resize_percent_width: Width scaling factor
        :param resize_percent_height: Height scaling factor
        :param _param_color: Outline color for parameters
        :param _param_fill_color: Fill color for parameters
        :param _bind_click: Whether to bind click events
        :param on_click_callback: Callback function for click events
        """
        self.painter.draw_rectangles_around_parameters(
            parameters_dic,
            resize_percent_width,
            resize_percent_height,
            param_color=_param_color,
            param_fill_color=_param_fill_color,
            bind_click=_bind_click,
            click_handler=self.on_rectangle_click  # Pass the click handler here
        )

    '''def reload_config_data(self):
        """
        Lädt die Konfigurationsdaten aus der JSON-Datei neu.
        """
        self.config_data = load_config_data(self.mde_config_file_path)
        return self.config_data'''

    def reset_matcher_and_painter(self):
        """
        Lädt die Konfiguration neu, indem der Matcher, der Painter und die config_data neu initialisiert werden.
        """
        # Matcher und Painter neu initialisieren
        self.matcher = ImageMatcher(
            self.mde_config_dir, self.mde_config_file_name, self.templates_dir_name
        )
        #self.painter = Painter(self.img_canvas, self.config_data)
        self.painter = Painter(self.img_canvas, self.mde_config_file_path)

        # Konfigurationsdaten neu laden
        #self.reload_config_data()
        #return self.config_data 

    # New Method: on_rectangle_click
    def on_rectangle_click(self, event):
        """
        Event handler called when the rectangle or its text is clicked.
        Toggles the fill color of the rectangle between 'red' and transparent (no fill).
        """
        # Access the canvas from self.img_canvas
        canvas = self.img_canvas
        # Get the unique tags of the clicked item
        clicked_tags = canvas.gettags("current")
        unique_tag = None
        for tag in clicked_tags:
            if tag.startswith("rect_"):
                unique_tag = tag
                break
        if not unique_tag:
            return  # No rectangle tag found
        # Access rect_data from self.painter
        rect_info = self.painter.rect_data.get(unique_tag)
        if not rect_info:
            return  # No data found for the tag
        # Toggle the state
        rect_info['toggle_state'] = not rect_info['toggle_state']
        toggle_state = rect_info['toggle_state']

        # Access selected_parameters_from_suggested_parameters from self.painter
        selected_params = self.painter.selected_parameters_from_suggested_parameters



        # Set fill color based on toggle state
        if   toggle_state:
            new_fill_color = ''      # Active fill color

            par_to_add = {"name": rect_info["name"], "position": rect_info["position"]}
            position= rect_info["position"]
            orginal_position= calculate_original_position(position, self.painter.resize_percent_width, self.painter.resize_percent_height, operation='/')
            # Check if par_to_add is already in the list before appending
            if par_to_add not in selected_params:
                selected_params.append(par_to_add)
                self.add_parameter(self.temp_img_id, rect_info["name"], orginal_position)
   
           
        else:
            new_fill_color = 'red'         # No fill color (transparent)
            position= rect_info["position"]
            orginal_position= calculate_original_position(position, self.painter.resize_percent_width, self.painter.resize_percent_height, operation='/')
            par_to_remove = {"name": rect_info["name"], "position": rect_info["position"]}
            # Remove par_to_remove if it exists in the list
            if par_to_remove in selected_params:
                selected_params.remove(par_to_remove)
                remove_parameter(self.config_data_1, self.temp_img_id, rect_info["name"], orginal_position)#remove the par from the dict
                remove_parameter(self.mde_config_file_path, self.temp_img_id, rect_info["name"], orginal_position)# remove the par from thr json file
                

        # Update the rectangle's fill color
        canvas.itemconfig(rect_info['rect_id'], fill=new_fill_color)