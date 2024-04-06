from cv2 import imshow, imread, imwrite, IMREAD_GRAYSCALE, IMREAD_ANYDEPTH, addWeighted
from matplotlib import pyplot as plt
from pathlib import Path
from tkinter import messagebox
from webbrowser import get
import json
import numpy as np
import os
import tkinter as tk
from scipy.optimize import curve_fit


def get_frames(path, ext):
    filenames = []
    if os.path.exists(path):
        for p in Path(path).rglob(f'*{ext}'):
            filenames.append(str(p))
    return filenames


def get_calibration_frame(y_size, x_size, calibration_path, default_value):
    master_frame = np.full((y_size, x_size), default_value, dtype=np.float32)

    if os.path.exists(os.path.join(calibration_path, "masterFrame.tif")):
        tmp_calibration_frame = imread(os.path.join(calibration_path, "masterFrame.tif"), IMREAD_ANYDEPTH)
        if tmp_calibration_frame.shape[1] == master_frame.shape[1] and tmp_calibration_frame.shape[0] == master_frame.shape[0]:
            master_frame = tmp_calibration_frame
    else:
        calibration_frame_array = get_frames(calibration_path, ".png")
        if calibration_frame_array:
            for calibration_frame_path in calibration_frame_array:
                calibration_frame = imread(calibration_frame_path, IMREAD_ANYDEPTH)
                if calibration_frame.shape[1] == master_frame.shape[1] and calibration_frame.shape[0] == master_frame.shape[0]:
                    calibration_frame = calibration_frame.astype(np.float32) / 255.0
                    addWeighted(master_frame, 1, calibration_frame, 1 / len(calibration_frame_array), 0.0, master_frame)
            imwrite(os.path.join(calibration_path, "masterFrame.tif"), master_frame)

    return master_frame


def linear_function(x, m, c):
    return m * x + c


def quadratic_function(x, n, m, c):
    return n * x * x + m * x + c


def cubic_function(x, o, n, m, c):
    return o * x * x * x + n * x * x + m * x + c


def main():
    # Create the main window
    # root = tk.Tk()
    # root.title("Tkinter Button Returning List")

    # Create a label widget
    # label = tk.Label(root, text="Click the button to get a list.")
    # label.pack(pady=10)
    
    wavelengths = [6383, 6402, 6507, 6533, 6599, 6678, 6717]
    
    calvector = np.asarray(imread("C:\\Users\\47975\\Desktop\\spec\\test\\wcal.png",IMREAD_ANYDEPTH))

    #biasFrame = get_calibration_frame(1411, 2072, "C:\\Users\\47975\\Desktop\\spec\\test\\bias\\", 0)
    darkFrame = get_calibration_frame(1411, 2072, "C:\\Users\\47975\\Desktop\\spec\\test\\darks\\", 0)

    lightsList = get_frames("C:\\Users\\47975\\Desktop\\spec\\test\\lights\\", "png")
    
    stackFrame = np.full((1411, 2072), 0, dtype=np.float32)

    for x in lightsList:
        lightFrame = np.asarray(imread(x,IMREAD_ANYDEPTH))
        lightFrame = lightFrame.astype(np.float32)/(255**lightFrame.dtype.itemsize)
        lightFrame -= darkFrame
        addWeighted(stackFrame, 1, lightFrame, 1 / len(lightsList), 0.0, stackFrame)

    imwrite(os.path.join("C:\\Users\\47975\\Desktop\\spec\\test\\", "stackFrame.tif"), stackFrame)
    
    xpoints = np.mean(stackFrame[700:750, 1:], axis = 0)
    calpoints = np.mean(calvector[700:750, 1:], axis = 0)
        
    edges = np.where(abs(np.diff(np.where(calpoints == 255, calpoints, 0))) == 255)[0]
    
    # Loop through the array, adding consecutive elements
    lines = []

    # Loop through the array, adding consecutive elements
    for i in range(len(edges) - 1):
        if(i%2==0):
            lines.append((edges[i] + 1 + edges[i + 1])/2)

    print(wavelengths)
    print(lines)
    
    #params, covariance = curve_fit(linear_function, lines, wavelengths)
    
    params, covariance = curve_fit(quadratic_function, lines, wavelengths)

    # Extract the parameters
    n, m, c = params
           
    x_fit = np.arange(1, len(xpoints) + 1)
    #y_fit = linear_function(x_fit, m, c)
    y_fit = quadratic_function(x_fit, n, m, c)
    plt.plot(lines, wavelengths, 'o', color='blue', label='Neon lines data')
    plt.plot(x_fit, y_fit, color='red', label='Fit')
    plt.plot(top = 1, bottom = 0, right = 1, left = 0, hspace = 0, wspace = 0)
    plt.xlabel('Pixels')
    plt.ylabel('Wavelength ($\AA$)')
    plt.legend()
    plt.show()  
    
    plt.plot(linear_function(x_fit, m, c), xpoints, '-', label='Beta CrB')
    plt.plot(top = 1, bottom = 0, right = 1, left = 0, hspace = 0, wspace = 0)
    plt.xlabel('Wavelength ($\AA$)')
    plt.ylabel('Intensity')
    plt.legend()
    plt.show()

    # Function to get the list
    #def get_and_process_list():
    #    my_list = get_frames("C:\\Users\\47975\\Desktop\\spec\\test\\lights\\", "png")
    #    myList = process_list(my_list)

    # Create a button widget
    #button = tk.Button(root, text="Get List", command=get_and_process_list)
    #button.pack(pady=5)

    # Run the Tkinter event loop
    #root.mainloop()
    
#def process_list(my_list):
#    return my_list

if __name__ == "__main__":
    main()
