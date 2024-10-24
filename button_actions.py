# button_actions.py

import os
import threading
from tkinter import filedialog, messagebox
import cv2

from painter import Painter
from pattern_detection import ImageMatcher  # Import der ImageMatcher-Klasse
from helpers import (
    load_config_data,
    add_item_to_template,
    get_next_template_id,
    save_template_image
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
        self.config_data = config_tool.config_data

        # Threading-Lock für config_data
        self.config_data_lock = threading.Lock()

        # ImageMatcher-Objekt für den Bildvergleich erstellen
        self.matcher = ImageMatcher(mde_config_dir, mde_config_file_name, templates_dir_name)

        # Painter-Klasse initialisieren
        self.painter = Painter(img_canvas, self.config_data)

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
                match_result = self.matcher.match_images(img_cv2)
                self.temp_img_id = int(match_result[1])

                # Synchronisieren mit config_tool
                self.config_tool.temp_img_id = self.temp_img_id

                return file_path, self.temp_img_id

           # except Exception as e:
             #   messagebox.showerror("Fehler beim Durchsuchen von Dateien", f"Bild konnte nicht geladen werden: {e}")
        return None

    def draw_parameters_and_features(self, resize_percent_width, resize_percent_height, param_color, feature_color):
        """
        Zeichnet Rechtecke und Namen/IDs der Parameter und Features für die zugeordnete Vorlage.
        """
        # Verwenden der Painter-Klasse zum Zeichnen der Parameter und Features auf dem Bild
        self.painter.draw_rectangle(
            self.temp_img_id, resize_percent_width, resize_percent_height, param_color, feature_color
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
        new_template_id = get_next_template_id(self.config_data)

        # Bild im Vorlagenverzeichnis speichern
        template_image_name = save_template_image(img_path, self.templates_dir, new_template_id)

        # Metadaten der Vorlage zur config_data hinzufügen
        self.config_data["images"][str(new_template_id)] = {
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
    
            # Check if the operation was canceled
            if self.painter.last_rectangle is None:
                print("[INFO] Adding parameter was canceled.")
                # Reset the button background color
                self.config_tool.on_parameter_addition_complete()
                return
    
            # Ensure there's at least one rectangle
            if not self.painter.last_rectangle:
                print("[INFO] No rectangle drawn.")
                self.config_tool.on_parameter_addition_complete()
                return
    
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
                self.config_tool.on_parameter_addition_complete()
    
        thread = threading.Thread(target=add_parameter_thread)
        thread.start()
    
    def add_screen_feature_threaded(self, img_size, resize_percent_width, resize_percent_height, box_color):
        """
        Adds a screen feature to the image in a separate thread.
        """
        def add_screen_feature_thread():
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
    
            # Check if the operation was canceled
            if self.painter.last_rectangle is None:
                print("[INFO] Adding screen feature was canceled.")
                # Reset the button background color
                self.config_tool.on_screen_feature_addition_complete()
                return
    
            # Ensure there's at least one rectangle
            if not self.painter.last_rectangle:
                print("[INFO] No rectangle drawn.")
                self.config_tool.on_screen_feature_addition_complete()
                return
    
            # Get the feature name and position
            feature_name, feature_pos = self.painter.last_rectangle.popitem()
    
            if self.config_tool.temp_img_id is None:
                print("[ERROR] No valid template ID found for adding screen feature.")
                self.config_tool.on_screen_feature_addition_complete()
                return
            elif self.config_tool.temp_img_id == -1:
                # Add new template and get its ID
                self.config_tool.temp_img_id = self.add_template(self.img_path, img_size)
    
            print(f"[DEBUG][add_screen_feature_thread] Adding feature to config ... self.config_tool.temp_img_id = {self.config_tool.temp_img_id}, feature_name = {feature_name}, feature_pos = {feature_pos}")
            self.add_feature_to_config(self.config_tool.temp_img_id, feature_name, feature_pos)
            # Notify ConfigurationTool that screen feature addition is complete
            self.config_tool.on_screen_feature_addition_complete()
    
        thread = threading.Thread(target=add_screen_feature_thread)
        thread.start()
   
    def add_parameter(self, template_id, par_name, par_pos):
        """
        Fügt einen Parameter zur config.json-Datei für die gegebene Vorlage hinzu.
        """
        config_data = self.config_data

        param_data = {"name": par_name, "position": par_pos}
        add_item_to_template(template_id, "parameters", param_data, config_data)

    def add_feature_to_config(self, template_id, feature_name, feature_pos):
        """
        Fügt ein Feature zur config.json-Datei für die gegebene Vorlage hinzu.
        """
        feature_data = {"name": feature_name, "position": feature_pos}
        add_item_to_template(template_id, "features", feature_data, self.config_data)

    def clear_canvas(self, img_canvas, img_item):
        """
        Löscht das Canvas, außer dem geladenen Bild.
        """
        for item in img_canvas.find_all():
            if item != img_item:
                img_canvas.delete(item)

    def reload_config_data(self):
        """
        Lädt die Konfigurationsdaten aus der JSON-Datei neu.
        """
        self.config_data = load_config_data(self.mde_config_file_path)

    def reload_config(self):
        """
        Lädt die Konfiguration neu, indem der Matcher, der Painter und die config_data neu initialisiert werden.
        """
        # Matcher und Painter neu initialisieren
        self.matcher = ImageMatcher(
            self.mde_config_dir, self.mde_config_file_name, self.templates_dir_name
        )
        self.painter = Painter(self.img_canvas, self.config_data)

        # Konfigurationsdaten neu laden
        self.reload_config_data()
