from tkinter import ttk

def configure_style(style):
    style.theme_use('clam')  # Use 'clam' theme for better style support

    # Normal style
    style.configure("Custom.TCombobox",
                    foreground='black',
                    background='white',
                    fieldbackground='white',
                    bordercolor='black',
                    lightcolor='black',
                    darkcolor='black')

    # Error style with red background
    style.configure("Error.TCombobox",
                    foreground='black',
                    background='white',
                    fieldbackground='red',
                    bordercolor='black',
                    lightcolor='black',
                    darkcolor='black')
