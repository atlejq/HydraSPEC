from cv2 import imshow, imread, imwrite, IMREAD_GRAYSCALE, IMREAD_ANYDEPTH, addWeighted, flip, warpAffine, INTER_CUBIC
from matplotlib import pyplot as plt
from scipy.optimize import curve_fit
import numpy as np
from os import walk, path
from tkinter import filedialog, Label, Button, Radiobutton, Checkbutton, IntVar, Tk
import csv

class Application(Tk):
    def __init__(self):
        super().__init__()

        self.title("HydraSPEC")
        self.geometry("700x250")
        self.iconbitmap('python.ico')    
        self.resizable(False,False)

        self.basePath = ""    
        self.outDir ="out"
        self.lightDir = "lights"
        self.darkDir = "darks"
        self.flatDir = "flats"
        self.biasDir = "bias"
        self.wcalDir = "wcal"
        
        self.spectraPos = 1205;
        self.spectraWidth = 20;
        
        #self.wavelengths = [6383, 6402, 6507, 6533, 6599, 6678, 6717]
        #self.wavelengths = [6598.95, 6678.28, 6717.704]

        self.directoryLabel = Label(self, text="")
        
        self.pathButton = Button(self, text="Select path", command=self.selectPath)        
        self.stackButton = Button(self, text="Stack", command=self.Stack)        
        self.calButton = Button(self, text="Calibrate", command=self.Calibrate)
        
        self.flipStack = IntVar()
        self.flipStack.set(0)
        
        self.showWaveCal = IntVar()
        self.showWaveCal.set(0)
        
        self.c1 = Checkbutton(self, text="Flip stack frame", variable=self.flipStack, onvalue=1, offvalue=0)
        self.c2 = Checkbutton(self, text="Show calibration", variable=self.showWaveCal, onvalue=1, offvalue=0)
        
        self.resultLabel = Label(self, text="")
       
        self.wcalSelector = IntVar()
        self.wcalSelector.set(2)
             
        self.r1 = Radiobutton(self, variable=self.wcalSelector, value=1, text='Linear')
        self.r2 = Radiobutton(self, variable=self.wcalSelector, value=2, text='Quadratic')
        self.r3 = Radiobutton(self, variable=self.wcalSelector, value=3, text='Cubic')
        self.r4 = Radiobutton(self, variable=self.wcalSelector, value=4, text='Quartic')
        
        self.directoryLabel.grid(row=0, column=3, sticky='w', padx = 20, pady=10)        
        self.pathButton.grid(row=0, column=0, sticky='w', padx = 20, pady=10)
        self.stackButton.grid(row=1, column=0, sticky='w', padx = 20, pady=10)
        self.calButton.grid(row=2, column=0, sticky='w', padx = 20, pady=10)
        self.c1.grid(row=0, column=1, sticky='w', padx = 20, pady=10)
        self.c2.grid(row=1, column=1, sticky='w', padx = 20, pady=10)   
        self.r1.grid(row=0, column=2, sticky='w', padx = 20, pady=10)
        self.r2.grid(row=1, column=2, sticky='w', padx = 20, pady=10)
        self.r3.grid(row=2, column=2, sticky='w', padx = 20, pady=10)
        self.r4.grid(row=3, column=2, sticky='w', padx = 20, pady=10)
        self.resultLabel.grid(row=2, column=3, sticky='w', padx = 20, pady=10)                

    def Stack(self):           
        if(self.basePath != ""):
            lightsList = getFiles(path.join(self.basePath, self.lightDir), ".png")
        
            if(len(lightsList)>0):      
                i = 0
                for x in lightsList:
                    lightFrame = np.asarray(imread(x,IMREAD_ANYDEPTH))
                    if(i == 0):
                        height, width = lightFrame.shape[:2]
                        darkFrame = getCalibrationFrame(height, width, path.join(self.basePath, self.darkDir), 0)
                        biasFrame = getCalibrationFrame(height, width, path.join(self.basePath, self.biasDir), 0)
                        flatFrame = getCalibrationFrame(height, width, path.join(self.basePath, self.flatDir), 1)
                        biasSubtractedFlatFrame = flatFrame-biasFrame               
                        stackFrame = np.full((height, width), 0, dtype=np.float32)
                
                    lightFrame = lightFrame.astype(np.float32)/(255**lightFrame.dtype.itemsize)
                    lightFrame -= darkFrame
                    addWeighted(stackFrame, 1, lightFrame, 1 / len(lightsList), 0.0, stackFrame)
                
                if(self.flipStack.get() == 1):
                    biasSubtractedFlatFrame = flip(biasSubtractedFlatFrame,1)
                    stackFrame = flip(stackFrame,1)

                imwrite(path.join(self.basePath, self.outDir, "biasSubtractedFlatFrame.tif"), biasSubtractedFlatFrame)
                imwrite(path.join(self.basePath, self.outDir, "stackFrame.tif"), stackFrame)
        
                self.resultLabel.config(text="Stacked " + str(len(lightsList)) + " frames.", fg="blue")
            else: 
                self.resultLabel.config(text="No lightframes found!", fg="red")    
        else:
             self.resultLabel.config(text="Please enter a valid base path.", fg="red")    
      
    def Calibrate(self):     
        if(self.basePath != ""):           
            if path.exists(path.join(self.basePath, self.outDir, "stackFrame.tif") and path.join(self.basePath, self.wcalDir, "wcal.csv")):
                stackFrame = imread(path.join(self.basePath, self.outDir, "stackFrame.tif"), IMREAD_ANYDEPTH)                
                wcalData = np.loadtxt(path.join(self.basePath, self.wcalDir, "wcal.csv"), dtype=float, delimiter=';')
  
                lines = wcalData[:,1]
                wavelengths = wcalData[:,0]
           
                spectrum = np.mean(stackFrame[self.spectraPos:self.spectraPos+self.spectraWidth, 1:], axis = 0) 
                                
                plt.figure(figsize=(15, 1))
                plt.axis("off")
                plt.imshow(stackFrame[self.spectraPos:self.spectraPos+self.spectraWidth, 1:], cmap='gray')
                plt.show()
                
                spectrumPixels = np.arange(1, len(spectrum) + 1)                                 
                
                if((len(lines)>1 and self.wcalSelector.get() == 1) or (len(lines)>2 and self.wcalSelector.get() == 2) or 
                   (len(lines)>3 and self.wcalSelector.get() == 3) or (len(lines)>4 and self.wcalSelector.get() == 4)):              
                    if(self.wcalSelector.get() == 1):
                        params, covariance = curve_fit(linearFunction, lines, wavelengths)
                        w_fit = linearFunction(spectrumPixels, params[0], params[1])
                    elif(self.wcalSelector.get() == 2):
                        params, covariance = curve_fit(quadraticFunction, lines, wavelengths)
                        w_fit = quadraticFunction(spectrumPixels, params[0], params[1], params[2])                  
                    elif(self.wcalSelector.get() == 3):
                        params, covariance = curve_fit(cubicFunction, lines, wavelengths)
                        w_fit = quadraticFunction(spectrumPixels, params[0], params[1], params[2], params[3])
                    else:
                        params, covariance = curve_fit(quarticFunction, lines, wavelengths)
                        w_fit = quadraticFunction(spectrumPixels, params[0], params[1], params[2], params[3], params[4])
           
                    if(self.showWaveCal.get() == 1):
                        plt.plot(lines, wavelengths, 'o', color='blue', label='Calibration lines data')
                        plt.plot(spectrumPixels, w_fit, color='red', label='Fit')
                        plt.plot(top = 1, bottom = 0, right = 1, left = 0, hspace = 0, wspace = 0)
                        plt.xlabel('Pixels')
                        plt.ylabel('Wavelength ($\AA$)')
                        plt.legend()
                        plt.show()  
    
                    plt.plot(w_fit, spectrum, '-', label='Beta CrB')
        
                    plt.axvline(x = wavelengths[0], color = 'orange', label = 'Ne 6599.0')
                    plt.axvline(x = wavelengths[1], color = 'orange', label = 'Ne 6678.3')
                    plt.axvline(x = wavelengths[2], color = 'orange', label = 'Ne 6717.7')
      
                    plt.axvline(x = 6562.8, color = 'y', label = 'Ha 6562.8')
                    plt.axvline(x = 6645.1, color = 'r', label = 'Eu 6645.1')
                    plt.axvline(x = 6707.8, color = 'k', label = 'Li 6707.8')
                    plt.axvline(x = 6717.7, color = 'r', label = 'Ca 6717.7')
                    plt.plot(top = 1, bottom = 0, right = 1, left = 0, hspace = 0, wspace = 0)
                    plt.xlabel('Wavelength ($\AA$)')
                    plt.ylabel('Intensity')
                    plt.legend()
                    plt.show()
                else:
                    self.resultLabel.config(text="Needs at least " + str(self.wcalSelector.get() + 1) + " calibration lines for this fit.", fg="red")
            else:
                self.resultLabel.config(text="No stacked frame found.", fg="red")              
        else:
            self.resultLabel.config(text="Please enter a valid base path.", fg="red")    
            
    def selectPath(self):
        self.basePath = filedialog.askdirectory()
        self.directoryLabel.config(text=self.basePath, fg="blue")

               
    def display_results(self, results):
        self.resultLabel.config(text="\n".join(results))
        
def getFiles(filepath, ext):   
    filenames = []
    for root, dirs, files in walk(filepath):
        for file in files:
            if file.endswith(ext):
                filenames.append(path.join(root, file))
  
    return filenames

def getLights(inputDir, ext):
    lightsList = getFiles(inputDir, ext)
    return lightsList

def getCalibrationFrame(ySize, xSize, calibrationPath, defaultValue):
    masterFrame = np.full((ySize, xSize), defaultValue, dtype=np.float32)

    if path.exists(path.join(calibrationPath, "masterFrame.tif")):
        tmpFrame = imread(path.join(calibrationPath, "masterFrame.tif"), IMREAD_ANYDEPTH)
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
            imwrite(path.join(calibrationPath, "masterFrame.tif"), masterFrame)

    return masterFrame

def linearFunction(x, a, b):
    return a * x + b

def quadraticFunction(x, a, b, c):
    return a * x * x + b * x + c

def cubicFunction(x, a, b, c, d):
    return a * x * x * x + b * x * x + c * x + d

def quarticFunction(x, a, b, c, d, e):
    return a * x * x * x * x + b * x * x * x + c * x * x + d * x + e

if __name__ == "__main__":
    app = Application()
    app.mainloop()
