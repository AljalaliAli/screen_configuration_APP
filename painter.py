# painter.py

import threading
from tkinter import simpledialog
from helpers import get_temp_img_details

class Painter:
    def __init__(self, canvas, config_data):
        self.canvas = canvas
        self.config_data = config_data
        self.drawing = False
        self.last_rectangle = {}
        self.add_par_but_clicked = False
        self.add_screen_feature_but_clicked = False
        self.resize_percent_width = 1
        self.resize_percent_height = 1
        self.box_color = "#00FF00"  # Default color (green)
        self.rect = None  # Zum Verfolgen des aktuellen Rechtecks
        self.drawing_complete_event = threading.Event()  # Event zur Signalisierung des Zeichnens

    def activate_drawing(self, add_par_but_clicked=False, add_screen_feature_but_clicked=False, resize_percent_width=1, resize_percent_height=1, box_color="#00FF00"):
        """
        Aktiviert den Zeichenmodus und bindet die notwendigen Ereignisse.
        """
        self.add_par_but_clicked = add_par_but_clicked
        self.add_screen_feature_but_clicked = add_screen_feature_but_clicked
        self.resize_percent_width = resize_percent_width
        self.resize_percent_height = resize_percent_height
        self.box_color = box_color  # Setzt die Farbe für das Rechteck
        self.last_rectangle = {}  # Zurücksetzen der letzten Zeichnung
        self.drawing_complete_event.clear()  # Event zurücksetzen

        self.canvas.bind('<Button-1>', self.start_drawing)
        self.canvas.bind('<B1-Motion>', self.update_rectangle)
        self.canvas.bind('<ButtonRelease-1>', self.finish_drawing)

    def start_drawing(self, event):
        """
        Initialisiert den Zeichenprozess, wenn die linke Maustaste gedrückt wird.
        """
        self.drawing = True
        self.start_x = event.x
        self.start_y = event.y
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, event.x, event.y, outline=self.box_color, width=2)

    def update_rectangle(self, event):
        """
        Aktualisiert die Rechteckabmessungen, während der Benutzer die Maus zieht.
        """
        if self.drawing:
            self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)

    def finish_drawing(self, event):
        """
        Finalisiert den Zeichenprozess, wenn die Maustaste losgelassen wird.
        Fragt nach einem Namen und zeigt diesen neben dem Rechteck an.
        """
        self.drawing = False
        end_x = event.x
        end_y = event.y
        self.canvas.coords(self.rect, self.start_x, self.start_y, end_x, end_y)

        # Skalieren der Koordinaten zurück auf die Originalbildabmessungen
        original_start_x = self.start_x / self.resize_percent_width
        original_start_y = self.start_y / self.resize_percent_height
        original_end_x = end_x / self.resize_percent_width
        original_end_y = end_y / self.resize_percent_height

        # Abfrage des Namens des Parameters oder Features
        if self.add_par_but_clicked:
            name = simpledialog.askstring("Parameter Name", "Gib den Namen des Parameters ein:")
        elif self.add_screen_feature_but_clicked:
            name = simpledialog.askstring("Feature Name", "Gib den Namen des Features ein:")
        else:
            name = None

        if name:
            # Speichern der skalierten (Originalbildgröße) Koordinaten
            self.last_rectangle[name] = {
                "x1": original_start_x, 
                "y1": original_start_y, 
                "x2": original_end_x, 
                "y2": original_end_y
            }

            # Anzeige des Textes neben dem Rechteck (oben rechts vom Rechteck)
            text_x = end_x + 5  # 5 Pixel rechts vom Rechteck
            text_y = self.start_y  # Ausrichtung an der Oberseite des Rechtecks
            self.canvas.create_text(text_x, text_y, text=name, anchor="nw", font=("Arial", 12), fill=self.box_color)
        else:
            # Benutzer hat abgebrochen, daher das gezeichnete Rechteck löschen
            if self.rect:
                self.canvas.delete(self.rect)
            # Setze last_rectangle auf None, um den Abbruch zu signalisieren
            self.last_rectangle = None

        self.deactivate_drawing()
        self.drawing_complete_event.set()  # Event setzen, um den Thread zu signalisieren

    def deactivate_drawing(self):
        """
        Deaktiviert den Zeichenmodus, entfernt die Bindungen der Ereignisse.
        """
        self.canvas.unbind('<Button-1>')
        self.canvas.unbind('<B1-Motion>')
        self.canvas.unbind('<ButtonRelease-1>')

    def draw_rectangle(self, temp_img_id, resize_percent_width, resize_percent_height, param_color="#00ff00", feature_color="#ff0000"):
        """
        Zeichnet Rechtecke um Parameter und Features, die mit einer bestimmten Bild-ID verknüpft sind.
        """
        parameters, features, _, _, _ = get_temp_img_details(self.config_data, temp_img_id)
        
        # Rechtecke für Parameter zeichnen (mit param_color)
        for par_id, parameter in parameters.items():
            self.create_rectangle_with_text(
                parameter["position"]["x1"] * resize_percent_width,
                parameter["position"]["y1"] * resize_percent_height,
                parameter["position"]["x2"] * resize_percent_width,
                parameter["position"]["y2"] * resize_percent_height,
                parameter["name"],
                color=param_color
            )

        # Rechtecke für Features zeichnen (mit feature_color)
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
        Zeichnet ein Rechteck und fügt den zugehörigen Text auf dem Canvas hinzu.
        """
        rect = self.canvas.create_rectangle(x1, y1, x2, y2, outline=color, width=3)
        text = self.canvas.create_text(x2 + 5, y1, text=name, anchor='w', font=("Arial", 12), fill=color)
        return rect, text
