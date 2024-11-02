# parameter_selection_dialog.py

from tkinter import Toplevel, Label, Frame, Canvas, Scrollbar, BOTH, BooleanVar, Checkbutton, Button, LEFT, messagebox

def open_parameter_selection_dialog(root, unused_parameters_dics_list, but_functions, resize_percent_width, resize_percent_height, suggested_parameter_click_action):
    """
    Opens a dialog to select parameters from unused_parameters_dics_list,
    grouping them by parameter name and showing variations from different templates.
    """
    # Create a new Toplevel window
    selection_window = Toplevel(root)
    selection_window.title("Select Parameters")
    selection_window.geometry("400x500")

    # Instructions label
    Label(selection_window, text="Select parameters to suggest:").pack(pady=10)

    # Create a Frame with a Canvas and Scrollbar for scrolling
    container = Frame(selection_window)
    canvas = Canvas(container)
    scrollbar = Scrollbar(container, orient="vertical", command=canvas.yview)
    scrollable_frame = Frame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        )
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    container.pack(fill=BOTH, expand=True)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Use a list to keep track of variables and their corresponding parameters
    param_var_list = []

    # Group parameters by name
    params_by_name = {}
    for param in unused_parameters_dics_list:
        name = param.get('name', 'Unknown')
        params_by_name.setdefault(name, []).append(param)

    # Populate the scrollable frame
    for name, params in params_by_name.items():
        # Create a Label for the parameter name
        group_label = Label(scrollable_frame, text=name, font=('bold',))
        group_label.pack(anchor='w', pady=(10, 0))

        # For each parameter under the same name
        for param in params:
            template_id = param.get('template_id', 'Unknown Template')
            param_text = f"From Template {template_id}"
            var = BooleanVar()
            chk = Checkbutton(scrollable_frame, text=param_text, variable=var)
            chk.pack(anchor='w')
            param_var_list.append((var, param))  # Append the tuple to the list

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
            _param_color="#00ff00",
            _param_fill_color='red',
            _bind_click=True,
            on_click_callback=suggested_parameter_click_action  # Attach the callback
        )

    def on_cancel():
        selection_window.destroy()

    # Ensure the dialog reference is reset when the window is closed
    selection_window.protocol("WM_DELETE_WINDOW", on_cancel)

    button_frame = Frame(selection_window)
    button_frame.pack(pady=10)
    ok_button = Button(button_frame, text="OK", command=on_ok)
    ok_button.pack(side=LEFT, padx=5)
    cancel_button = Button(button_frame, text="Cancel", command=on_cancel)
    cancel_button.pack(side=LEFT, padx=5)

    # Return the selection_window to manage it externally if needed
    return selection_window
