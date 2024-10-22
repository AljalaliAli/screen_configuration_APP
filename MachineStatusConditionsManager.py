import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import Canvas, Toplevel
from helpers import (
    save_config_data,
    get_temp_img_details,
    add_machine_status_condition,
    remove_machine_status_condition,
    update_machine_status_condition,
    list_machine_status_conditions
)
import json
import colorsys  # Import colorsys for color generation


class MachineStatusConditionsManager:
    def __init__(self, title="Machine Status Conditions Manager", width=800, height=600,
                 mde_config_file_path="path/to/config.json", but_functions=None, choices_dict=None,
                 name_to_key=None, default_conditions=None, on_submit_callback=None):
        """
        Initializes the Machine Status Conditions Manager window.
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

        # The current configuration
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
        style.theme_use('clam')  # Use 'clam' theme for modern look

        # Define custom styles
        style.configure('MainFrame.TFrame', background='#2c3e50')
        style.configure('ConditionFrame.TFrame', background='#3b5998')
        style.configure('TLabel', background='#34495e', foreground='#ecf0f1', font=('Arial', 10))
        style.configure('TEntry', font=('Arial', 10))
        style.configure('TButton', font=('Arial', 10))
        style.configure('TCombobox', font=('Arial', 10))
        style.map('TButton', background=[('active', '#3498db')], foreground=[('active', '#ecf0f1')])

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

        # Main frame with custom style
        main_frame = ttk.Frame(self.status_conditions_manager_window, style='MainFrame.TFrame')
        main_frame.pack(fill='both', expand=True)

        # Scrollable Frame Setup
        container = ttk.Frame(main_frame)
        canvas = Canvas(container, background='#2c3e50', highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas, style='MainFrame.TFrame')

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
                self.add_condition_group(initial_data=condition_group, level=0)
        else:
            self.add_condition_group(level=0)

        # Update condition display after loading initial data
        self.update_condition_display()

        # Button Frame
        button_frame = ttk.Frame(main_frame, style='MainFrame.TFrame')
        button_frame.pack(pady=10)

        # Add Condition Group button
        add_condition_group_btn = ttk.Button(
            button_frame, text="Add Condition Group",
            command=lambda: self.add_condition_group(level=0)
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
        # Frame for simplified UI with custom style
        simplified_frame = ttk.Frame(self.status_conditions_manager_window, padding=20, style='MainFrame.TFrame')
        simplified_frame.pack(fill='both', expand=True)

        # Machine Status selection
        status_label = ttk.Label(simplified_frame, text="Machine Status:", background='#2c3e50', foreground='#ecf0f1')
        status_label.pack(anchor='w', pady=(0, 5))

        self.simple_selected_status = tk.StringVar()
        machine_status_dropdown = ttk.Combobox(
            simplified_frame,
            textvariable=self.simple_selected_status,
            values=self.machine_statuses,
            state='readonly'
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

    def get_color_by_level(self, level):
        """
        Generates a background color based on the nesting level.
        """
        # For the root group (level 0), return a color similar to the window's background
        if level == 0:
            return '#2c3e50'  # Same as the main frame background
        else:
            # Generate a color in HSV space and convert to RGB
            hue = (level * 0.15) % 1  # Adjust the multiplier to change the rate of hue change
            saturation = 0.6
            value = 0.9
            rgb = colorsys.hsv_to_rgb(hue, saturation, value)
            # Convert RGB to hex
            rgb = tuple(int(255 * x) for x in rgb)
            return "#{:02x}{:02x}{:02x}".format(*rgb)

    def add_condition_group(self, initial_data=None, parent_frame=None, parent_group=None, is_root=True, level=0):
        """
        Adds a new condition group to the UI.
        If initial_data is provided, populates the group with existing conditions.

        :param initial_data: Dictionary containing 'status' and 'conditions'.
        :param parent_frame: The parent frame to which this group belongs.
        :param parent_group: The parent group to which this group belongs.
        :param is_root: Boolean indicating if this is a root condition group.
        :param level: Integer representing the nesting level.
        """
        group = {}  # Dictionary to store group info

        if parent_frame is None:
            parent_frame = self.scrollable_frame

        # Generate a color based on the nesting level
        bg_color = self.get_color_by_level(level)

        # Frame for the group using tk.Frame
        group_frame = tk.Frame(parent_frame, relief='groove', borderwidth=2, bg=bg_color)
        group_frame.pack(fill='x', padx=10, pady=10, ipady=5, ipadx=5)

        # Store group frame before adding condition rows
        group['frame'] = group_frame
        group['operands'] = []

        # Machine status selection (only for root groups)
        if is_root:
            status_label = ttk.Label(group_frame, text="Machine Status:", background=bg_color)
            status_label.pack(anchor='w', padx=5, pady=5)

            selected_option = tk.StringVar()
            machine_status_dropdown = ttk.Combobox(
                group_frame,
                textvariable=selected_option,
                values=self.machine_statuses,
                state='readonly'
            )
            machine_status_dropdown.pack(fill='x', padx=5, pady=5)
            machine_status_dropdown.bind("<<ComboboxSelected>>", self.on_option_select)
            group['status_var'] = selected_option

            # Label to display the complete condition
            condition_display_var = tk.StringVar()
            condition_display_label = ttk.Label(
                group_frame,
                textvariable=condition_display_var,
                background=bg_color,
                wraplength=600,
                justify='left'
            )
            condition_display_label.pack(anchor='w', padx=5, pady=5)
            group['condition_display_var'] = condition_display_var
            group['condition_display_label'] = condition_display_label

        # Container for buttons at the bottom
        button_container = tk.Frame(group_frame, bg=bg_color)
        button_container.pack(side='bottom', pady=5)

        # Button to add condition row in the group
        add_condition_btn = ttk.Button(
            button_container, text="Add Condition",
            command=lambda: add_condition_row_in_group()
        )
        add_condition_btn.pack(side='left', padx=5)

        # Button to add nested condition group
        add_nested_group_btn = ttk.Button(
            button_container, text="Add Nested Group",
            command=lambda: self.add_nested_group(group, level, group_frame)
        )
        add_nested_group_btn.pack(side='left', padx=5)

        # Button to delete this entire condition group
        if not is_root:
            delete_group_btn = ttk.Button(
                button_container, text="Delete Group",
                command=lambda: self.remove_condition_operand(parent_group, group)
            )
            delete_group_btn.pack(side='left', padx=5)

        # Function to add condition row within this group
        def add_condition_row_in_group():
            self.add_condition_row(group)
            # Ensure buttons remain at the bottom after adding a condition
            button_container.pack_forget()
            button_container.pack(side='bottom', pady=5)
            # Update the condition display
            self.update_condition_display()

        # Add initial condition rows from initial_data if provided
        if initial_data:
            if is_root:
                status_name = initial_data.get('status', '')
                group['status_var'].set(status_name)
                conditions = initial_data.get('conditions', {})
            else:
                conditions = initial_data

            operands = conditions.get('operands', [])

            for idx, operand in enumerate(operands):
                logic_operator = operand.get('logic_operator', None)

                if 'operands' in operand:
                    # Nested condition group
                    nested_group_frame = tk.Frame(group_frame, bg=self.get_color_by_level(level + 1))
                    nested_group_frame.pack(fill='x', padx=10, pady=2)

                    # Logic operator (if not the first operand)
                    if idx != 0:
                        logic_operator_var = tk.StringVar(value=logic_operator if logic_operator else 'AND')
                        logic_operator_dropdown = ttk.Combobox(
                            nested_group_frame,
                            textvariable=logic_operator_var,
                            values=["AND", "OR"],
                            state='readonly',
                            width=5
                        )
                        logic_operator_dropdown.pack(side='left', padx=5)
                        # Update condition display when logic operator changes
                        logic_operator_var.trace_add('write', lambda *args: self.update_condition_display())
                    else:
                        logic_operator_var = None

                    # Create the nested group
                    nested_group = self.add_condition_group(
                        initial_data=operand,
                        parent_frame=nested_group_frame,
                        parent_group=group,
                        is_root=False,
                        level=level + 1
                    )

                    # Store the nested group
                    nested_group_dict = {
                        'type': 'group',
                        'logic_operator_var': logic_operator_var,
                        'group': nested_group,
                        'frame': nested_group_frame
                    }
                    group['operands'].append(nested_group_dict)
                else:
                    # Simple condition
                    self.add_condition_row(group, operand.get('parameter', ''), operand.get('comparison_operator', '='), operand.get('value', ''))
                    # Set the logic operator if not the first operand
                    if idx != 0:
                        logic_operator_var = group['operands'][-1]['logic_operator_var']
                        if logic_operator_var:
                            logic_operator_var.set(logic_operator if logic_operator else 'AND')
        else:
            # Add initial condition row
            add_condition_row_in_group()

        # Append to the condition_groups list
        if is_root:
            self.condition_groups.append(group)

        return group  # Return the group for tracking nested groups

    def add_condition_row(self, group, param='', comparison_operator='=', value=''):
        """
        Adds a new condition row to the specified group.
        """
        if not self.parameters:
            messagebox.showerror("Configuration Error", "No parameters available. Please check the configuration.")
            return

        # Condition frame
        row_frame = ttk.Frame(group['frame'])
        row_frame.pack(fill='x', padx=10, pady=2)

        # Logic operator (if not the first operand)
        if group['operands'] and len(group['operands']) > 0:
            logic_operator_var = tk.StringVar(value='AND')
            logic_operator_dropdown = ttk.Combobox(
                row_frame,
                textvariable=logic_operator_var,
                values=["AND", "OR"],
                state='readonly',
                width=5
            )
            logic_operator_dropdown.pack(side='left', padx=5)
            # Update condition display when logic operator changes
            logic_operator_var.trace_add('write', lambda *args: self.update_condition_display())
        else:
            logic_operator_var = None

        # Dropdown for parameter name
        param_var = tk.StringVar(value=param)
        param_dropdown = ttk.Combobox(
            row_frame,
            textvariable=param_var,
            values=self.parameters,
            state='readonly',
            width=15
        )
        param_dropdown.pack(side='left', padx=5)
        # Update condition display when parameter changes
        param_var.trace_add('write', lambda *args: self.update_condition_display())

        # Dropdown for comparison operator
        comparison_operator_var = tk.StringVar(value=comparison_operator)
        comparison_operator_dropdown = ttk.Combobox(
            row_frame,
            textvariable=comparison_operator_var,
            values=["=", ">", "<", "<=", ">="],
            state='readonly',
            width=5
        )
        comparison_operator_dropdown.pack(side='left', padx=5)
        # Update condition display when comparison operator changes
        comparison_operator_var.trace_add('write', lambda *args: self.update_condition_display())

        # Entry for parameter value
        value_entry = ttk.Entry(row_frame, width=10)
        value_entry.insert(0, str(value))
        value_entry.pack(side='left', padx=5)
        # Update condition display when value changes
        value_entry.bind('<KeyRelease>', lambda event: self.update_condition_display())

        # Button to remove this condition row
        remove_btn = ttk.Button(
            row_frame,
            text="Remove",
            command=lambda: self.remove_condition_operand(group, condition)
        )
        remove_btn.pack(side='left', padx=5)

        # Store variables
        condition = {
            'type': 'condition',
            'logic_operator_var': logic_operator_var,  # Can be None for the first operand
            'param_var': param_var,
            'comparison_operator_var': comparison_operator_var,
            'value_entry': value_entry,
            'frame': row_frame
        }
        group['operands'].append(condition)

        # Update the condition display
        self.update_condition_display()

    def add_nested_group(self, group, level, parent_frame):
        """
        Adds a nested condition group to the specified group and links it with previous conditions.
        """
        # Add logic operator if this is not the first condition in the parent group
        if group['operands']:
            logic_operator_var = tk.StringVar(value='AND')  # Default to AND
            logic_operator_dropdown = ttk.Combobox(
                parent_frame,  # Place logic operator in the parent frame
                textvariable=logic_operator_var,
                values=["AND", "OR"],
                state='readonly',
                width=5
            )
            logic_operator_dropdown.pack(side='top', padx=5)
            # Update condition display when logic operator changes
            logic_operator_var.trace_add('write', lambda *args: self.update_condition_display())
        else:
            logic_operator_var = None

        # Create a new frame for the nested group
        nested_group_frame = tk.Frame(parent_frame, bg=self.get_color_by_level(level + 1))
        nested_group_frame.pack(fill='x', padx=10, pady=2)

        # Add the nested group as a second operand in the parent group
        nested_group = self.add_condition_group(
            parent_frame=nested_group_frame,
            parent_group=group,
            is_root=False,
            level=level + 1
        )

        # Store the nested group with the logic operator connecting the parent group and the nested group
        nested_group_dict = {
            'type': 'group',
            'logic_operator_var': logic_operator_var,
            'group': nested_group,
            'frame': nested_group_frame
        }

        # Append the new nested group to the parent group’s operands
        group['operands'].append(nested_group_dict)

        # Update the condition display
        self.update_condition_display()

    def remove_condition_operand(self, group, operand):
        """
        Removes a condition row or nested group from the group after confirmation.
        """
        confirm = messagebox.askyesno(
            "Confirm Remove",
            "Are you sure you want to remove this condition?",
            parent=self.status_conditions_manager_window
        )
        if confirm:
            # Destroy the operand's frame
            operand['frame'].destroy()

            # Destroy the logic operator widget if it exists
            if operand.get('logic_operator_dropdown'):
                operand['logic_operator_dropdown'].destroy()
            # Remove references to logic operator variable
            operand['logic_operator_var'] = None

            # Remove the operand from the group's operands list
            if operand in group['operands']:
                group['operands'].remove(operand)

            # Update the condition display
            self.update_condition_display()

    def collect_conditions(self, group):
        """
        Recursively collects conditions from the UI into a nested structure.
        """
        operands = []
        for idx, operand in enumerate(group.get('operands', [])):
            # Check if operand's frame exists
            if not operand['frame'].winfo_exists():
                continue  # Skip destroyed operands

            logic_operator = operand['logic_operator_var'].get() if operand['logic_operator_var'] else None

            if operand['type'] == 'condition':
                # Check if widgets exist
                if not operand['value_entry'].winfo_exists():
                    continue  # Skip if the widget has been destroyed

                param_name = operand['param_var'].get()
                comparison_operator = operand['comparison_operator_var'].get()
                value = operand['value_entry'].get()

                condition_dict = {
                    'parameter': param_name,
                    'comparison_operator': comparison_operator,
                    'value': value
                }

                if logic_operator:
                    condition_dict['logic_operator'] = logic_operator

                operands.append(condition_dict)

            elif operand['type'] == 'group':
                nested_conditions = self.collect_conditions(operand['group'])

                nested_condition_dict = nested_conditions  # Nested conditions already include operands

                if logic_operator:
                    nested_condition_dict['logic_operator'] = logic_operator

                operands.append(nested_condition_dict)

        return {'operands': operands}

    def generate_condition_text(self, conditions):
        """
        Generates a string representation of the conditions using brackets.
        """
        operands = conditions.get('operands', [])

        condition_strings = []

        for idx, operand in enumerate(operands):
            # Include logic operator if present
            logic_operator = operand.get('logic_operator', None)
            if idx > 0 and logic_operator:
                condition_strings.append(logic_operator)

            if 'operands' in operand:
                # Nested condition
                nested_condition = self.generate_condition_text(operand)
                condition_strings.append(f"({nested_condition})")
            else:
                param = operand.get('parameter', '')
                comparison_operator = operand.get('comparison_operator', '=')
                value = operand.get('value', '')
                condition_strings.append(f"{param} {comparison_operator} {value}")

        return ' '.join(condition_strings).strip()

    def update_condition_display(self):
        """
        Updates the condition display label with the current conditions.
        """
        for group in self.condition_groups:
            conditions = self.collect_conditions(group)
            condition_text = self.generate_condition_text(conditions)
            group['condition_display_var'].set(condition_text)

    def submit_status_conditions(self):
        """
        Collects the conditions from the UI and saves them.
        """
        all_selected_params = []

        for group in self.condition_groups:
            group_data = {}
            status_name = group['status_var'].get()
            if not status_name:
                messagebox.showwarning(
                    "Input Error",
                    "Please select a machine status for each group.",
                    parent=self.status_conditions_manager_window
                )
                return
            group_data['status'] = status_name

            conditions = self.collect_conditions(group)
            group_data['conditions'] = conditions

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

        # Update `machine_status_conditions` in config_data
        self.config_data['images'][str(self.but_functions.temp_img_id)]['machine_status_conditions'] = self.machine_status_conditions

        # Save the configuration data
        successfully = save_config_data(self.config_data, self.mde_config_file_path)
        print(f'Saving successful: {successfully}')
        print(f"Config file path: {self.mde_config_file_path}")
        print(f"Config data: {self.config_data}")

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

        if not selected_status:
            messagebox.showwarning(
                "Input Error",
                "Please select a machine status.",
                parent=self.status_conditions_manager_window
            )
            return

        # Set machine_status_conditions to a list containing the selected status
        self.machine_status_conditions = [{"status": selected_status}]

        # Update the machine_status_conditions in config_data
        if self.config_data:
            self.config_data['images'][str(self.but_functions.temp_img_id)]['machine_status_conditions'] = self.machine_status_conditions

            # Save the configuration data
            successfully = save_config_data(self.config_data, self.mde_config_file_path)
            print(f'Saving successful: {successfully}')
            print(f"Config file path: {self.mde_config_file_path}")
            print(f"Config data: {self.config_data}")

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
    # Define your default machine_status_conditions with nested conditions
    default_machine_status_conditions = [
        {
            'status': 'Produktiv im Automatikbetrieb',
            'conditions': {
                'operands': [
                    {
                        'parameter': 'run',
                        'comparison_operator': '=',
                        'value': '*'
                    },
                    {
                        'logic_operator': 'OR',
                        'parameter': 'S',
                        'comparison_operator': '>',
                        'value': '0'
                    },
                    {
                        'logic_operator': 'AND',
                        'operands': [
                            {
                                'parameter': 'T',
                                'comparison_operator': '<',
                                'value': '100'
                            },
                            {
                                'logic_operator': 'OR',
                                'parameter': 'U',
                                'comparison_operator': '>=',
                                'value': '50'
                            }
                        ]
                    }
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
