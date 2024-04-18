import tkinter as tk
from cv2 import imshow, imread, imwrite, IMREAD_GRAYSCALE, IMREAD_ANYDEPTH, addWeighted
from matplotlib import pyplot as plt
from tkinter import FLAT, filedialog
import os
from pathlib import Path
from scipy.optimize import curve_fit
import numpy as np

class Application(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("File Processing App")
        self.geometry("400x350")

        self.basePath = "C:\\Users\\47975\\Desktop\\spec\\test2\\"    
        #self.wavelengths = [6383, 6402, 6507, 6533, 6599, 6678, 6717]
        self.wavelengths = [6599, 6678, 6717]

        self.directory_label = tk.Label(self, text="Enter Directory Path:")
        self.directory_label.pack(pady=(20, 5))

        self.directory_entry = tk.Entry(self)
        self.directory_entry.insert(0, self.basePath)  
        self.directory_entry.pack(pady=(0, 10), padx=10, fill=tk.X)

        self.run_button = tk.Button(self, text="Run", command=self.Execute)
        self.run_button.pack(pady=5)

        self.result_label = tk.Label(self, text="", font=("Helvetica", 12))
        self.result_label.pack()
        
        self.wcalSelector = tk.IntVar()
        self.wcalSelector.set(1)
             
        self.r1 = tk.Radiobutton(self, variable=self.wcalSelector, value=1, text='Linear')
        self.r2 = tk.Radiobutton(self, variable=self.wcalSelector, value=2, text='Quadratic')
        self.r1.pack(pady=10)
        self.r2.pack(pady=10)

                          
    def Execute(self):
        lightsList = getFiles(os.path.join(self.basePath, "lights\\"), ".png")
        
        darkFrame = getCalibrationFrame(1504, 1504, os.path.join(self.basePath, "darks\\"), 0)
        biasFrame = getCalibrationFrame(1504, 1504, os.path.join(self.basePath, "bias\\"), 0)
        flatFrame = getCalibrationFrame(1504, 1504, os.path.join(self.basePath, "flats\\"), 1)
        flatFrame = flatFrame-biasFrame
                
        stackFrame = np.full((1504, 1504), 0, dtype=np.float32)

        for x in lightsList:
            lightFrame = np.asarray(imread(x,IMREAD_ANYDEPTH))
            lightFrame = lightFrame.astype(np.float32)/(255**lightFrame.dtype.itemsize)
            lightFrame -= darkFrame
            addWeighted(stackFrame, 1, lightFrame, 1 / len(lightsList), 0.0, stackFrame)
        
        imwrite(os.path.join(self.basePath, "stackFrame.tif"), stackFrame)
        
        calvector = np.asarray(imread(os.path.join(self.basePath, "wcal.png"), IMREAD_ANYDEPTH))
        
        #intensityCal = np.mean(flatFrame[1205:1215, 1:], axis = 0)
        
        #coefficients = np.polyfit(np.arange(1, len(intensityCal) + 1), intensityCal, 2)

        #smoothedintensityCal = np.polyval(coefficients, np.arange(1, len(intensityCal) + 1))
        
        xpoints = np.mean(stackFrame[1205:1215, 1:], axis = 0) #/np.flipud(smoothedintensityCal)

        calpoints = np.mean(calvector[1205:1215, 1:], axis = 0)
        
        edges = np.where(abs(np.diff(np.where(calpoints == 255, calpoints, 0))) == 255)[0]
        #(255**calibration_frame.dtype.itemsize)
    
        lines = []

        for i in range(len(edges) - 1):
            if(i%2==0):
                lines.append((edges[i] + 1 + edges[i + 1])/2)
                
        lines = [1216,808,606]

        #self.display_results(str(self.wavelengths))  # Display the results

        x_fit = np.arange(1, len(xpoints) + 1)

        if(self.wcalSelector.get() == 1):
            params, covariance = curve_fit(linearFunction, lines, self.wavelengths)
            y_fit = linearFunction(x_fit, params[0], params[1])

        else:
            params, covariance = curve_fit(quadraticFunction, lines, self.wavelengths)
            y_fit = quadraticFunction(x_fit, params[0], params[1], params[2])
           
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
            master_frame = np.full((y_size, x_size), 0, dtype=np.float32)
            for calibration_frame_path in calibration_frame_array:
                calibration_frame = imread(calibration_frame_path, IMREAD_ANYDEPTH)
                if calibration_frame.shape[1] == master_frame.shape[1] and calibration_frame.shape[0] == master_frame.shape[0]:
                    calibration_frame = calibration_frame.astype(np.float32)/(255**calibration_frame.dtype.itemsize)
                    addWeighted(master_frame, 1, calibration_frame, 1 / len(calibration_frame_array), 0.0, master_frame)
            imwrite(os.path.join(calibration_path, "masterFrame.tif"), master_frame)

    return master_frame

def linearFunction(x, a, b):
    return a * x + b

def quadraticFunction(x, a, b, c):
    return a * x * x + b * x + c

def cubicFunction(x, a, b, c, d):
    return a * x * x * x + b * x * x + c * x + d

if __name__ == "__main__":
    app = Application()
    app.mainloop()
