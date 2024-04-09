import tkinter as tk
from tkinter import filedialog
import os

class Application(tk.Tk):
    def __init__(self):
        super().__init__()

        # Set the title and size of the window
        self.title("File Processing App")
        self.geometry("400x350")

        # Set the default directory
        self.default_directory = "C:\\Users\\47975\\Desktop\\spec\\test\\lights\\"

        # Create widgets
        self.directory_label = tk.Label(self, text="Enter Directory Path:")
        self.directory_label.pack(pady=(20, 5))

        self.directory_entry = tk.Entry(self)
        self.directory_entry.insert(0, self.default_directory)  # Set the default directory in the entry field
        self.directory_entry.pack(pady=(0, 10), padx=10, fill=tk.X)

        self.run_button = tk.Button(self, text="Run", command=self.getFiles)
        self.run_button.pack(pady=5)

        self.result_label = tk.Label(self, text="", font=("Helvetica", 12))
        self.result_label.pack()
        
        self.lights = []

    def getFiles(self):
        for filename in os.listdir(self.default_directory):
            if filename.endswith(".png"):
                self.lights.append(filename)
                    
        self.display_results(self.lights)  # Display the results
            
        
    def display_results(self, results):
        self.result_label.config(text="\n".join(results))

if __name__ == "__main__":
    app = Application()
    app.mainloop()
