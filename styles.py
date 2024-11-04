# styles.py

from tkinter import ttk

# Define color constants
MAIN_BACKGROUND = "#1c2833"  # Darker shade for main background
LABEL_BACKGROUND = "#2e4053"  # Harmonized shade for labels
TEXT_FOREGROUND = "#f0f3f4"  # Lighter shade for text
BUTTON_FOREGROUND = "#f0f3f4"  # Consistent button text color
OK_BUTTON_BG = "#5dade2"  # Softer blue for OK button
OK_BUTTON_ACTIVE_BG = "#2e86c1"  # Slightly darker blue for active state
CANCEL_BUTTON_BG = "#e74c3c"  # Harmonized red for cancel button
CANCEL_BUTTON_ACTIVE_BG = "#c0392b"  # Darker red for active state
TOGGLE_BUTTON_BG = "#5dade2"  # Consistent color for toggle button
TOGGLE_BUTTON_ACTIVE_BG = "#2e86c1"  # Active state for toggle button
PARAMETER_COLOR = "#58d68d"  # Harmonized green for parameters
PARAMETER_FILL_COLOR = "#ec7063"  # Soft red for parameter fill
DEFAULT_FONT = ('Arial', 11)  # Consistent font style for all widgets


def configure_style(style):
    style.theme_use('clam')  # Use 'clam' theme for better style support

    # Combobox Styles
    style.configure(
        "Custom.TCombobox",
        font=DEFAULT_FONT,
        foreground='black',
        background='white',
        fieldbackground='white',
        bordercolor='black',
        lightcolor='black',
        darkcolor='black'
    )

    style.configure(
        "Error.TCombobox",
        font=DEFAULT_FONT,
        foreground='black',
        background='white',
        fieldbackground='#f1948a',  # Light red for error field
        bordercolor='black',
        lightcolor='black',
        darkcolor='black'
    )

    # Button Styles
    style.configure(
        "OK.TButton",
        font=DEFAULT_FONT,
        foreground=BUTTON_FOREGROUND,
        background=OK_BUTTON_BG,
        borderwidth=0
    )
    style.map(
        "OK.TButton",
        background=[("active", OK_BUTTON_ACTIVE_BG)],
        foreground=[("active", BUTTON_FOREGROUND)]
    )

    style.configure(
        "Cancel.TButton",
        font=DEFAULT_FONT,
        foreground=BUTTON_FOREGROUND,
        background=CANCEL_BUTTON_BG,
        borderwidth=0
    )
    style.map(
        "Cancel.TButton",
        background=[("active", CANCEL_BUTTON_ACTIVE_BG)],
        foreground=[("active", BUTTON_FOREGROUND)]
    )

    style.configure(
        "Toggle.TButton",
        font=DEFAULT_FONT,
        foreground=BUTTON_FOREGROUND,
        background=TOGGLE_BUTTON_BG,
        borderwidth=0
    )
    style.map(
        "Toggle.TButton",
        background=[("active", TOGGLE_BUTTON_ACTIVE_BG)],
        foreground=[("active", BUTTON_FOREGROUND)]
    )

    # Label Styles
    style.configure(
        "Custom.TLabel",
        font=DEFAULT_FONT,
        foreground=TEXT_FOREGROUND,
        background=LABEL_BACKGROUND
    )

    # Checkbutton Styles
    style.configure(
        "Custom.TCheckbutton",
        font=DEFAULT_FONT,
        foreground=TEXT_FOREGROUND,
        background=MAIN_BACKGROUND,
        selectcolor=MAIN_BACKGROUND
    )

def apply_widget_styles(widget, widget_type, level=0):
    """
    Applies styles to standard Tkinter widgets.

    Parameters:
    - widget: The Tkinter widget to style.
    - widget_type: A string indicating the type of widget ('label', 'button', 'checkbutton', etc.).
    - level: The nesting level for dynamic background colors (used for frames).
    """
    if widget_type == 'label':
        widget.configure(
            font=DEFAULT_FONT,
            fg=TEXT_FOREGROUND,
            bg=LABEL_BACKGROUND
        )
    elif widget_type == 'button':
        # Assuming buttons are ttk Buttons with specific styles
        pass  # ttk.Buttons are styled via configure_style
    elif widget_type == 'checkbutton':
        widget.configure(
            font=DEFAULT_FONT,
            fg=TEXT_FOREGROUND,
            bg=MAIN_BACKGROUND,
            activebackground=MAIN_BACKGROUND,
            activeforeground=TEXT_FOREGROUND,
            selectcolor=MAIN_BACKGROUND
        )
    elif widget_type == 'frame':
        widget.configure(
            bg=MAIN_BACKGROUND
        )
    elif widget_type == 'toggle_button':
        # Assuming toggle buttons are ttk Buttons with specific styles
        pass  # ttk.Buttons are styled via configure_style
    # Add more widget types as needed
