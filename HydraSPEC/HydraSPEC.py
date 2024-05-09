from cv2 import imshow, imread, imwrite, IMREAD_GRAYSCALE, IMREAD_ANYDEPTH, addWeighted, flip
from matplotlib import pyplot as plt
from scipy.optimize import curve_fit
import numpy as np
import os
import tkinter as tk

class Application(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("HydraSPEC")
        self.geometry("400x350")
        self.iconbitmap('python.ico')

        self.basePath = "C:\\Users\\47975\\Desktop\\spec\\test2\\"    
        #self.wavelengths = [6383, 6402, 6507, 6533, 6599, 6678, 6717]
        self.wavelengths = [6598.95, 6678.28, 6717.704]

        self.directoryLabel = tk.Label(self, text="Enter Directory Path:")
        self.directoryLabel.pack(pady=(20, 5))

        self.directoryEntry = tk.Entry(self)
        self.directoryEntry.insert(0, self.basePath)  
        self.directoryEntry.pack(pady=(0, 10), padx=10, fill=tk.X)

        self.stackButton = tk.Button(self, text="Stack", command=self.Stack)        
        self.calButton = tk.Button(self, text="Calibrate", command=self.Calibrate)
        self.stackButton.pack(pady=10)
        self.calButton.pack(pady=10)

        self.resultLabel = tk.Label(self, text="", font=("Helvetica", 12))
        self.resultLabel.pack()
        
        self.wcalSelector = tk.IntVar()
        self.wcalSelector.set(2)
             
        self.r1 = tk.Radiobutton(self, variable=self.wcalSelector, value=1, text='Linear')
        self.r2 = tk.Radiobutton(self, variable=self.wcalSelector, value=2, text='Quadratic')
        self.r1.pack(side=tk.LEFT, padx=10)
        self.r2.pack(side=tk.LEFT, padx=10)
        
        self.showWaveCal = tk.IntVar()
        self.showWaveCal.set(0)
        self.c1 = tk.Checkbutton(self, text="Show wavelength calibration", variable=self.showWaveCal, onvalue=1, offvalue=0)
        self.c1.pack(side=tk.LEFT, pady=10)
                          
    def Stack(self):        
        lightsList = getFiles(os.path.join(self.basePath, "lights"), ".png")
        
        self.resultLabel.config(text="Stacking " + str(len(lightsList)) + " frames...", fg="red")

        i = 0
        for x in lightsList:
            lightFrame = np.asarray(imread(x,IMREAD_ANYDEPTH))
            if(i == 0):
                height, width = lightFrame.shape[:2]
                darkFrame = getCalibrationFrame(height, width, os.path.join(self.basePath, "darks"), 0)
                biasFrame = getCalibrationFrame(height, width, os.path.join(self.basePath, "bias"), 0)
                flatFrame = getCalibrationFrame(height, width, os.path.join(self.basePath, "flats"), 1)
                flatFrame = flatFrame-biasFrame               
                stackFrame = np.full((height, width), 0, dtype=np.float32)
                
            lightFrame = lightFrame.astype(np.float32)/(255**lightFrame.dtype.itemsize)
            lightFrame -= darkFrame
            #lightFrame /= flatFrame
            addWeighted(stackFrame, 1, lightFrame, 1 / len(lightsList), 0.0, stackFrame)
        
        stackFrame = flip(stackFrame, 1)
        imwrite(os.path.join(self.basePath, "out", "stackFrame.tif"), stackFrame)
        
      
    def Calibrate(self):
        
        if os.path.exists(os.path.join(self.basePath, "out", "stackFrame.tif") and os.path.join(self.basePath, "wcal", "wcal.png")):

            stackFrame = imread(os.path.join(self.basePath, "out", "stackFrame.tif"), IMREAD_ANYDEPTH)

            calvector = np.asarray(imread(os.path.join(self.basePath, "wcal", "wcal.png"), IMREAD_ANYDEPTH))
        
            #intensityCal = np.mean(flatFrame[1205:1215, 1:], axis = 0)    
            #coefficients = np.polyfit(np.arange(1, len(intensityCal) + 1), intensityCal, 2)
            #smoothedintensityCal = np.polyval(coefficients, np.arange(1, len(intensityCal) + 1))
        
            xpoints = np.mean(stackFrame[1205:1215, 1:], axis = 0) #/np.flipud(smoothedintensityCal)

            calpoints = np.mean(calvector[1205:1215, 1:], axis = 0)
        
            #edges = np.where(abs(np.diff(np.where(calpoints == 255, calpoints, 0))) == 255)[0]
            #(255**calibration_frame.dtype.itemsize)
    
            #lines = []

            #for i in range(len(edges) - 1):
            #    if(i%2==0):
            #        lines.append((edges[i] + 1 + edges[i + 1])/2)
                
            lines = [606, 808, 1216]
            lines = np.flipud(lines)

            #self.display_results(str(self.wavelengths))  # Display the results

            x_fit = np.arange(1, len(xpoints) + 1)

            if(self.wcalSelector.get() == 1):
                params, covariance = curve_fit(linearFunction, lines, self.wavelengths)
                y_fit = linearFunction(x_fit, params[0], params[1])

            else:
                params, covariance = curve_fit(quadraticFunction, lines, self.wavelengths)
                y_fit = quadraticFunction(x_fit, params[0], params[1], params[2])
           
            if(self.showWaveCal.get() == 1):
                plt.plot(lines, self.wavelengths, 'o', color='blue', label='Calibration lines data')
                plt.plot(x_fit, y_fit, color='red', label='Fit')
                plt.plot(top = 1, bottom = 0, right = 1, left = 0, hspace = 0, wspace = 0)
                plt.xlabel('Pixels')
                plt.ylabel('Wavelength ($\AA$)')
                plt.legend()
                plt.show()  
    
            plt.plot(y_fit, xpoints, '-', label='Beta CrB')
        
            plt.axvline(x = self.wavelengths[0], color = 'orange', label = 'Ne 6599.0')
            plt.axvline(x = self.wavelengths[1], color = 'orange', label = 'Ne 6678.3')
            plt.axvline(x = self.wavelengths[2], color = 'orange', label = 'Ne 6717.7')
      
            plt.axvline(x = 6562.8, color = 'y', label = 'Ha 6562.8')
            plt.axvline(x = 6645.1, color = 'r', label = 'Eu 6645.1')
            plt.axvline(x = 6707.8, color = 'k', label = 'Li 6707.8')
            plt.axvline(x = 6717.7, color = 'r', label = 'Ca 6717.7')
            plt.plot(top = 1, bottom = 0, right = 1, left = 0, hspace = 0, wspace = 0)
            plt.xlabel('Wavelength ($\AA$)')
            plt.ylabel('Intensity')
            plt.legend()
            plt.show()
        
            
    def display_results(self, results):
        self.resultLabel.config(text="\n".join(results))

def getFiles(filepath, ext):   
    filenames = []
    for root, dirs, files in os.walk(filepath):
        for file in files:
            if file.endswith(ext):
                filenames.append(os.path.join(root, file))
  
    return filenames

def getLights(inputDir, ext):
    lightsList = getFiles(inputDir, ext)
    return lightsList

def getCalibrationFrame(ySize, xSize, calibrationPath, defaultValue):
    masterFrame = np.full((ySize, xSize), defaultValue, dtype=np.float32)

    if os.path.exists(os.path.join(calibrationPath, "masterFrame.tif")):
        tmpFrame = imread(os.path.join(calibrationPath, "masterFrame.tif"), IMREAD_ANYDEPTH)
        if tmpFrame.shape[1] == masterFrame.shape[1] and tmpFrame.shape[0] == masterFrame.shape[0]:
            masterFrame = tmpFrame
    else:
        calibrationFrameArray = getFiles(calibrationPath, ".png")
        if calibrationFrameArray:
            masterFrame = np.full((ySize, xSize), 0, dtype=np.float32)
            for calibrationFramePath in calibrationFrameArray:
                calibrationFrame = imread(calibrationFramePath, IMREAD_ANYDEPTH)
                if calibrationFrame.shape[1] == masterFrame.shape[1] and calibrationFrame.shape[0] == masterFrame.shape[0]:
                    calibrationFrame = calibrationFrame.astype(np.float32)/(255**calibrationFrame.dtype.itemsize)
                    addWeighted(masterFrame, 1, calibrationFrame, 1 / len(calibrationFrameArray), 0.0, masterFrame)
            imwrite(os.path.join(calibrationPath, "masterFrame.tif"), masterFrame)

    return masterFrame

def linearFunction(x, a, b):
    return a * x + b

def quadraticFunction(x, a, b, c):
    return a * x * x + b * x + c

def cubicFunction(x, a, b, c, d):
    return a * x * x * x + b * x * x + c * x + d

if __name__ == "__main__":
    app = Application()
    app.mainloop()
