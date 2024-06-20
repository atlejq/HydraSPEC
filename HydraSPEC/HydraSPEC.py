import string
from cv2 import NONE_POLISHER, imshow, imread, imwrite, IMREAD_GRAYSCALE, IMREAD_ANYDEPTH, addWeighted, flip, warpAffine, INTER_CUBIC
from matplotlib import pyplot as plt
from scipy.optimize import curve_fit
import numpy as np
from os import walk, path
from tkinter import filedialog, Label, Button, Radiobutton, Checkbutton, Spinbox, IntVar, DoubleVar, Tk, Entry, ttk, messagebox, simpledialog
import csv

fig = None
ax = None
image = None
hline = None
hline2 = None

neonWavelengths = [5852.4878, 5881.895, 5944.8342, 5975.534, 6029.9971, 6074.3377, 6096.1631, 6143.0626, 6163.5939, 
                   6217.2812, 6266.495, 6304.789, 6334.4278, 6382.9917, 6402.246, 6506.5281, 6532.8822, 6598.9529, 
                   6678.2764, 6717.043, 6929.4673, 7032.4131, 7245.1666, 7438.899]

class Application(Tk):
    def __init__(self):
        super().__init__()

        tabs = ttk.Notebook(self)  
        t1 = ttk.Frame(tabs)
        t2 = ttk.Frame(tabs)
        t3 = ttk.Frame(tabs)
        tabs.add(t1, text = 'Stacking')
        tabs.add(t2, text = 'Geometric corrections')
        tabs.add(t3, text = 'Wavelength calibration')
        tabs.pack(expand = 1, fill = "both")

        self.title("HydraSPEC")
        self.geometry("500x250")
        self.iconbitmap('python.ico') 
        self.wm_attributes("-topmost", 1)
        self.resizable(False,False)

        self.basePath = ""    
        self.outDir ="out"
        self.lightDir = "lights"
        self.darkDir = "darks"
        self.flatDir = "flats"
        self.biasDir = "bias"
        self.wcalDir = "wcal"
        
        self.th = 0      
        self.ROI_y = 1
        self.ROI_dy = 1
        
        self.directoryLabel = Label(t1, text="")
        self.tiltLabel = Label(t2, text="Tilt")
        self.entryLabel = Label(t2, text="Spectra top")
        self.entryLabel2 = Label(t2, text="Spectra width")
        
        self.pathButton = Button(t1, text="Select path", command=self.selectPath)        
        self.stackButton = Button(t1, text="Stack", command=self.Stack)   
        self.processButton = Button(t2, text="Process", command=self.processGeometry)
        self.calButton = Button(t3, text="Calibrate", command=self.Calibrate)             
        
        self.entry = Spinbox(t2, from_=1, to=10000, increment=1, textvariable=IntVar(value="1"), command=self.processGeometry)  
        self.entry2 = Spinbox(t2, from_=1, to=10000, increment=1, textvariable=IntVar(value="1"), command=self.processGeometry)      
        self.tilt = Spinbox(t2, from_=-2, to=2, increment=0.01, textvariable=DoubleVar(value="0") , format="%.2f", command=self.processGeometry)         
        
        self.showWaveCal = IntVar(value="0")
        self.polySelector = IntVar(value="2")
        self.calSourceSelector = IntVar(value="1")

        self.c1 = Checkbutton(t3, variable=self.showWaveCal, onvalue=1, offvalue=0, text="Show calibration")    
        self.r1 = Radiobutton(t3, variable=self.polySelector, value=1, text='Linear')
        self.r2 = Radiobutton(t3, variable=self.polySelector, value=2, text='Quadratic')
        self.r3 = Radiobutton(t3, variable=self.polySelector, value=3, text='Cubic')
        self.r4 = Radiobutton(t3, variable=self.polySelector, value=4, text='Quartic')   
        self.r5 = Radiobutton(t3, variable=self.calSourceSelector, value=1, text='Input file')
        self.r6 = Radiobutton(t3, variable=self.calSourceSelector, value=2, text='Ne lamp')
        
        self.directoryLabel.grid(column=1, row=0, sticky='w', padx = 20, pady=10)  
        self.tiltLabel.grid(column=2, row=0, sticky='w', padx = 20, pady=10)  
        self.entryLabel.grid(column=2, row=1, sticky='w', padx = 20, pady=10)  
        self.entryLabel2.grid(column=2, row=2, sticky='w', padx = 20, pady=10)  
        
        self.pathButton.grid(column=0, row=0, sticky='w', padx = 20, pady=10)
        self.stackButton.grid(column=0, row=1, sticky='w', padx = 20, pady=10)
        self.processButton.grid(column=0, row=0, sticky='w', padx = 20, pady=10)
        self.calButton.grid(column=0, row=0, sticky='w', padx = 20, pady=10)
       
        self.tilt.grid(column=3, row=0, sticky='w', padx = 20, pady=10)  
        self.entry.grid(column=3, row=1, sticky='w', padx = 20, pady=10)
        self.entry2.grid(column=3, row=2, sticky='w', padx = 20, pady=10)
      
        self.c1.grid(column=0, row=1, sticky='w', padx = 20, pady=10)               
        self.r1.grid(column=2, row=0, sticky='w', padx = 20, pady=10)
        self.r2.grid(column=2, row=1, sticky='w', padx = 20, pady=10)
        self.r3.grid(column=2, row=2, sticky='w', padx = 20, pady=10)
        self.r4.grid(column=2, row=3, sticky='w', padx = 20, pady=10)
        self.r5.grid(column=1, row=0, sticky='w', padx = 20, pady=10)
        self.r6.grid(column=1, row=1, sticky='w', padx = 20, pady=10)

    def Stack(self):           
        if(self.basePath != ""):
            lightsList = getFiles(path.join(self.basePath, self.lightDir), ".png")       
            if(len(lightsList)>0):      
                i = 0
                hotPixels = []

                for l in lightsList:
                    lightFrame = np.asarray(imread(l,IMREAD_ANYDEPTH))
                    if(i == 0):
                        height, width = lightFrame.shape[:2]
                        masterDarkFrame = getCalibrationFrame(height, width, path.join(self.basePath, self.darkDir), 0)
                        masterBiasFrame = getCalibrationFrame(height, width, path.join(self.basePath, self.biasDir), 0)
                        masterFlatFrame = getCalibrationFrame(height, width, path.join(self.basePath, self.flatDir), 1)
                        masterBiasSubtractedFlatFrame = masterFlatFrame-masterBiasFrame               
                        stackFrame = np.full((height, width), 0, dtype=np.float32)

                        meanDarkValue = np.average(masterDarkFrame)
                       
                        hotPixelPositions = np.where(masterDarkFrame > 10 * meanDarkValue)
                        hotPixels = np.column_stack((hotPixelPositions[1], hotPixelPositions[0]))

                    i = i+1
                    lightFrame = lightFrame.astype(np.float32)/(255**lightFrame.dtype.itemsize)
                    lightFrame -= masterDarkFrame
                                    
                    addWeighted(stackFrame, 1, lightFrame, 1 / len(lightsList), 0.0, stackFrame)
                
                    #stackFrame = hotPixelCorrect(stackFrame, hotPixels)

                imwrite(path.join(self.basePath, self.outDir, "masterBiasSubtractedFlatFrame.tif"), masterBiasSubtractedFlatFrame)
                imwrite(path.join(self.basePath, self.outDir, "stackFrame.tif"), stackFrame)
        
                messagebox.showinfo("Success!", f"Stacked {len(lightsList)} frames.")
            else: 
                messagebox.showerror("Invalid Input", "No lightframes found!")
        else:
            messagebox.showerror("Invalid Input", "Please enter a valid base path.")
      
    def Geometry(self):   
        if(self.basePath != ""):           
            if path.exists(path.join(self.basePath, self.wcalDir, "wcal.png")):
                wcalFrame = imread(path.join(self.basePath, self.wcalDir, "wcal.png"), IMREAD_ANYDEPTH) 
              
                self.th = float(self.tilt.get())*3.14159/180
                M = np.float32([[np.cos(self.th), -np.sin(self.th), 0], [np.sin(self.th), np.cos(self.th), 0]])
                wcalFrame = warpAffine(wcalFrame, M, (wcalFrame.shape[1], wcalFrame.shape[0]), flags = INTER_CUBIC)
                            
                global fig, ax, image, hline, hline2
                
                if(self.ROI_y > wcalFrame.shape[1]-1):                
                    self.ROI_y = wcalFrame.shape[1]-2
                    
                if(self.ROI_y + self.ROI_dy > wcalFrame.shape[1]):                
                    self.ROI_dy = 1
  
                if fig is None or ax is None or image is None or not plt.fignum_exists(fig.number):
                    fig, ax = plt.subplots()
                    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)

                    ax.axis("off")
                    image = ax.imshow(5*wcalFrame, cmap='gray', aspect='auto')

                    hline = ax.axhline(y=self.ROI_y, color='red', linewidth=1)
                    hline2 = ax.axhline(y=self.ROI_y + self.ROI_dy, color='red', linewidth=1)

                    plt.ion()  
                    plt.show()
                else:
                    image.set_data(5*wcalFrame)
                    hline.set_ydata([self.ROI_y, self.ROI_y])
                    hline2.set_ydata([self.ROI_y + self.ROI_dy, self.ROI_y + self.ROI_dy])
                    
                    ax.relim()  
                    ax.autoscale_view()  
                    plt.draw()  
                    plt.pause(0.01)  
               
            else:
                messagebox.showerror("Invalid Input", "No stack frame found!")
        else:
            messagebox.showerror("Invalid Input", "Please enter a valid base path.")
        
    def Calibrate(self):     
        if(self.basePath != ""):           
            if path.exists(path.join(self.basePath, self.outDir, "stackFrame.tif")):
                stackFrame = imread(path.join(self.basePath, self.outDir, "stackFrame.tif"), IMREAD_ANYDEPTH)                               
                if(self.calSourceSelector.get() == 1 and path.join(self.basePath, self.wcalDir, "wcal.csv")):
                    wcalData = np.loadtxt(path.join(self.basePath, self.wcalDir, "wcal.csv"), dtype=float, delimiter=';')
                    polyFit(self, stackFrame, wcalData[:,0], wcalData[:,1])
                elif(self.calSourceSelector.get() == 2):
                    popup = FloatInputPopup(self, title="Enter Floats")                  
                    if hasattr(popup, 'results'):
                        resultArr = np.array(popup.results)                   
                        polyFit(self, stackFrame, resultArr[:,0], resultArr[:,1])
                else:
                    messagebox.showerror("Invalid Input", "No calibration file found!")                                                          
            else:
                messagebox.showerror("Invalid Input", "No stack frame found!")    
        else:
            messagebox.showerror("Invalid Input", "Please enter a valid base path.")
             
    def selectPath(self):
        self.basePath = filedialog.askdirectory()
        self.directoryLabel.config(text=self.basePath, fg="blue")

    def processGeometry(self):
        """Handle the submit button click event."""
        try:
            self.ROI_y = int(self.entry.get())
            self.ROI_dy = int(self.entry2.get())
            self.Geometry()
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter two valid numbers.")
            
