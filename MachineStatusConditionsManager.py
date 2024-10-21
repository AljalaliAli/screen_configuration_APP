# MachineStatusConditionsManager.py

import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import Canvas, Frame, Toplevel
from helpers import (
    save_config_data,
    get_temp_img_details,
    add_machine_status_condition,
    remove_machine_status_condition,
    update_machine_status_condition,
    list_machine_status_conditions
)
import json


class MachineStatusConditionsManager:
    def __init__(self, title="Machine Status Conditions Manager", width=800, height=600,
                 mde_config_file_path="path/to/config.json", but_functions=None, choices_dict=None,
                 name_to_key=None, default_conditions=None, on_submit_callback=None):
        """
        Initializes the Machine Status Conditions Manager window.

        :param title: The title of the window.
        :param width: The width of the window in pixels.
        :param height: The height of the window in pixels.
        :param mde_config_file_path: Path to the configuration JSON file.
        :param but_functions: Object containing functions and data locks.
        :param choices_dict: Dictionary containing machine status choices.
        :param name_to_key: Dictionary mapping names to keys.
        :param default_conditions: List of default machine status conditions.
        :param on_submit_callback: A callback function to be called after submitting conditions.
        """

        self.title = title
        self.width = width
        self.height = height
        self.mde_config_file_path = mde_config_file_path
        self.but_functions = but_functions
        self.choices_dict = choices_dict if choices_dict else {}
        self.name_to_key = name_to_key if name_to_key else {}
        self.condition_groups = []
        self.parameters = []
        self.status_conditions_manager_window = None
        self.config_data = None

        # Initialize machine_status_conditions with default values if provided
        self.machine_status_conditions = default_conditions if default_conditions else []

        # Initialize is_machine_status_defined
        self.is_machine_status_defined = False

        # Store the callback
        self.on_submit_callback = on_submit_callback

    def define_machine_status(self, current_config_data):
        """
        Opens a new window to define machine status parameters with conditions.
        Initializes the GUI with default machine_status_conditions if available.
        """
        # Ensure but_functions and related attributes are provided
        if not self.but_functions:
            messagebox.showerror("Configuration Error", "but_functions is not defined.")
            return

        # the current configuration 
        self.config_data = current_config_data
        if not self.config_data:
            messagebox.showerror("Error", "Configuration data could not be loaded.")
            return

        # Retrieve parameters using helper function
        parameters, _, _, _, _ = get_temp_img_details(self.config_data, self.but_functions.temp_img_id)
        self.parameters = [item['name'] for item in parameters.values()]
        print(f"[DEBUG] Loaded parameters: {self.parameters}")  # Debugging statement

        # Determine if there are parameters
        self.has_parameters = len(self.parameters) > 0

        # Prevent multiple instances
        if self.status_conditions_manager_window and self.status_conditions_manager_window.winfo_exists():
            self.status_conditions_manager_window.lift()
            return

        self.status_conditions_manager_window = Toplevel()
        self.status_conditions_manager_window.title(self.title)
        self.status_conditions_manager_window.geometry(f"{self.width}x{self.height}")
        self.status_conditions_manager_window.resizable(True, True)

        # Apply a consistent style
        style = ttk.Style()
        style.configure('TFrame', background='#f0f0f0')
        style.configure('TLabel', background='#f0f0f0', font=('Arial', 10))
        style.configure('TCheckbutton', background='#f0f0f0', font=('Arial', 10))
        style.configure('TEntry', font=('Arial', 10))
        style.configure('TButton', font=('Arial', 10))
        style.configure('TCombobox', font=('Arial', 10))

        # Get machine statuses from choices_dict
        self.machine_statuses = [value['name'] for key, value in self.choices_dict.items()]

        if self.has_parameters:
            # Existing complex UI with condition groups
            self.setup_complex_ui()
        else:
            # Simplified UI with only machine status dropdown and submit button
            self.setup_simplified_ui()

    def setup_complex_ui(self):
        """
        Sets up the complex UI with condition groups when parameters are available.
        """
        # List to keep track of condition groups
        self.condition_groups = []

        # Scrollable Frame Setup
        container = ttk.Frame(self.status_conditions_manager_window)
        canvas = Canvas(container)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)

        container.pack(fill="both", expand=True)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # If there are default conditions, load them; otherwise, add an empty condition group
        if self.machine_status_conditions:
            for condition_group in self.machine_status_conditions:
                self.add_condition_group(initial_data=condition_group)
        else:
            self.add_condition_group()

        # Button Frame
        button_frame = ttk.Frame(self.status_conditions_manager_window)
        button_frame.pack(pady=10)

        # Add Condition Group button
        add_condition_group_btn = ttk.Button(
            button_frame, text="Add Condition Group",
            command=lambda: self.add_condition_group()
        )
        add_condition_group_btn.pack(side='left', padx=5)

        # Submit Button
        submit_btn = ttk.Button(
            button_frame, text="Submit",
            command=self.submit_status_conditions
        )
        submit_btn.pack(side='left', padx=5)

    def setup_simplified_ui(self):
        """
        Sets up the simplified UI with only machine status dropdown and submit button when no parameters are available.
        """
        # Frame for simplified UI
        simplified_frame = ttk.Frame(self.status_conditions_manager_window, padding=20)
        simplified_frame.pack(fill='both', expand=True)

        # Machine Status selection
        status_label = ttk.Label(simplified_frame, text="Machine Status:")
        status_label.pack(anchor='w', pady=(0, 5))

        self.simple_selected_status = tk.StringVar()
        machine_status_dropdown = ttk.Combobox(
            simplified_frame,
            textvariable=self.simple_selected_status,
            values=self.machine_statuses,
            state='readonly',
            style='Custom.TCombobox'
        )
        machine_status_dropdown.pack(fill='x', padx=5, pady=5)
        if self.machine_statuses:
            machine_status_dropdown.current(0)

        # Submit Button
        submit_btn = ttk.Button(
            simplified_frame, text="Submit",
            command=self.submit_simple_status_conditions
        )
        submit_btn.pack(pady=10)

    def add_condition_group(self, initial_data=None):
        """
        Adds a new condition group to the status_conditions_manager_window.
        If initial_data is provided, populates the group with existing conditions.

        :param initial_data: Dictionary containing 'status' and 'conditions'.
        """
        group = {}  # Dictionary to store group info

        # Frame for the group using standard Frame to support 'relief' and 'borderwidth'
        group_frame = Frame(self.scrollable_frame, relief='groove', borderwidth=2)
        group_frame.pack(fill='x', padx=10, pady=10, ipady=5, ipadx=5)

        # Store group frame before adding condition rows
        group['frame'] = group_frame

        # Machine status selection
        status_label = ttk.Label(group_frame, text="Machine Status:")
        status_label.pack(anchor='w')

        selected_option = tk.StringVar()
        machine_status_dropdown = ttk.Combobox(
            group_frame,
            textvariable=selected_option,
            values=self.machine_statuses,
            state='readonly',
            style='Custom.TCombobox'
        )
        machine_status_dropdown.pack(fill='x', padx=5, pady=5)
        machine_status_dropdown.bind("<<ComboboxSelected>>", self.on_option_select)

        # Initialize group's condition rows list
        group['condition_rows'] = []

        # Function to add condition row within this group
        def add_condition_row_in_group():
            self.add_condition_row(group)

        # Add initial condition rows from initial_data if provided
        if initial_data:
            status_name = initial_data.get('status', '')
            selected_option.set(status_name)

            conditions = initial_data.get('conditions', {}).get('operands', [])
            main_operator = initial_data.get('conditions', {}).get('operator', 'AND').upper()

            # Add each condition to the group
            for condition in conditions:
                param = condition.get('parameter', '')
                operator = condition.get('operator', 'AND')  # Default to 'AND' if not provided
                value = condition.get('value', '')
                self.add_condition_row(group, param, operator, value)

        else:
            # Add initial condition row
            add_condition_row_in_group()

        # Button to add condition row in the group
        add_condition_btn = ttk.Button(
            group_frame, text="Add Condition",
            command=add_condition_row_in_group
        )
        add_condition_btn.pack(anchor='w', padx=5, pady=5)

        # Store additional group info
        group['status_var'] = selected_option

        # Append to the condition_groups list
        self.condition_groups.append(group)

    def add_condition_row(self, group, param='', operation='=', value=''):
        """
        Adds a new condition row to the specified group.
        If param, operation, or value are provided, initializes the row with these values.

        :param group: The condition group to which the row is added.
        :param param: The parameter name.
        :param operation: The operation symbol.
        :param value: The value for the parameter.
        """
        if not self.parameters:
            messagebox.showerror("Configuration Error", "No parameters available. Please check the configuration.")
            return

        # Condition frame
        row_frame = ttk.Frame(group['frame'])
        row_frame.pack(fill='x', padx=10, pady=2)

        # Dropdown for logical operator if not the first condition
        if group['condition_rows']:
            operator_var = tk.StringVar(value='AND')
            operator_dropdown = ttk.Combobox(
                row_frame,
                textvariable=operator_var,
                values=["AND", "OR"],
                state='readonly',
                width=5
            )
            operator_dropdown.pack(side='left', padx=5)
        else:
            operator_var = None  # No operator for the first condition

        # Dropdown for parameter name
        param_var = tk.StringVar(value=param)
        param_dropdown = ttk.Combobox(
            row_frame,
            textvariable=param_var,
            values=self.parameters,
            state='readonly',
            width=15
        )
        if param:
            try:
                param_index = self.parameters.index(param)
                param_dropdown.current(param_index)
            except ValueError:
                param_dropdown.current(0)  # Default to first parameter if not found
        elif self.parameters:
            param_dropdown.current(0)  # Set default to first parameter
        else:
            messagebox.showerror("Configuration Error", "No parameters available to select.")
            return

        param_dropdown.pack(side='left', padx=5)

        # Dropdown for operation
        operation_var = tk.StringVar(value=operation)
        operation_dropdown = ttk.Combobox(
            row_frame,
            textvariable=operation_var,
            values=["=", ">", "<", "<=", ">="],
            state='readonly',
            width=5
        )
        if operation in ["=", ">", "<", "<=", ">="]:
            operation_dropdown.set(operation)
        else:
            operation_dropdown.set("=")  # Default to "="
        operation_dropdown.pack(side='left', padx=5)

        # Entry for parameter value
        value_entry = ttk.Entry(row_frame, width=10)
        value_entry.insert(0, str(value))
        value_entry.pack(side='left', padx=5)

        # Button to remove this condition row
        remove_btn = ttk.Button(row_frame, text="Remove", command=lambda: self.remove_condition_row(group, row_frame))
        remove_btn.pack(side='left', padx=5)

        # Condition text display
        condition_text_var = tk.StringVar()
        condition_text_var.set(f"{param} {operation} {value}")
        condition_label = ttk.Label(group['frame'], textvariable=condition_text_var, font=('Arial', 10, 'italic'))
        condition_label.pack(anchor='w', padx=15)

        # Update condition text whenever any of the fields change
        def update_condition_text(*args):
            current_param = param_var.get()
            current_operator = operation_var.get()
            current_value = value_entry.get()
            condition_text_var.set(f"{current_param} {current_operator} {current_value}")

        param_var.trace_add('write', update_condition_text)
        operation_var.trace_add('write', update_condition_text)
        value_entry.bind('<KeyRelease>', lambda event: update_condition_text())

        # Store variables
        condition = {
            'operator_var': operator_var,  # Can be None for the first condition
            'param_var': param_var,
            'operation_var': operation_var,
            'value_entry': value_entry,
            'condition_text_var': condition_text_var,
            'condition_label': condition_label,
            'frame': row_frame
        }
        group['condition_rows'].append(condition)

    def remove_condition_row(self, group, row_frame):
        """
        Removes a condition row from the group.

        :param group: The condition group.
        :param row_frame: The frame of the condition row to remove.
        """
        for condition in group['condition_rows']:
            if condition['frame'] == row_frame:
                # Destroy the condition text label
                condition['condition_label'].destroy()
                # Destroy the entire row frame
                condition['frame'].destroy()
                group['condition_rows'].remove(condition)
                break

    def submit_status_conditions(self):
        """
        Collects the selected parameters, their values, and operations from all condition groups.
        Structures them into the machine_status_conditions format.
        """
        all_selected_params = []
        for group in self.condition_groups:
            group_data = {}
            status_name = group['status_var'].get()
            if not status_name:
                messagebox.showwarning(
                    "Input Error",
                    "Please select a machine status for each group."
                )
                return
            group_data['status'] = status_name
            selected_params = []
            condition_rows = group['condition_rows']

            for condition in condition_rows:
                operator = condition['operator_var'].get() if condition['operator_var'] else None
                param_name = condition['param_var'].get()
                operation = condition['operation_var'].get()
                value = condition['value_entry'].get()

                if not param_name or not operation or not value:
                    messagebox.showwarning(
                        "Input Error",
                        "Please ensure all fields are filled."
                    )
                    return

                condition_dict = {
                    'parameter': param_name,
                    'operator': operation,
                    'value': value
                }

                if operator:
                    condition_dict['operator'] = operator

                selected_params.append(condition_dict)

            if not selected_params:
                messagebox.showwarning(
                    "No Selection",
                    "No parameters selected in one of the groups."
                )
                return

            # Determine the main operator for the group
            main_operator = 'AND'
            if condition_rows:
                first_condition = condition_rows[0]
                if first_condition['operator_var']:
                    main_operator = first_condition['operator_var'].get().upper()

            # Structure the conditions with a main operator and operands
            conditions_structured = {
                'operator': main_operator,
                'operands': selected_params
            }

            group_data['conditions'] = conditions_structured
            all_selected_params.append(group_data)

        # Update the machine_status_conditions attribute
        self.machine_status_conditions = all_selected_params

        # For demonstration, print the structured conditions
        print("Updated machine_status_conditions:")
        print(json.dumps(self.machine_status_conditions, indent=4, ensure_ascii=False))

        # Save the updated conditions using helper function

        if not self.config_data:
            messagebox.showerror("Error", "Configuration data could not be loaded.")
            return
        # Update `machine_status_conditions`
        self.config_data['images'][str(self.but_functions.temp_img_id)]['machine_status_conditions'] = self.machine_status_conditions

        # Save the configuration data
        successfully = save_config_data(self.config_data, self.mde_config_file_path)
        print(f'#####################################################saving successfully ={successfully}#######################################')
        print(f"self.mde_config_file_path............:{self.mde_config_file_path}")
        print(f"self.config_data............: {self.config_data}")

        if successfully:
            # Set is_machine_status_defined to True after successful save
            self.is_machine_status_defined = True

        # Call the callback if it's provided
        if self.on_submit_callback:
            self.on_submit_callback()

        # Close the status_conditions_manager_window
        self.status_conditions_manager_window.destroy()

    def submit_simple_status_conditions(self):
        """
        Handles the submission when there are no parameters.
        Sets machine_status_conditions to an empty list.
        """
        # Retrieve the selected status if needed
        selected_status = self.simple_selected_status.get()
        print(f"Selected Machine Status: {selected_status}")

        # Set machine_status_conditions to empty list
        self.machine_status_conditions = [{"status": selected_status}]
          

        # Update the machine_status_conditions in config_data
        if self.config_data:
            self.config_data['images'][str(self.but_functions.temp_img_id)]['machine_status_conditions'] = self.machine_status_conditions

            # Save the configuration data
            successfully = save_config_data(self.config_data, self.mde_config_file_path)
            print(f'#####################################################saving successfully ={successfully}#######################################')
            print(f"self.mde_config_file_path............:{self.mde_config_file_path}")
            print(f"self.config_data............: {self.config_data}")

            if successfully:
                # Set is_machine_status_defined to True after successful save
                self.is_machine_status_defined = True

        # Call the callback if it's provided
        if self.on_submit_callback:
            self.on_submit_callback()

        # Close the status_conditions_manager_window
        self.status_conditions_manager_window.destroy()

    def on_option_select(self, event):
        """
        Callback function when a machine status is selected from the dropdown.
        Implement any additional logic needed upon selection.
        """
        selected_status = event.widget.get()
        print(f"Selected Machine Status: {selected_status}")
        # Add any additional handling here


