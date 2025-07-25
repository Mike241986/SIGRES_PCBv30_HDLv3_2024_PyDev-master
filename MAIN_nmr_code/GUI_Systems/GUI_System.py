import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import scrolledtext
import subprocess
import re
import os
from PIL import Image, ImageTk
import glob
from GUI_ParameterEdit import ParameterPopup
import psutil
# from builtins import None
# from pip._vendor.typing_extensions import Self


class Appstate:
    def __init__(self):
        self.run_FILE_PATH = "nmr_cpmg.py"      # The file being ran when clicked run
        self.config_FILE_PATH = "sys_configs/phenc_conf_halbach_v07test_240624_honey.py"
        self.cpmg_config_FILE_line_num = 54     # The location in cpmg scan file where the config file is imported
        self.diffusion_config_FILE_line_num = 54   # The location in diffusion scan file where the config file is imported
        self.scan_process = None
    
    def get_config_FILE_PATH(self):
        return self.config_FILE_PATH
    
    def update_config_FILE_PATH(self, new_path):
        self.config_FILE_PATH = new_path
    
    def get_run_FILE_PATH(self):
        return self.run_FILE_PATH
    
    def update_run_FILE_PATH(self, new_path):
        self.run_FILE_PATH = new_path
        
    def set_scan_process(self, process):
        self.scan_process = process

    def stop_scan_process(self):
        if self.scan_process and self.scan_process.poll() is None:
            try:
                proc = psutil.Process(self.scan_process.pid)
                for child in proc.children(recursive=True):
                    child.kill()
                proc.kill()
                print("Scan process terminated.")
            except Exception as e:
                print(f"Error stopping scan process: {e}")
        else:
            print("No running scan process.")
        
# Defines a class of process that can know which process it is running, multiple instances of the class can be initiated to track different processes
class ProcessState:
    def __init__(self,path):
        self.process = None
        self.path = path
    
    def update_path(self, path):
        self.path = path
        
    def start_process(self):
        if self.process is None:
            self.process = subprocess.Popen(["python", "Monitor_Noise.py"], shell=True)
            print("Subprocess started")
        else: 
            print(str(self.path), " already running")
            
    def stop_process(self):
        if self.process is not None: 
            # self.process.kill()
            # self.process = None
            # print("Process terminated")
            try:
                # Get the process and all its children
                proc = psutil.Process(self.process.pid)
                for child in proc.children(recursive=True):
                    child.kill()
                proc.kill()
                self.process = None
                print("Subprocess terminated")
            except Exception as e:
                print(f"An error occurred while terminating the subprocess: {e}")
        else:
            print("No subprocess is running")
            

def preserve_indentation(line):
    """Preserves the indentation of the original line in the new line."""
    indent = re.match(r'^\s*', line).group()
    return indent

def modify_line(FILE_PATH, line_num, new_line):
    '''Modifies a specific line in the file.
    FILE_PATH: the path to the file containing the parameters
    line_num: the line number to be modified (based on editor, so for python indexing, need to subtract 1)
    new_line: the new line to replace the old line'''
    with open(FILE_PATH, "r") as file:
        lines = file.readlines()    # Read all lines from the file
    
    # Modify the line
    indent = preserve_indentation(lines[line_num-1])
    lines[line_num-1] = f"{indent}{new_line}\n"

    # Write the modified lines back to the file
    with open(FILE_PATH, "w") as file:
        file.writelines(lines)


def select_directory(entry_var):
    folder_selected = filedialog.askdirectory()
    if folder_selected:  # Only update if a folder was selected
        entry_var.set(folder_selected)

def check_process_finished(app_state, selected_folder, image_frame, root):
    process = app_state.scan_process
    if process.poll() is None:
        # Process still running, check again after 500 ms
        root.after(500, check_process_finished, app_state, selected_folder, image_frame, root)
    else:
        # Process finished
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            # There was an error
            error_msg = stderr.decode('utf-8') if stderr else "Unknown error occurred."
            print("Error:", error_msg)
            tk.messagebox.showerror("Process Error", f"The process failed with the following error:\n\n{error_msg}")
        else:
            print("Process completed.")
            load_plots(selected_folder, image_frame)
            