def polyFit(self, stackFrame, wavelengths, lines):
        M = np.float32([[np.cos(self.th), -np.sin(self.th), 0], [np.sin(self.th), np.cos(self.th), 0]])
        stackFrame = warpAffine(stackFrame, M, (stackFrame.shape[1], stackFrame.shape[0]), flags = INTER_CUBIC)
        spectrum = np.mean(stackFrame[self.ROI_y:self.ROI_y+self.ROI_dy, 1:], axis = 0) 
                
        spectrumPixels = np.arange(1, len(spectrum) + 1)                                 
                
        if((len(lines)>1 and self.polySelector.get() == 1) or (len(lines)>2 and self.polySelector.get() == 2) or (len(lines)>3 and self.polySelector.get() == 3) or (len(lines)>4 and self.polySelector.get() == 4)):              
            if(self.polySelector.get() == 1):
                params, covariance = curve_fit(linearFunction, lines, wavelengths)
                w_fit = linearFunction(spectrumPixels, params[0], params[1])
            elif(self.polySelector.get() == 2):
                params, covariance = curve_fit(quadraticFunction, lines, wavelengths)
                w_fit = quadraticFunction(spectrumPixels, params[0], params[1], params[2])                  
            elif(self.polySelector.get() == 3):
                params, covariance = curve_fit(cubicFunction, lines, wavelengths)
                w_fit = quadraticFunction(spectrumPixels, params[0], params[1], params[2], params[3])
            else:
                params, covariance = curve_fit(quarticFunction, lines, wavelengths)
                w_fit = quadraticFunction(spectrumPixels, params[0], params[1], params[2], params[3], params[4])
           
            if(self.showWaveCal == 1):                     
                fig3, ax3 = plt.subplots()
                ax3.plot(lines, wavelengths, 'o', color='blue', label='Calibration lines data')
                ax3.plot(spectrumPixels, w_fit, color='red', label='Fit')
                ax3.set(xlabel='Pixels', ylabel = 'Wavelength ($\AA$)')
                ax3.legend()
                plt.show()  
    
            fig2, ax2 = plt.subplots()
                    
            if(path.join(self.basePath, self.wcalDir, "elements.csv")):
                elementNames = []
                elementColors = []
                elementLines = []
                description = ""

                with open(path.join(self.basePath, self.wcalDir, "elements.csv"), mode='r') as file:
                    csv_reader = csv.reader(file)
                    description = next(csv_reader)[0]
                    next(csv_reader)
    
                    for row in csv_reader:
                        elementNames.append(row[0])
                        elementColors.append(row[1])
                        elementLines.append(float(row[2]))

                ax2.plot(w_fit, spectrum, '.-', label="Data")
                
                i = 0;
                for e in elementNames:
                    ax2.axvline(x = elementLines[i], color=elementColors[i], label = elementNames[i] + ' ' + str(elementLines[i]))
                    i = i + 1
                    
                plt.title(description)
                
            if(self.showWaveCal.get() == 1):   
                for w in wavelengths:
                    ax2.axvline(x = w, linestyle = ":", color = 'orange', label = 'Ne ' + str(w))
               
            ax2.set(xlabel='Wavelength ($\AA$)', ylabel = 'Intensity')

            ax2.legend()
            plt.show()   
        else:
            messagebox.showerror("Invalid Input", f"Needs at least {self.polySelector.get() + 1} calibration lines for this fit.")
                 
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

