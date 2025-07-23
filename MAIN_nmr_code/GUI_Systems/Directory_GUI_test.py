import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
import os
import subprocess
from test_process import test_process

def select_directory():
    folder_selected = filedialog.askdirectory()
    if folder_selected:  # Only update if a folder was selected
        entry_var.set(folder_selected)

def run_script():
    selected_folder = entry_var.get()
    if selected_folder:
        selected_folder = selected_folder.replace("/", "\\")
        # test_process(selected_folder)
        subprocess.Popen(["python", "test_process.py", selected_folder], shell=True)  #make sure it is ran in the shell so we can use sys.argv to check the arguments
        # Run the script with the selected folder
    else:
        print("No folder selected")


root = tk.Tk()
root.title("Select a directory to save NMR Data")

entry_var = tk.StringVar(value="D:\\NMR_DATA")

frame = tk.Frame(root)
frame.pack(pady=20)

tk.Label(frame, text="Data Directory Path:").grid(row=0, column=0, padx=10)
entry = tk.Entry(frame, textvariable=entry_var, width=80)
entry.grid(row=0, column=1, padx=10)

browse_button = tk.Button(frame, text="Browse", command=select_directory)
browse_button.grid(row=0, column=2, padx=10)

run_button = tk.Button(root, text="Run Script", command=run_script)
run_button.pack(pady=20)

root.mainloop()
