import tkinter as tk
from tkinter import ttk
import re

class ParameterPopup(tk.Toplevel):
    def __init__(self, parent, FILE_PATH):
        super().__init__(parent)
        self.title("Scan Parameters")

        self.FILE_PATH = FILE_PATH
        
        # Adding notebook (tabs)
        self.notebook = ttk.Notebook(self)
        
        # Tab frames
        self.tabs = [ttk.Frame(self.notebook) for _ in range(2)]
        for i, text in enumerate(["Pulse Sequence", "Acquisition"]):
            self.notebook.add(self.tabs[i], text=text)
        
        self.notebook.pack(expand=True, fill='both')
        
        # Create the parameter entry widgets on the first tab
        self.create_param_pulseSequence(self.tabs[0])
        self.create_param_acquisition(self.tabs[1])
        # Create bottom buttons
        # self.create_buttons()
    
    def create_param_pulseSequence(self, parent):
        parameters = [
            ("B1_freq", "B1 Frequency (MHz)","MHz"),
            ("offset", "Offset (kHz)","kHz"),
            ("p90_us", "90 Pulse (us)", "us"),
            ("p180_p90_len_fact", "180 Pulse/90 Pulse", ""),
            ("scanspacing_us", "Scan Spacing (us)","us")
        ]
        
        self.param_widgets = {}     # store the parameter widgets
        self.param_label = {}       # store the parameter labels
        
        for idx, (param_name, display_name, unit) in enumerate(parameters):
            if param_name == "[REDACTED]":  # This is for checkbox, currently not used in this example
                tk.Label(parent, text=display_name).grid(row=idx, column=0, sticky='w')
                var = tk.BooleanVar()
                tk.Checkbutton(parent, variable=var).grid(row=idx, column=1)
                self.param_widgets[param_name] = var
            else:
                label = tk.Label(parent, text=display_name)
                label.grid(row=idx, column=0, sticky='w')
                entry = tk.Entry(parent)
                entry.grid(row=idx, column=1)
                self.param_widgets[param_name] = entry
                self.param_label[param_name] = label
                # Load initial values from file
                value = self.read_parameters(self.FILE_PATH, label, param_name, unit, display_name=display_name)
                if value:
                    entry.insert(0, value)

        # Update button 
        ttk.Button(parent, text="Update Parameters", command=self.update_all_parameters).grid(row=idx+1, column=0, columnspan=2, pady=5)

    def create_param_acquisition(self, parent):
        parameters = [
            ("echotime_us", "Echo Time (us)","us"),
            ("echoshift_us", "Echo Shift (us)","us"),
            ("samples_per_echo", "Samples per echo",""),
            ("echoes_per_scan", "Echoes per scan",""),
        ]
        
        self.acquisition_widgets = {}     # store the parameter widgets
        self.acquisition_label = {}       # store the parameter labels
        
        for idx, (param_name, display_name, unit) in enumerate(parameters):
            if param_name == "[REDACTED]":  # This is for checkbox, currently not used in this example
                tk.Label(parent, text=display_name).grid(row=idx, column=0, sticky='w')
                var = tk.BooleanVar()
                tk.Checkbutton(parent, variable=var).grid(row=idx, column=1)
                self.acquisition_widgets[param_name] = var
            else:
                label = tk.Label(parent, text=display_name)
                label.grid(row=idx, column=0, sticky='w')
                entry = tk.Entry(parent)
                entry.grid(row=idx, column=1)
                self.acquisition_widgets[param_name] = entry
                self.acquisition_label[param_name] = label
                # Load initial values from file
                value = self.read_parameters(self.FILE_PATH, label, param_name, unit, display_name=display_name)
                if value:
                    entry.insert(0, value)

        # Update button 
        ttk.Button(parent, text="Update Parameters", command=self.update_aquisition_parameters).grid(row=idx+1, column=0, columnspan=2, pady=5)
        
    def update_aquisition_parameters(self):
        for param_name, widget in self.acquisition_widgets.items():
            if isinstance(widget, tk.BooleanVar):       # this is for checkbox, currently not used in this example
                new_value = widget.get()
                # Assuming the format for boolean in file
                unit = ""
            else:
                new_value = widget.get()
                unit = "us" if "echotime_us" in param_name else "us" if "echoshift_us" in param_name else ""
                display_name = self.acquisition_label[param_name].cget("text").split(":")[0]   # Extract the display name from the label widget

            if new_value != "":
                self.update_parameter(self.FILE_PATH, self.acquisition_label[param_name], param_name, new_value, unit, display_name=display_name)
    # def create_bottom_buttons(self):
    #     bottom_frame = ttk.Frame(self)
    #     bottom_frame.pack(side='bottom', fill='x', pady=5)
        
    #     buttons = ["Run", "Stop", "Load", "Help", "Pref.", "Expand", "Close"]
    #     for btn in buttons:
    #         ttk.Button(bottom_frame, text=btn, command=getattr(self, f'on_{btn.lower()}')).pack(side='left', padx=5)

    # def create_buttons(self):
    #     bottom_frame = ttk.Frame(self)
    #     bottom_frame.pack(side='bottom', fill='x', pady=5)

    #     ttk.Button(bottom_frame, text="Update Parameters", command=self.update_all_parameters).pack(side='left', padx=5)
    
    def on_run(self): pass
    def on_stop(self): pass
    def on_load(self): pass
    def on_help(self): pass
    def on_pref(self): pass
    def on_expand(self): pass
    def on_close(self): self.destroy()

    def update_all_parameters(self):    # this is not updating all parameters, but only update the parameters in the first tab
        for param_name, widget in self.param_widgets.items():
            if isinstance(widget, tk.BooleanVar):       # this is for checkbox, currently not used in this example
                new_value = widget.get()
                # Assuming the format for boolean in file
                unit = ""
            else:
                new_value = widget.get()
                unit = "MHz" if "B1_freq" in param_name else "Hz" if "offset" in param_name else "us" if "scanspacing_us" in param_name else ""
                display_name = self.param_label[param_name].cget("text").split(":")[0]   # Extract the display name from the label widget

            if new_value != "":
                self.update_parameter(self.FILE_PATH, self.param_label[param_name], param_name, new_value, unit, display_name=display_name)
  
            

    # These are functions that edit the parameters in the file
    def preserve_indentation(self,line):
        """Preserves the indentation of the original line in the new line."""
        indent = re.match(r'^\s*', line).group()
        return indent

    def read_parameters(self,FILE_PATH, param_label, param_name, unit, display_name=None):
        """Reads the parameters from the file and updates the GUI.
        FILE_PATH: the path to the file containing the parameters
        param_label: the label widget to display the parameter value (for GUI parameter)
        param_name: the name of the parameter to be read
        unit: the unit of the parameter (to print to the output)
        display_name: the name of the parameter to be displayed in the GUI (if different from param_name)"""
        if display_name is None:
            display_name = param_name

        with open(FILE_PATH, "r") as file:
            lines = file.readlines()
        
        for line in lines:
            line = line.lstrip()        # Remove leading whitespace
            if line.startswith(param_name):
                param_value = line.split("=")[1].strip()            # Extract the parameter value
                param_value = param_value.split(' ')[0]             # Remove comments
                param_label.config(text=f"{display_name}: {param_value} {unit}")
                break
        return None

    def update_parameter(self, FILE_PATH, param_label, param_name, new_value, unit, display_name=None):
        """Updates a specific parameter in the file.
        FILE_PATH: the path to the file containing the parameters
        param_label: the label widget to display the parameter value (for GUI parameter)
        param_name: the name of the parameter in the file to be updated
        new_value: the new value to be assigned to the parameter
        unit: the unit of the parameter (to print to the output)
        display_name: the name of the parameter to be displayed in the GUI (if different from param_name)"""
        if display_name is None:
            display_name = param_name

        with open(FILE_PATH, "r") as file:
            lines = file.readlines()
        
        # Update the line containing the parameter
        with open(FILE_PATH, "w") as file:
            for line in lines:   
                if line.lstrip().startswith(param_name):  # Remove leading whitespace
                    comment = line.split("=")[1].strip()            # Extract the parameter value

                    if re.search(r'#', comment):                    # Check if there is a comment after the value
                        comment = comment.split(' ',maxsplit=1)[1]      # Extract the comment after the value
                    else:
                        comment = ""

                    # Extract beginning of the line before the parameter value
                    indent = self.preserve_indentation(line)
                    file.write(f"{indent}{param_name} = {new_value} {comment}\n")
                else:
                    file.write(line)
    
        # Refresh the displayed values
        self.read_parameters(FILE_PATH, param_label, param_name, unit, display_name=display_name)