def hotPixelCorrect(frame, hotPixels):
    for i in range(len(hotPixels)):
        x = hotPixels[i][0]
        y = hotPixels[i][1]
        if x > 0 or y > 0 or x < frame.shape[1] - 1 or y < frame.shape[0] - 1:
            frame[y, x] = frame[y - 1, x]/2 + frame[y + 1, x]/2
        
    return frame

class FloatInputPopup(simpledialog.Dialog):
    def body(self, master):
        self.entries = []
              
        Label(master, text=f"Wavelength").grid(row=0, column=0)
        Label(master, text=f"Position").grid(row=0, column=1)
        
        for i in range(len(neonWavelengths)):           
            rowEntries = []
            
            entry = Entry(master, textvariable=DoubleVar(value=neonWavelengths[i]), state='readonly')
            entry.grid(row=i+1, column=0)
            rowEntries.append(entry)
                        
            entry = Entry(master)
            entry.grid(row=i+1, column=1)
            rowEntries.append(entry)
            
            self.entries.append(rowEntries)
                    
        return self.entries[0][0]   

    def apply(self):
        self.results = []
        for row in self.entries:
            row_result = []
            valid_row = True
            for entry in row:
                try:
                    value = float(entry.get())
                    row_result.append(value)
                except ValueError:
                    valid_row = False
                    break
            if valid_row:
                self.results.append(row_result)

if __name__ == "__main__":
    app = Application()
    app.mainloop()
