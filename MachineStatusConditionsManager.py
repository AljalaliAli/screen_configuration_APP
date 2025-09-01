import colorsys
import tkinter as tk
from tkinter import messagebox, ttk
from config_manager import ConfigData
from helpers import get_temp_img_details


class MachineStatusConditionsManager:
    #################################################
    # === Initialization and Setup Methods ===
    #################################################
    def __init__(
        self,
        title="Machine Status Conditions Manager",
        width=800,
        height=600,
        mde_config_file_path="path/to/config.json",
        but_functions=None,
        choices_dict=None,
        name_to_key=None,
        default_conditions=None,
        on_submit_callback=None,
    ):
        """
        Initializes the MachineStatusConditionsManager with default values and configurations.

        Args:
            title: The title of the window.
            width: The width of the window.
            height: The height of the window.
            mde_config_file_path: Path to the configuration JSON file.
            but_functions: Reference to button functions or related object.
            choices_dict: Dictionary of machine statuses.
            name_to_key: Mapping from names to keys.
            default_conditions: Default conditions to load.
            on_submit_callback: Callback function to execute on submit.
        """
        self.title = title
        self.width = width
        self.height = height
        self.mde_config_file_path = mde_config_file_path
        self.config= ConfigData(self.mde_config_file_path)
        self.config_data_1 = self.config.config_data
        self.but_functions = but_functions
        self.choices_dict = choices_dict or {}
        self.name_to_key = name_to_key or {}
        self.condition_groups = []
        self.parameters = []
        self.status_conditions_manager_window = None
        #self.config_data = None
        self.machine_status_conditions = default_conditions or []
        self.is_machine_status_defined = False
        self.on_submit_callback = on_submit_callback


    def define_machine_status(self):
        """
        Opens the Machine Status Conditions Manager window and sets up the UI based on parameters.

        """
        #print(f'#'*60)
        #print(f"[Debug] define_machine_status called!")
        #print(f"self.config_data:{self.config_data}")
        #print(f'#'*60)
        if not self.but_functions:
            messagebox.showerror("Configuration Error", "Button functions are not defined.")
            return

       # self.config_data = current_config_data
        if not self.config_data_1:
            messagebox.showerror("Error", "Configuration data could not be loaded.")
            return
        if self.but_functions.temp_img_id is None:
             messagebox.showwarning("No Image selected", "Please select an Image first.")
             return

        elif self.but_functions.temp_img_id == -1:
             messagebox.showwarning("No Screen Features", "Please add a screen feature first.")
             return

        parameters, _, _, _, _ = get_temp_img_details(self.config_data_1, self.but_functions.temp_img_id)

        self.parameters = [item["name"] for item in parameters.values()]
        self.has_parameters = bool(self.parameters)

        if self.status_conditions_manager_window and self.status_conditions_manager_window.winfo_exists():
            self.status_conditions_manager_window.lift()
            return

        self.status_conditions_manager_window = tk.Toplevel()
        self.status_conditions_manager_window.title(self.title)
        self.status_conditions_manager_window.geometry(f"{self.width}x{self.height}")
        self.status_conditions_manager_window.resizable(True, True)
        self._apply_styles()

        self.machine_statuses = [value["name"] for value in self.choices_dict.values()]

        if self.has_parameters:
            self.setup_complex_ui()
        else:
            self.setup_simplified_ui()

    def _apply_styles(self):
        """
        Applies consistent styling to the UI elements using ttk styles.
        """
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("MainFrame.TFrame", background="#2c3e50")
        style.configure("TLabel", background="#34495e", foreground="#ecf0f1", font=("Arial", 10))
        style.configure("TEntry", font=("Arial", 10))
        style.configure("TButton", font=("Arial", 10))
        style.configure("TCombobox", font=("Arial", 10))
        style.map(
            "TButton",
            background=[("active", "#3498db")],
            foreground=[("active", "#ecf0f1")],
        )

    #################################################
    # === UI Setup Methods ===
    #################################################
    def setup_complex_ui(self):
        """
        Sets up the complex UI with parameters, allowing users to define conditions and nested groups.
        """
        self.condition_groups = []
        main_frame = ttk.Frame(self.status_conditions_manager_window, style="MainFrame.TFrame")
        main_frame.pack(fill="both", expand=True)
        self._create_scrollable_frame(main_frame)

        if self.machine_status_conditions:
            for condition_group in self.machine_status_conditions:
                self.add_condition_group(initial_data=condition_group, level=0)
        else:
            self.add_condition_group(level=0)

        self.update_condition_display()
        self._create_buttons(main_frame, self.add_condition_group, self.submit_status_conditions)

    def setup_simplified_ui(self):
        """
        Sets up a simplified UI when no parameters are available, allowing users to select a machine status.
        """
        simplified_frame = ttk.Frame(
            self.status_conditions_manager_window, padding=20, style="MainFrame.TFrame"
        )
        simplified_frame.pack(fill="both", expand=True)
        status_label = ttk.Label(simplified_frame, text="Machine Status:")
        status_label.pack(anchor="w", pady=(0, 5))
        self.simple_selected_status = tk.StringVar()
        machine_status_dropdown = ttk.Combobox(
            simplified_frame,
            textvariable=self.simple_selected_status,
            values=self.machine_statuses,
            state="readonly",
        )
        machine_status_dropdown.pack(fill="x", padx=5, pady=5)
        if self.machine_statuses:
            machine_status_dropdown.current(0)


        submit_btn = ttk.Button(
            simplified_frame, text="Submit", command=self.submit_simple_status_conditions
        )
        submit_btn.pack(pady=10)

    def _create_scrollable_frame(self, parent_frame):
        """
        Creates a scrollable frame to accommodate multiple condition groups in the UI.

        Args:
            parent_frame: The parent frame in which to create the scrollable frame.
        """
        container = ttk.Frame(parent_frame)
        canvas = tk.Canvas(container, background="#2c3e50", highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas, style="MainFrame.TFrame")
        self.scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        container.pack(fill="both", expand=True)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def _create_buttons(
        self,
        parent_frame,
        add_command,
        submit_command,
    ):
        """
        Creates 'Add Condition Group' and 'Submit' buttons at the bottom of the UI.

        Args:
            parent_frame: The parent frame in which to create the buttons.
            add_command: The command to execute when 'Add Condition Group' is clicked.
            submit_command: The command to execute when 'Submit' is clicked.
        """
        button_frame = ttk.Frame(parent_frame, style="MainFrame.TFrame")
        button_frame.pack(pady=10)
        add_btn = ttk.Button(button_frame, text="Add Condition Group", command=lambda: add_command(level=0))
        add_btn.pack(side="left", padx=5)
        submit_btn = ttk.Button(button_frame, text="Submit", command=submit_command)
        submit_btn.pack(side="left", padx=5)

    #################################################
    # === UI Elements Creation Methods ===
    #################################################
    def add_condition_group(
        self,
        initial_data=None,
        parent_frame=None,
        parent_group=None,
        is_root=True,
        level=0,
    ):
        """
        Adds a new condition group to the UI. Can be a root group or a nested group.

        Args:
            initial_data: Initial data to populate the group with.
            parent_frame: The parent frame in which to create the group.
            parent_group: The parent group to which this group belongs.
            is_root: Indicates if this is a root group.
            level: The nesting level of the group.

        Returns:
            The group dictionary containing group details and UI elements.
        """
        group = {"operands": [], "parent_group": parent_group}
        parent_frame = parent_frame or self.scrollable_frame
        bg_color = self.get_color_by_level(level)
        group_frame = tk.Frame(parent_frame, relief="groove", borderwidth=2, bg=bg_color)
        group_frame.pack(fill="x", padx=10, pady=10, ipady=5, ipadx=5)
        group["frame"] = group_frame

        if is_root:
            self._add_status_selector(group, group_frame, bg_color)

        button_container = tk.Frame(group_frame, bg=bg_color)
        button_container.pack(side="bottom", pady=5)
        self._add_group_buttons(group, group_frame, button_container, is_root, level)

        if initial_data:
            self._populate_initial_data(group, initial_data, group_frame, level, is_root)
        else:
            self.add_condition_row(group)

        if is_root:
            self.condition_groups.append(group)
        return group

    def add_condition_row(
        self,
        group,
        param="",
        comparison_operator="=",
        value="",
    ):
        """
        Adds a new condition row to a condition group.

        Args:
            group: The group to which the condition row will be added.
            param: The parameter name.
            comparison_operator: The comparison operator.
            value: The value to compare against.
        """
        if not self.parameters:
            messagebox.showerror(
                "Configuration Error", "No parameters available. Please check the configuration."
            )
            return

        row_frame = ttk.Frame(group["frame"])
        row_frame.pack(fill="x", padx=10, pady=2)

        logic_operator_var = self._add_logic_operator_if_needed(group, row_frame)
        param_var = self._add_param_dropdown(row_frame, param)
        comparison_operator_var = self._add_comparison_operator_dropdown(row_frame, comparison_operator)
        value_entry = self._add_value_entry(row_frame, value)

        condition = {
            "type": "condition",
            "logic_operator_var": logic_operator_var,
            "param_var": param_var,
            "comparison_operator_var": comparison_operator_var,
            "value_entry": value_entry,
            "frame": row_frame,
            "parent_group": group,
        }

        insert_after_btn = ttk.Button(
            row_frame,
            text="Insert After",
            command=lambda: self.insert_condition_after(group, condition),
        )
        insert_after_btn.pack(side="left", padx=2)

        duplicate_btn = ttk.Button(
            row_frame,
            text="Duplicate",
            command=lambda: self.duplicate_condition(group, condition),
        )
        duplicate_btn.pack(side="left", padx=2)

        remove_btn = ttk.Button(
            row_frame,
            text="Remove",
            command=lambda: self.remove_condition_operand(group, condition),
        )
        remove_btn.pack(side="left", padx=5)

        group["operands"].append(condition)
        self.update_condition_display()

    def add_nested_group( self, group, level, parent_frame):
        """
        Adds a nested condition group within an existing group.

        Args:
            group: The parent group.
            level: The nesting level.
            parent_frame: The frame in which to create the nested group.
        """
        logic_operator_var = self._add_logic_operator_if_needed(group, parent_frame)
        nested_group_frame = tk.Frame(parent_frame, bg=self.get_color_by_level(level + 1))
        nested_group_frame.pack(fill="x", padx=10, pady=2)
        nested_group = self.add_condition_group(
            parent_frame=nested_group_frame,
            parent_group=group,
            is_root=False,
            level=level + 1,
        )
        group["operands"].append(
            {
                "type": "group",
                "logic_operator_var": logic_operator_var,
                "group": nested_group,
                "frame": nested_group_frame,
                "parent_group": group,
            }
        )
        self.update_condition_display()

    #################################################
    # === Helper Methods for UI Components ===
    #################################################
    def _add_status_selector(
        self, group, group_frame, bg_color
    ):
        """
        Adds a machine status dropdown selector to the root condition group.

        Args:
            group: The group to which the status selector will be added.
            group_frame: The frame of the group.
            bg_color: The background color of the group.
        """
        status_label = ttk.Label(group_frame, text="Machine Status:", background=bg_color)
        status_label.pack(anchor="w", padx=5, pady=5)
        selected_option = tk.StringVar()
        machine_status_dropdown = ttk.Combobox(
            group_frame,
            textvariable=selected_option,
            values=self.machine_statuses,
            state="readonly",
        )


        machine_status_dropdown.pack(fill="x", padx=5, pady=5)
        machine_status_dropdown.bind("<<ComboboxSelected>>", self.on_option_select)
        group["status_var"] = selected_option

        condition_display_var = tk.StringVar()
        condition_display_label = ttk.Label(
            group_frame,
            textvariable=condition_display_var,
            background=bg_color,
            wraplength=600,
            justify="left",
        )
        condition_display_label.pack(anchor="w", padx=5, pady=5)
        group["condition_display_var"] = condition_display_var

    def _add_group_buttons(
        self,
        group,
        group_frame,
        button_container,
        is_root,
        level,
    ):
        """
        Adds buttons for adding conditions, nested groups, or deleting the group.

        Args:
            group: The group to which buttons will be added.
            group_frame: The frame of the group.
            button_container: The container for the buttons.
            is_root: Indicates if this is a root group.
            level: The nesting level of the group.
        """
        add_condition_btn = ttk.Button(
            button_container, text="Add Condition", command=lambda: self.add_condition_row(group)
        )
        add_condition_btn.pack(side="left", padx=5)

        add_nested_group_btn = ttk.Button(
            button_container,
            text="Add Nested Group",
            command=lambda: self.add_nested_group(group, level, group_frame),
        )
        add_nested_group_btn.pack(side="left", padx=5)

        if not is_root:
            delete_group_btn = ttk.Button(
                button_container,
                text="Delete Group",
                command=lambda: self.remove_condition_operand(group["parent_group"], group),
            )
            delete_group_btn.pack(side="left", padx=5)

    def _add_logic_operator_if_needed(
        self, group, parent_frame
    ):
        """
        Adds a logic operator dropdown ('AND', 'OR') if the group already has operands.

        Args:
            group: The group to which the logic operator may be added.
            parent_frame: The frame in which to add the logic operator.

        Returns:
            The logic operator variable if added, otherwise None.
        """
        if group["operands"]:
            logic_operator_var = tk.StringVar(value="AND")
            logic_operator_dropdown = ttk.Combobox(
                parent_frame,
                textvariable=logic_operator_var,
                values=["AND", "OR"],
                state="readonly",
                width=5,
            )
            logic_operator_dropdown.pack(side="left", padx=5)
            logic_operator_var.trace_add("write", lambda *args: self.update_condition_display())
            return logic_operator_var
        return None

    def _add_param_dropdown(self, parent_frame, param):
        """
        Adds a parameter dropdown to a condition row.

        Args:
            parent_frame: The frame in which to add the parameter dropdown.
            param: The default parameter value.

        Returns:
            The parameter variable.
        """
        param_var = tk.StringVar(value=param)
        param_dropdown = ttk.Combobox(
            parent_frame,
            textvariable=param_var,
            values=self.parameters,
            state="readonly",
            width=15,
        )
        param_dropdown.pack(side="left", padx=5)
        param_var.trace_add("write", lambda *args: self.update_condition_display())
        return param_var

    def _add_comparison_operator_dropdown(
        self, parent_frame, comparison_operator
    ):
        """
        Adds a comparison operator dropdown to a condition row.

        Args:
            parent_frame: The frame in which to add the comparison operator dropdown.
            comparison_operator: The default comparison operator.

        Returns:
            The comparison operator variable.
        """
        comparison_operator_var = tk.StringVar(value=comparison_operator)
        comparison_operator_dropdown = ttk.Combobox(
            parent_frame,
            textvariable=comparison_operator_var,
            values=["=", ">", "<", "<=", ">="],
            state="readonly",
            width=5,
        )
        comparison_operator_dropdown.pack(side="left", padx=5)
        comparison_operator_var.trace_add("write", lambda *args: self.update_condition_display())
        return comparison_operator_var

    def _add_value_entry(self, parent_frame, value):
        """
        Adds a value entry field to a condition row.

        Args:
            parent_frame: The frame in which to add the value entry.
            value: The default value.

        Returns:
            The value entry widget.
        """
        value_entry = ttk.Entry(parent_frame, width=10)
        value_entry.insert(0, str(value))
        value_entry.pack(side="left", padx=5)
        value_entry.bind("<KeyRelease>", lambda event: self.update_condition_display())
        return value_entry

    #################################################
    # === Data Population Methods ===
    #################################################
    def _populate_initial_data(
        self,
        group,
        initial_data,
        group_frame,
        level,
        is_root,
    ):
        """
        Populates the condition group with initial data, including conditions and nested groups.

        Args:
            group: The group to populate.
            initial_data: The initial data for the group.
            group_frame: The frame of the group.
            level: The nesting level of the group.
            is_root: Indicates if this is a root group.
        """
        if is_root:
            group["status_var"].set(initial_data.get("status", ""))
            conditions = initial_data.get("conditions", {})
        else:
            conditions = initial_data

        operands = conditions.get("operands", [])
        for idx, operand in enumerate(operands):
            logic_operator = operand.get("logic_operator")
            if "operands" in operand:
                self._add_nested_group_from_data(
                    group, operand, group_frame, level, idx, logic_operator
                )
            else:
                self.add_condition_row(
                    group,
                    operand.get("parameter", ""),
                    operand.get("comparison_operator", "="),
                    operand.get("value", ""),
                )
                if idx != 0:
                    logic_operator_var = group["operands"][-1]["logic_operator_var"]
                    if logic_operator_var:
                        logic_operator_var.set(logic_operator or "AND")

    def _add_nested_group_from_data(
        self,
        group,
        operand,
        group_frame,
        level,
        idx,
        logic_operator,
    ):
        """
        Adds a nested group based on initial data, including its conditions and logic operator.

        Args:
            group: The parent group.
            operand: The operand data for the nested group.
            group_frame: The frame of the parent group.
            level: The nesting level.
            idx: The index of the operand.
            logic_operator: The logic operator ('AND' or 'OR').
        """
        nested_group_frame = tk.Frame(group_frame, bg=self.get_color_by_level(level + 1))
        nested_group_frame.pack(fill="x", padx=10, pady=2)

        logic_operator_var = None
        if idx != 0:
            logic_operator_var = tk.StringVar(value=logic_operator or "AND")
            logic_operator_dropdown = ttk.Combobox(
                nested_group_frame,
                textvariable=logic_operator_var,
                values=["AND", "OR"],
                state="readonly",
                width=5,
            )
            logic_operator_dropdown.pack(side="left", padx=5)
            logic_operator_var.trace_add("write", lambda *args: self.update_condition_display())

        nested_group = self.add_condition_group(
            initial_data=operand,
            parent_frame=nested_group_frame,
            parent_group=group,
            is_root=False,
            level=level + 1,
        )

        group["operands"].append(
            {
                "type": "group",
                "logic_operator_var": logic_operator_var,
                "group": nested_group,
                "frame": nested_group_frame,
                "parent_group": group,
            }
        )

    def insert_condition_after(self, group, condition):
        """
        Inserts a new condition after the specified condition in the group.

        Args:
            group: The group containing the condition.
            condition: The condition after which to insert a new one.
        """
        # Find the index of the current condition
        try:
            condition_index = group["operands"].index(condition)
        except ValueError:
            messagebox.showerror("Error", "Condition not found in group.")
            return

        # Add a new condition row
        self.add_condition_row(group)
        
        # Move the new condition to the correct position
        if len(group["operands"]) > condition_index + 1:
            new_condition = group["operands"].pop()  # Remove from end
            group["operands"].insert(condition_index + 1, new_condition)  # Insert at correct position
            
        self.update_condition_display()

    def duplicate_condition(self, group, condition):
        """
        Duplicates the specified condition in the group.

        Args:
            group: The group containing the condition.
            condition: The condition to duplicate.
        """
        try:
            condition_index = group["operands"].index(condition)
        except ValueError:
            messagebox.showerror("Error", "Condition not found in group.")
            return

        # Get the current values from the condition
        param = condition["param_var"].get()
        comparison_operator = condition["comparison_operator_var"].get()
        value = condition["value_entry"].get()

        # Add a new condition row with the same values
        self.add_condition_row(group, param, comparison_operator, value)
        
        # Move the new condition to the position after the original
        if len(group["operands"]) > condition_index + 1:
            new_condition = group["operands"].pop()  # Remove from end
            group["operands"].insert(condition_index + 1, new_condition)  # Insert at correct position
            
        self.update_condition_display()

    #################################################
    # === Deletion Methods ===
    #################################################
    def remove_condition_operand(
        self, parent_group, operand
    ):
        """
        Removes a condition or nested group from the UI and updates the parent group accordingly.

        Args:
            parent_group: The parent group from which to remove the operand.
            operand: The operand to remove.
        """
        confirm = messagebox.askyesno(
            "Confirm Remove",
            "Are you sure you want to remove this entire group or condition?",
            parent=self.status_conditions_manager_window,
        )
        if confirm:
            # Destroy the operand's frame
            if operand["frame"].winfo_exists():
                operand["frame"].destroy()

            # Remove from parent's operands
            if operand in parent_group["operands"]:
                parent_group["operands"].remove(operand)

            # Remove empty parent groups if needed
            self.remove_empty_parent_groups(parent_group)
            # Update the condition display
            self.update_condition_display()

    def remove_empty_parent_groups(self, group):
        """
        Recursively removes empty parent groups to clean up the UI and data structure.

        Args:
            group: The group to check and potentially remove.
        """
        if not group["operands"]:
            if group["frame"].winfo_exists():
                group["frame"].destroy()
            parent_group = group.get("parent_group")
            if parent_group:
                parent_group["operands"] = [
                    op for op in parent_group["operands"] if op.get("group") != group
                ]
                self.remove_empty_parent_groups(parent_group)
            else:
                self.condition_groups = [g for g in self.condition_groups if g != group]

    #################################################
    # === Data Collection and Display Methods ===
    #################################################
    def collect_conditions(self, group):
        """
        Collects all conditions and nested groups into a structured dictionary.

        Args:
            group: The group from which to collect conditions.

        Returns:
            A dictionary representing the conditions.
        """
        operands = []
        for idx, operand in enumerate(group.get("operands", [])):
            if not operand["frame"].winfo_exists():
                continue
            logic_operator = operand["logic_operator_var"].get() if operand["logic_operator_var"] else None

            if operand["type"] == "condition":
                param_name = operand["param_var"].get()
                comparison_operator = operand["comparison_operator_var"].get()
                value = operand["value_entry"].get()

              # **Filter out operands with any fields empty**
                if not param_name or not comparison_operator or not value:
                    continue  # Skip saving this operand

                condition_dict = {
                    "parameter": param_name,
                    "comparison_operator": comparison_operator,
                    "value": value,
                }
                if logic_operator:
                    condition_dict["logic_operator"] = logic_operator
                operands.append(condition_dict)
            elif operand["type"] == "group":
                nested_conditions = self.collect_conditions(operand["group"])
                if nested_conditions["operands"]:
                    if logic_operator:
                        nested_conditions["logic_operator"] = logic_operator
                    operands.append(nested_conditions)
        return {"operands": operands}

    def generate_condition_text(self, conditions):
        """
        Generates a text representation of the conditions for display purposes.

        Args:
            conditions: The conditions dictionary.

        Returns:
            A string representing the conditions.
        """
        condition_strings = []
        for idx, operand in enumerate(conditions.get("operands", [])):
            logic_operator = operand.get("logic_operator")
            if idx > 0 and logic_operator:
                condition_strings.append(logic_operator)
            if "operands" in operand:
                nested_condition = self.generate_condition_text(operand)
                condition_strings.append(f"({nested_condition})")
            else:
                param = operand.get("parameter", "")
                comparison_operator = operand.get("comparison_operator", "=")
                value = operand.get("value", "")
                condition_strings.append(f"{param} {comparison_operator} {value}")
        return " ".join(condition_strings).strip()

    def update_condition_display(self):
        """
        Updates the condition display labels in the UI to reflect the current conditions.
        """
        for group in self.condition_groups:
            conditions = self.collect_conditions(group)
            condition_text = self.generate_condition_text(conditions)
            group["condition_display_var"].set(condition_text)

    #################################################
    # === Submission Methods ===
    #################################################
    def submit_status_conditions(self):
        """
        Collects all conditions and saves them to the configuration file upon submission.
        """
        all_selected_params = []
        total_groups_count = len(self.condition_groups)
        for group in self.condition_groups:
            status_name = group["status_var"].get()
            if not status_name:
                messagebox.showwarning(
                    "Input Error", "Please select a machine status for each group."
                )
                return
            conditions = self.collect_conditions(group)
            if total_groups_count > 1 and not conditions["operands"]:
                messagebox.showwarning(
                    "Input Error", "Please add at least one condition to each group."
                )
                return
            all_selected_params.append({"status": status_name, "conditions": conditions})

        self.machine_status_conditions = all_selected_params
        if not self.config_data_1:
            messagebox.showerror("Error", "Configuration data could not be loaded.")
            return

        image_id = str(self.but_functions.temp_img_id)
        self.config_data_1["images"][image_id]["machine_status_conditions"] = self.machine_status_conditions

        if self.config.save_config_data():#save_config_data(self.config_data, self.mde_config_file_path):
            self.is_machine_status_defined = True

        if self.on_submit_callback:
            self.on_submit_callback()

        self.status_conditions_manager_window.destroy()


    def submit_simple_status_conditions(self):
        """
        Saves the selected machine status when no parameters are available.
        """
        selected_status = self.simple_selected_status.get()
        if not selected_status:
            messagebox.showwarning("Input Error", "Please select a machine status.")
            return

        self.machine_status_conditions = [{"status": selected_status}]
        if self.config_data_1:
            image_id = str(self.but_functions.temp_img_id)

            # Check if temp_img_id is valid
            if image_id != '-1':
                if image_id not in self.config_data_1["images"]:
                    self.config_data_1["images"][image_id] = {}

                self.config_data_1["images"][image_id]["machine_status_conditions"] = self.machine_status_conditions
                if self.config.save_config_data():#save_config_data(self.config_data, self.mde_config_file_path):
                    self.is_machine_status_defined = True
            else:
                messagebox.showwarning("Invalid Image ID", "Cannot save machine status with temp_img_id = -1.")
                return

        if self.on_submit_callback:
            self.on_submit_callback()

        self.status_conditions_manager_window.destroy()

        print(f"[Debug submit_status_conditions] self.config_data_1 : {self.config_data_1}")
    #################################################
    # === Utility Methods ===
    #################################################
    def get_color_by_level(self, level):
        """
        Generates a background color based on the nesting level to differentiate groups.

        Args:
            level: The nesting level.

        Returns:
            A hex color string.
        """
        if level == 0:
            return "#2c3e50"
        hue = (level * 0.15) % 1
        saturation = 0.6
        value = 0.9
        rgb = colorsys.hsv_to_rgb(hue, saturation, value)
        rgb = tuple(int(255 * x) for x in rgb)
        return "#{:02x}{:02x}{:02x}".format(*rgb)

    def on_option_select(self, event):
        """
        Callback function when a machine status is selected from the dropdown.

        Args:
            event: The event object.
        """
        pass  # Implement additional logic if needed "