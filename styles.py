from tkinter import ttk

def configure_style(style):
    style.theme_use('default')
    style.configure("Custom.TButton", font=("Arial", 12), background="#001F3F", foreground="white")
    style.configure("Custom.TCombobox", fieldbackground="#FFFFFF", background="#FFFFFF", foreground='black')