def run_script(app_state, entry_var, image_frame, file_var, root, console_output):
    selected_folder = entry_var.get()
    if selected_folder:
        selected_folder = selected_folder.replace("/", "\\")
        try:
            console_output.config(state='normal')
            console_output.delete('1.0', tk.END)
            console_output.config(state='disabled')
            # Start subprocess with stdout and stderr piped
            process = subprocess.Popen(
                ["python", file_var.get(), selected_folder],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,  # get text strings instead of bytes
                shell=True
            )
            app_state.set_scan_process(process)

            # Start reading output asynchronously
            def read_output():
                for line in process.stdout:
                    console_output.config(state='normal')
                    console_output.insert(tk.END, line)
                    console_output.see(tk.END)
                    console_output.config(state='disabled')
                for line in process.stderr:
                    console_output.config(state='normal')
                    console_output.insert(tk.END, line)
                    console_output.see(tk.END)
                    console_output.config(state='disabled')

            import threading
            threading.Thread(target=read_output, daemon=True).start()

            # If your original code loads plots, keep that behavior here as needed
            if file_var.get()=='nmr_2D.py':
                root.after(5000)
                load_latest_plot_while_running(app_state, image_frame, root, script_name=file_var.get())
            else:
                root.after(500, check_process_finished, app_state, selected_folder, image_frame, root)

        except Exception as e:
            tk.messagebox.showerror("Execution Error", f"Error: {e}")
    else:
        print("No folder selected")

def stop_script(app_state):
    app_state.stop_scan_process()
    
def get_latest_directory(parent_folder):
    """Find the most recently modified directory inside the parent folder."""
    # Find complete path to all the subdirectories inside the parent folder
    subdirs = [os.path.join(parent_folder, d) for d in os.listdir(parent_folder) if os.path.isdir(os.path.join(parent_folder, d))]
    
    if not subdirs:
        return None  # No subdirectories found
    
    latest_dir = max(subdirs, key=os.path.getmtime)  # Find latest modified folder
    return latest_dir

