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
        self.basePath = "C:\\Users\\47975\\Desktop\\spec\\test\\"    
        self.wavelengths = [6383, 6402, 6507, 6533, 6599, 6678, 6717]

        # Create widgets
        self.directory_label = tk.Label(self, text="Enter Directory Path:")
        self.directory_label.pack(pady=(20, 5))

        self.directory_entry = tk.Entry(self)
        self.directory_entry.insert(0, os.path.join(self.basePath, "lights\\"))  # Set the default directory in the entry field
        self.directory_entry.pack(pady=(0, 10), padx=10, fill=tk.X)

        self.run_button = tk.Button(self, text="Run", command=self.Execute)
        self.run_button.pack(pady=5)

        self.result_label = tk.Label(self, text="", font=("Helvetica", 12))
        self.result_label.pack()
                          
    def Execute(self):
        lightsList = getFiles(os.path.join(self.basePath, "lights\\"), ".png")
        darkFrame = getCalibrationFrame(1411, 2072, os.path.join(self.basePath, "darks\\"), 0)
        stackFrame = np.full((1411, 2072), 0, dtype=np.float32)

        for x in lightsList:
            lightFrame = np.asarray(imread(x,IMREAD_ANYDEPTH))
            lightFrame = lightFrame.astype(np.float32)/(255**lightFrame.dtype.itemsize)
            lightFrame -= darkFrame
            addWeighted(stackFrame, 1, lightFrame, 1 / len(lightsList), 0.0, stackFrame)
        
        imwrite(os.path.join(self.basePath, "stackFrame.tif"), stackFrame)
        
        calvector = np.asarray(imread(os.path.join(self.basePath, "wcal.png"),IMREAD_ANYDEPTH))
        
        xpoints = np.mean(stackFrame[700:750, 1:], axis = 0)
        calpoints = np.mean(calvector[700:750, 1:], axis = 0)
        
        edges = np.where(abs(np.diff(np.where(calpoints == 255, calpoints, 0))) == 255)[0]
    
        lines = []

        for i in range(len(edges) - 1):
            if(i%2==0):
                lines.append((edges[i] + 1 + edges[i + 1])/2)


        #self.display_results(str(self.wavelengths))  # Display the results

        #params, covariance = curve_fit(linear_function, lines, wavelengths)

        x_fit = np.arange(1, len(xpoints) + 1)

        # Extract the parameters
        params, covariance = curve_fit(quadratic_function, lines, self.wavelengths)
        a, b, c = params
        y_fit = quadratic_function(x_fit, a, b, c)
           
        #y_fit = linear_function(x_fit, m, c)
        plt.plot(lines, self.wavelengths, 'o', color='blue', label='Neon lines data')
        plt.plot(x_fit, y_fit, color='red', label='Fit')
        plt.plot(top = 1, bottom = 0, right = 1, left = 0, hspace = 0, wspace = 0)
        plt.xlabel('Pixels')
        plt.ylabel('Wavelength ($\AA$)')
        plt.legend()
        plt.show()  
    
        plt.plot(y_fit, xpoints, '-', label='Beta CrB')
        plt.plot(top = 1, bottom = 0, right = 1, left = 0, hspace = 0, wspace = 0)
        plt.xlabel('Wavelength ($\AA$)')
        plt.ylabel('Intensity')
        plt.legend()
        plt.show()
            
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

def linear_function(x, a, b):
    return a * x + b

def quadratic_function(x, a, b, c):
    return a * x * x + b * x + c

def cubic_function(x, a, b, c, d):
    return a * x * x * x + b * x * x + c * x + d

if __name__ == "__main__":
    app = Application()
    app.mainloop()
