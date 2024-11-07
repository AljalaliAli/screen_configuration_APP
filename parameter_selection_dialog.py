# parameter_selection_dialog.py

import tkinter as tk
from tkinter import ttk
from tkinter import (
    Toplevel, Label, Frame, Canvas, Scrollbar, BOTH, BooleanVar,
    Checkbutton, messagebox, VERTICAL, LEFT, X
)
from functools import partial
from styles import (
    configure_style,   
    PARAMETER_COLOR, 
    PARAMETER_FILL_COLOR, 
    MAIN_BACKGROUND  # Import MAIN_BACKGROUND
)

def open_parameter_selection_dialog(
    root,
    unused_parameters_dics_list,
    but_functions,
    resize_percent_width,
    resize_percent_height,
    suggested_parameter_click_action
):
    """
    Opens a dialog to select parameters from unused_parameters_dics_list,
    grouping them by parameter name and showing variations from different templates.
    Each group can be independently expanded or collapsed using "+" and "-" buttons.
    """

    # Create a new Toplevel window
    selection_window = Toplevel(root)
    selection_window.title("Select Parameters")
    selection_window.geometry("500x600")
    selection_window.transient(root)
    selection_window.grab_set()

    # Apply main background color using style.py
    selection_window.configure(bg=MAIN_BACKGROUND)

    # Initialize ttk Style
    style = ttk.Style()
    configure_style(style)

    # Instructions label
    instructions_label = Label(
        selection_window,
        text="Select parameters to suggest:",
        font=('Arial', 12, 'bold'),
        fg="#ecf0f1",  # TEXT_FOREGROUND from style.py
        bg="#34495e"    # LABEL_BACKGROUND from style.py
    )
    instructions_label.pack(pady=10, fill=X)

    # Create a Frame with a Canvas and Scrollbar for scrolling
    container = Frame(selection_window, bg=MAIN_BACKGROUND)
    container.pack(fill=BOTH, expand=True, padx=10, pady=5)

    canvas = Canvas(container, borderwidth=0, highlightthickness=0, bg=MAIN_BACKGROUND)
    scrollbar = Scrollbar(container, orient=VERTICAL, command=canvas.yview)
    scrollable_frame = Frame(canvas, bg=MAIN_BACKGROUND)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        )
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set, bg=MAIN_BACKGROUND)

    canvas.pack(side="left", fill=BOTH, expand=True)
    scrollbar.pack(side="right", fill="y")

    # Use a list to keep track of variables and their corresponding parameters
    param_var_list = []

    # Group parameters by name
    params_by_name = {}
    for param in unused_parameters_dics_list:
        name = param.get('name', 'Unknown')
        params_by_name.setdefault(name, []).append(param)

    # Function to toggle the visibility of sub-parameters when the toggle button is clicked
    def toggle_group(sub_frame, toggle_button, is_expanded, level):
        if is_expanded.get():
            sub_frame.pack_forget()
            toggle_button.config(text="+")
            is_expanded.set(False)
        else:
            sub_frame.pack(fill="x", padx=20, pady=(2, 5))
            toggle_button.config(text="-")
            is_expanded.set(True)

    # Function to handle "Select All" checkbox
    def select_all_toggle(select_all_var, sub_vars):
        new_state = select_all_var.get()
        for var in sub_vars:
            var.set(new_state)
        update_select_all(select_all_var, sub_vars)  # Ensure consistency

    # Function to update "Select All" based on sub-parameters
    def update_select_all(select_all_var, sub_vars):
        if all(var.get() for var in sub_vars):
            select_all_var.set(True)
        else:
            select_all_var.set(False)

    # Populate the scrollable frame
    for name, params in params_by_name.items():
        # List to hold sub-parameter variables for this group
        sub_vars = []
        is_expanded = BooleanVar(value=False)

        # Determine the nesting level (assuming all are level 0 here)
        level = 0

        # Frame to hold the main checkbox and toggle button
        group_frame = Frame(
            scrollable_frame,
            bd=1,
            relief="solid",
            padx=10,
            pady=5,
            bg=MAIN_BACKGROUND
        )
        group_frame.pack(fill="x", anchor='w', padx=5, pady=5)

        # Frame for main parameter and toggle button
        header_frame = Frame(group_frame, bg=MAIN_BACKGROUND)
        header_frame.pack(fill="x", anchor='w')

        # Toggle button
        toggle_button = ttk.Button(
            header_frame,
            text="+",
            width=2,
            style="Toggle.TButton"
        )
        toggle_button.pack(side=LEFT, anchor='w')

        # Main parameter as "Select All" checkbox
        select_all_var = BooleanVar()
        main_checkbox = Checkbutton(
            header_frame,
            text=name,
            font=('Arial', 11, 'bold'),
            variable=select_all_var,
            command=lambda sa=select_all_var, sv=sub_vars: select_all_toggle(sa, sv),
            fg="#ecf0f1",  # TEXT_FOREGROUND
            bg=MAIN_BACKGROUND,
            activebackground=MAIN_BACKGROUND,
            activeforeground="#ecf0f1",
            selectcolor=MAIN_BACKGROUND
        )
        main_checkbox.pack(side=LEFT, anchor="w", padx=(5, 0))

        # Sub-parameter frame (initially hidden)
        sub_frame = Frame(group_frame, padx=20, bg=MAIN_BACKGROUND)
        # Assign the toggle functionality with the correct references
        toggle_button.config(
            command=lambda sf=sub_frame, tb=toggle_button, ie=is_expanded, lvl=level + 1: toggle_group(sf, tb, ie, lvl)
        )

        # Populate the sub-parameters
        for param in params:
            template_id = param.get('template_id', 'Unknown Template')
            param_text = f"From Template {template_id}"
            var = BooleanVar()
            chk = Checkbutton(
                sub_frame,
                text=param_text,
                variable=var,
                command=partial(update_select_all, select_all_var, sub_vars),
                font=('Arial', 10),
                fg="#ecf0f1",  # TEXT_FOREGROUND
                bg=MAIN_BACKGROUND,
                activebackground=MAIN_BACKGROUND,
                activeforeground="#ecf0f1",
                selectcolor=MAIN_BACKGROUND
            )
            chk.pack(anchor='w', pady=2)
            param_var_list.append((var, param))
            sub_vars.append(var)

        # Set initial state of main checkbox based on sub-parameters
        update_select_all(select_all_var, sub_vars)

    # OK and Cancel buttons
    def on_ok():
        selected_params = [param for var, param in param_var_list if var.get()]
        if not selected_params:
            messagebox.showwarning("No Selection", "Please select at least one parameter.")
            return
        selection_window.destroy()
        # Now call parametrs_suggestions with the selected parameters
        but_functions.parametrs_suggestions(
            selected_params,
            resize_percent_width,
            resize_percent_height,
            _param_color=PARAMETER_COLOR,
            _param_fill_color=PARAMETER_FILL_COLOR,
            _bind_click=True,
            on_click_callback=suggested_parameter_click_action
        )

    def on_cancel():
        selection_window.destroy()

    # Frame for OK and Cancel buttons
    button_frame = Frame(selection_window, bg=MAIN_BACKGROUND)
    button_frame.pack(pady=10)

    ok_button = ttk.Button(
        button_frame,
        text="OK",
        width=10,
        command=on_ok,
        style="OK.TButton"
    )
    ok_button.pack(side=tk.LEFT, padx=10)

    cancel_button = ttk.Button(
        button_frame,
        text="Cancel",
        width=10,
        command=on_cancel,
        style="Cancel.TButton"
    )
    cancel_button.pack(side=tk.LEFT, padx=10)

    # Return the selection_window to manage it externally if needed
    return selection_window
