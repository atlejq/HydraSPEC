import tkinter as tk
from cv2 import imshow, imread, imwrite, IMREAD_GRAYSCALE, IMREAD_ANYDEPTH, addWeighted
from matplotlib import pyplot as plt
from tkinter import filedialog
import os
from pathlib import Path
from scipy.optimize import curve_fit
import numpy as np

class Application(tk.Tk):
    def __init__(self):
        super().__init__()

        # Set the title and size of the window
        self.title("File Processing App")
        self.geometry("400x350")

        # Set the default directory
        self.lights_directory = "C:\\Users\\47975\\Desktop\\spec\\test\\lights\\"
        self.darks_directory = "C:\\Users\\47975\\Desktop\\spec\\test\\darks\\"
        
        wavelengths = [6383, 6402, 6507, 6533, 6599, 6678, 6717]
    
        calvector = np.asarray(imread("C:\\Users\\47975\\Desktop\\spec\\test\\wcal.png",IMREAD_ANYDEPTH))

        #biasFrame = get_calibration_frame(1411, 2072, "C:\\Users\\47975\\Desktop\\spec\\test\\bias\\", 0)
        #darkFrame = get_calibration_frame(1411, 2072, "C:\\Users\\47975\\Desktop\\spec\\test\\darks\\", 0)

        # Create widgets
        self.directory_label = tk.Label(self, text="Enter Directory Path:")
        self.directory_label.pack(pady=(20, 5))

        self.directory_entry = tk.Entry(self)
        self.directory_entry.insert(0, self.lights_directory)  # Set the default directory in the entry field
        self.directory_entry.pack(pady=(0, 10), padx=10, fill=tk.X)

        self.run_button = tk.Button(self, text="Run", command=self.Execute)
        self.run_button.pack(pady=5)

        self.result_label = tk.Label(self, text="", font=("Helvetica", 12))
        self.result_label.pack()
                          
    def Execute(self):
        lightsList = getFiles(self.lights_directory, ".png")
        darkFrame = getCalibrationFrame(1411, 2072, self.darks_directory, 0)
        self.display_results(lightsList)  # Display the results
        stackFrame = np.full((1411, 2072), 0, dtype=np.float32)

        for x in lightsList:
            lightFrame = np.asarray(imread(x,IMREAD_ANYDEPTH))
            lightFrame = lightFrame.astype(np.float32)/(255**lightFrame.dtype.itemsize)
            lightFrame -= darkFrame
            addWeighted(stackFrame, 1, lightFrame, 1 / len(lightsList), 0.0, stackFrame)
        
        imwrite(os.path.join("C:\\Users\\47975\\Desktop\\spec\\test\\", "stackFrame.tif"), stackFrame)
            
    def display_results(self, results):
        self.result_label.config(text="\n".join(results))

def getFiles(path, ext):
    files = []
    if os.path.exists(path):
        for p in Path(path).rglob(f'*{ext}'):
            files.append(str(p))
    return files

def getLights(inputDir, ext):
    lightsList = getFiles(inputDir, ext)
    return lightsList

def getCalibrationFrame(y_size, x_size, calibration_path, default_value):
    master_frame = np.full((y_size, x_size), default_value, dtype=np.float32)

    if os.path.exists(os.path.join(calibration_path, "masterFrame.tif")):
        tmp_calibration_frame = imread(os.path.join(calibration_path, "masterFrame.tif"), IMREAD_ANYDEPTH)
        if tmp_calibration_frame.shape[1] == master_frame.shape[1] and tmp_calibration_frame.shape[0] == master_frame.shape[0]:
            master_frame = tmp_calibration_frame
    else:
        calibration_frame_array = getFiles(calibration_path, ".png")
        if calibration_frame_array:
            for calibration_frame_path in calibration_frame_array:
                calibration_frame = imread(calibration_frame_path, IMREAD_ANYDEPTH)
                if calibration_frame.shape[1] == master_frame.shape[1] and calibration_frame.shape[0] == master_frame.shape[0]:
                    calibration_frame = calibration_frame.astype(np.float32) / 255.0
                    addWeighted(master_frame, 1, calibration_frame, 1 / len(calibration_frame_array), 0.0, master_frame)
            imwrite(os.path.join(calibration_path, "masterFrame.tif"), master_frame)

    return master_frame

if __name__ == "__main__":
    app = Application()
    app.mainloop()