def load_plots(parent_folder, image_frame):
    """Load the plots from the most recently modified directory inside the parent folder."""
    latest_dir = get_latest_directory(parent_folder)
    if latest_dir is None:
        print("No subdirectories found")
        return  # No subdirectories found
    
    # Find all the image files in the latest directory
    image_files = sorted(glob.glob(os.path.join(latest_dir, "*.png")))
    if not image_files:
        print("No images found in", latest_dir)
        return  # No image files found
    
    print(f'Data saved to: {latest_dir}')
    # clear previous images
    for widget in image_frame.winfo_children():
        widget.destroy()
    
    # Load the images in the frame
    # for image_file in image_files:
    #     image = Image.open(image_file)
    #     photo = ImageTk.PhotoImage(image)
    #     label = tk.Label(image_frame, image=photo)
    #     label.image = photo
    #     label.pack()
    images = []
    # for image in image_files:
    #     img = Image.open(image)
    #     img = img.resize((400, 300))  # Resize for display
    #     img_tk = ImageTk.PhotoImage(img)
    #
    #     label = tk.Label(image_frame, image=img_tk)
    #     label.image = img_tk  # Prevent garbage collection
    #     label.pack(side="left", padx=10)
    #     images.append(img_tk)
        
    # create a new top-level window to display the images
    top = tk.Toplevel()
    top.title("NMR Scan Results")
    #####################################
    # plot the images in 3 by 2 array in new window
    # for i, image_file in enumerate(image_files):
    #     image = Image.open(image_file)
    #     image = image.resize((400, 300))  # Resize for display
    #     photo = ImageTk.PhotoImage(image)
    #     label = tk.Label(top, image=photo)
    #     label.image = photo
    #     label.grid(row=i//3, column=i%3)
    #
    # return images
    #########################################
    # make image resizable based on the window
    # Frame to hold all image labels
    top.geometry("1200x800")  # Set a good initial size

    container = tk.Frame(top)
    container.pack(fill="both", expand=True)

    original_images = []
    image_labels = []
    frames = []

    rows = (len(image_files) + 2) // 3
    for i, image_file in enumerate(image_files):
        image = Image.open(image_file)
        original_images.append(image)

        frame = tk.Frame(container, bg="black", bd=1, relief="solid")
        frame.grid(row=i // 3, column=i % 3, sticky="nsew", padx=5, pady=5)
        frames.append(frame)

        container.grid_rowconfigure(i // 3, weight=1)
        container.grid_columnconfigure(i % 3, weight=1)

        label = tk.Label(frame)
        label.pack(fill="both", expand=True)
        image_labels.append(label)

    resize_job = [None]

    def resize_images(event=None):
        if resize_job[0]:
            top.after_cancel(resize_job[0])

        def do_resize():
            for i, frame in enumerate(frames):
                if i >= len(original_images):
                    continue
                w = frame.winfo_width()
                h = frame.winfo_height()
                if w > 10 and h > 10:
                    resized = original_images[i].resize((w, h), Image.Resampling.LANCZOS)
                    img_tk = ImageTk.PhotoImage(resized)
                    image_labels[i].config(image=img_tk)
                    image_labels[i].image = img_tk  # Prevent GC

        resize_job[0] = top.after(50, do_resize)

    top.bind("<Configure>", resize_images)

    return image_labels

def load_latest_plot_while_running(app_state, image_frame, root, script_name="Monitor_Noise.py"):
    process = app_state.scan_process

    if process is None:
        print("No process running.")
        return

    if process.poll() is not None:
        # Process finished
        if process.returncode != 0:
            # Error occurred
            stdout, stderr = process.communicate()
            error_msg = stderr.decode("utf-8") if stderr else "Unknown error occurred."
            print("Error from process:", error_msg)
            tk.messagebox.showerror("Process Error", f"The process failed with the following error:\n\n{error_msg}")
        else:
            print("Process finished normally.")
        return  # Stop re-calling itself

    # Process is still running; try to load latest plot
    latest_dir = get_latest_directory("D:/NMR_DATA")
    if not latest_dir:
        root.after(1000, load_latest_plot_while_running, app_state, image_frame, root, script_name)
        return

    image_files = sorted(glob.glob(os.path.join(latest_dir, "*.png")), key=os.path.getmtime)
    if not image_files:
        root.after(1000, load_latest_plot_while_running, app_state, image_frame, root, script_name)
        return

    latest_image_path = image_files[-1]

    # Clear previous widgets
    for widget in image_frame.winfo_children():
        widget.destroy()

    try:
        original_image = Image.open(latest_image_path)

        # Create a Canvas to allow flexible resizing
        C_width = image_frame.winfo_width()
        C_height = image_frame.winfo_height()
        canvas = tk.Canvas(image_frame, bg="black", width=1000, height=500)
        canvas.pack(fill="both", expand=True)

        def update_resized_image(event=None):
            canvas_width = canvas.winfo_width()
            canvas_height = canvas.winfo_height()

            if canvas_width > 1 and canvas_height > 1:
                resized_image = original_image.resize((canvas_width, canvas_height), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(resized_image)

                canvas.image = photo  # Keep reference
                canvas.delete("all")  # Clear previous
                canvas.create_image(canvas_width // 2, canvas_height // 2, anchor="center", image=photo)

        # Bind canvas resizing
        canvas.bind("<Configure>", update_resized_image)

    except Exception as e:
        print(f"Error loading image: {e}")

    # Schedule next check
    root.after(1000, load_latest_plot_while_running, app_state, image_frame, root, script_name)
    
def update_selected_file(file_var):
    """Displays the selected Python file when ComboBox value changes."""
    selected_file = file_var.get()
    print(f"Selected file: {selected_file}")

def list_python_files():
    """Lists all Python (.py) files in the current directory."""
    return sorted(glob.glob("NMR*.py"))  # Get only Python files that start with 'NMR'

def open_parameter_popup(root, FILE_PATH):
    popup = ParameterPopup(root, FILE_PATH)
    popup.grab_set()  # Make the popup modal


# def change_config_files(FILE_PATH, line_num, new_line1, new_line2):
#     '''Modifies a specific line in the file.
#     FILE_PATH: the path to the file containing the parameters
#     line_num: the first line number to be modified
#     new_line1: the new line to replace the first line in the file
#     new_line2: the new line to replace the second line in the file'''
#     modify_line(FILE_PATH, line_num, new_line1)
#     modify_line(FILE_PATH, line_num+1, new_line2)


def main():
    app_state = Appstate()

    # FILE_PATH = "sys_configs/phenc_conf_halbach_v07test_240624_honey.py"

    # Create the main window
    root = tk.Tk()
    root.title('NMR System GUI')

    # # Create a button widget for run
    # run_cpmg_button = tk.Button(root, text='Run NMR', command=run_nmr(app_state))
    # run_cpmg_button.pack(pady=20)

    entry_var = tk.StringVar(value="D:\\NMR_DATA")

    # Create a frame for scanning setup in tkinter
    frame_scan = tk.Frame(root)
    frame_scan.pack(pady=20)

    tk.Label(frame_scan, text="Select Directory to save scan data:").grid(row=0, column=0, padx=10)
    entry = tk.Entry(frame_scan, textvariable=entry_var, width=60)
    entry.grid(row=0, column=1, padx=10)

    browse_button = tk.Button(frame_scan, text="Browse", command=lambda: select_directory(entry_var))
    browse_button.grid(row=0, column=2, padx=10)

    image_frame = tk.Frame(root)  # Frame for displaying images
    image_frame.pack(pady=20)
    

    
    ########## Monitor noise script currently doesn't work on the newest system
    # # Create button that monitors noise and stops monitoring noise
    # monitor_noise_process = ProcessState("Monitor_Noise.py")            # Initialize Monitor_Noise class to track the python file processes
    # monitor_noise_button = tk.Button(frame_scan, text="Monitor Noise", command=lambda: monitor_noise_process.start_process())
    # monitor_noise_button.grid(row=1, column=0, padx = 30, pady=15)                    
    # monitor_noise_stop = tk.Button(frame_scan, text="Stop Monitoring Noise", command=lambda: monitor_noise_process.stop_process())
    # monitor_noise_stop.grid(row=1, column=1)
    

    # Get a list of python files that does different scans
    python_files = list_python_files()

    # Create a label widget for displaying the scans
    scan_label = tk.Label(frame_scan, text="Select the scan to run:")
    scan_label.grid(row=2, column=0, padx=10, pady=10)

    # Create a ComboBox widget for selecting the Python file
    file_var = tk.StringVar(value=python_files[0])
    file_combobox = ttk.Combobox(frame_scan, textvariable=file_var, values=python_files, state="readonly")
    file_combobox.bind("<<ComboboxSelected>>", lambda event: update_selected_file(file_var))
    file_combobox.grid(row=2, column=1, padx=10, pady=10)

    # Create a button to open the parameter edit popup
    open_param_button = tk.Button(frame_scan, text="Edit Scan Parameters", command=lambda: open_parameter_popup(root, "sys_configs/"+str(file_var.get())))
    open_param_button.grid(row=2, column=2, padx=10, pady=10)

    # run_button = tk.Button(frame_scan, text="Run Scan", command=lambda: run_script(app_state, entry_var, image_frame, file_var, root))
    # run_button.grid(row=3, column=1, pady=20)
    run_button = tk.Button(frame_scan, text="Run Scan", command=lambda: run_script(app_state, entry_var, image_frame, file_var, root, console_output))
    run_button.grid(row=3, column=1, pady=20)
    
    
    stop_button = tk.Button(frame_scan, text="Stop Scan", command=lambda: stop_script(app_state))
    stop_button.grid(row=3, column=2, padx=10, pady=20)
    
    # Frame for console output
    console_frame = tk.Frame(root)
    console_frame.pack(pady=10, fill="both", expand=True)
    
    console_output = scrolledtext.ScrolledText(console_frame, height=10, state='disabled')
    console_output.pack(fill="both", expand=True)


    # Create a label widget
    # label = tk.Label(root, text='Parameters')

    # # Create labels for current value of parameters and buttons for updating them
    # cpmg_freq_label = tk.Label(root, text='CPMG Frequency: ')
    # read_parameters(app_state.get_config_FILE_PATH(), cpmg_freq_label, "cpmg_freq", "MHz", display_name="CPMG Frequency")

    # # Create a button widget for updating the parameter
    # cpmg_freq_entry = tk.Entry(root) 
    # update_cpmg_freq_button = tk.Button(root, text='Update CPMG Frequency', command=lambda: update_parameter(app_state.get_config_FILE_PATH(), cpmg_freq_label, "cpmg_freq", cpmg_freq_entry.get(), "MHz", display_name="CPMG Frequency"))
    

    # Create a radio button to select the system configuration file
    var = tk.StringVar(value="Honey")

    # # Create Radio Buttons with multiple commands using lambda
    # DopedWater_radioButton = tk.Radiobutton(
    #     root, 
    #     text="Doped Water", 
    #     variable=var, 
    #     value="Doped Water", 
    #     command=lambda: [modify_line('nmr_cpmg.py','from sys_configs.phenc_conf_halbach_v07test_240624_dopedwater import phenc_conf_halbach_v07test_240624_dopedwater'), modify_line('nmr_cpmg.py',55, 'phenc_conf = phenc_conf_halbach_v07test_240624_dopedwater()'), label.config(text=f"You selected: {var.get()}"), app_state.update_config_FILE_PATH("sys_configs/phenc_conf_halbach_v07test_240624_dopedwater.py"), read_parameters(app_state.get_config_FILE_PATH(), cpmg_freq_label, "cpmg_freq", "MHz", display_name="CPMG Frequency")]
    # )
    # Honey_radioButton = tk.Radiobutton(
    #     root, 
    #     text="Honey", 
    #     variable=var, 
    #     value="Honey", 
    #     command=lambda: [modify_line('nmr_cpmg.py',54,'from sys_configs.phenc_conf_halbach_v07test_240624_honey import phenc_conf_halbach_v07test_240624_honey'), \
    #     modify_line('nmr_cpmg.py',55, 'phenc_conf = phenc_conf_halbach_v07test_240624_honey()'), \
    #     label.config(text=f"You selected: {var.get()}"), \
    #     app_state.update_config_FILE_PATH("sys_configs/phenc_conf_halbach_v07test_240624_honey.py"), \
    #     read_parameters(app_state.get_config_FILE_PATH(), cpmg_freq_label, "cpmg_freq", "MHz", display_name="CPMG Frequency")]
    # )

    # Pack everything
    # DopedWater_radioButton.pack(anchor="w", padx=20)
    # Honey_radioButton.pack(anchor="w", padx=20)
    # label.pack()
    # cpmg_freq_label.pack(pady=5)
    # cpmg_freq_entry.pack(pady=5)
    # update_cpmg_freq_button.pack(pady=10)

    # Start the GUI event loop
    root.mainloop()

if __name__ == "__main__":
    main()
    
    
    
    # add example scripts for the parameters
    # add more pulse sequence into the user
    # add data analysis to the script part