# Example usage
if __name__ == "__main__":
    # Define your default machine_status_conditions
    default_machine_status_conditions = [
        {
            'status': 'Produktiv im Automatikbetrieb',
            'conditions': {
                'operator': 'OR',
                'operands': [
                    {'parameter': 'run', 'operator': '=', 'value': '*'},
                    {'parameter': 'S', 'operator': '>', 'value': '0'}
                ]
            }
        },
        {
            'status': 'Läuft nicht',
            'conditions': {
                'operator': 'OR',
                'operands': [
                    {'parameter': 'run', 'operator': '=', 'value': 'MIN'},
                    {'parameter': 'run', 'operator': '=', 'value': 'manuell'},
                    {'parameter': 'temperature', 'operator': '<=', 'value': '50'}
                ]
            }
        }
    ]

    # Mock but_functions object
    class ButFunctions:
        def __init__(self):
            self.config_data_lock = None  # Replace with actual lock if needed
            self.temp_img_id = "1"

    but_functions_object = ButFunctions()

    # Mock choices_dict and name_to_key
    choices_dict = {
        'status1': {'name': 'Produktiv im Automatikbetrieb'},
        'status2': {'name': 'Läuft nicht'}
    }
    name_to_key = {
        'Produktiv im Automatikbetrieb': 'status1',
        'Läuft nicht': 'status2'
    }

    # Initialize Tkinter root
    root = tk.Tk()
    root.withdraw()  # Hide the main window

    # Create an instance of the manager with default conditions
    manager = MachineStatusConditionsManager(
        title="Machine Status Conditions Manager",
        width=800,
        height=600,
        mde_config_file_path="ConfigFiles/mde_config.json",
        but_functions=but_functions_object,  # Replace with your actual object
        choices_dict=choices_dict,          # Replace with your actual dictionary
        name_to_key=name_to_key,            # Replace with your actual dictionary
        default_conditions=default_machine_status_conditions
    )

    # To open the define_machine_status window
    # Assume current_config_data is provided; here we mock it with default conditions
    current_config_data = {
        "images": {
            "1": {
                "machine_status_conditions": default_machine_status_conditions
            }
        }
    }
    manager.define_machine_status(current_config_data)

    # Start the Tkinter event loop
    root.mainloop()

    # After the window is closed, you can access the updated conditions
    print("Final machine_status_conditions:")
    print(json.dumps(manager.machine_status_conditions, indent=4, ensure_ascii=False))
    print(f"Is machine status defined: {manager.is_machine_status_defined}")
