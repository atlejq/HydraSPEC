# HydraSPEC
Python astronomical spectra stacking software with a Tkinter GUI. The software is still very preliminary and lacks intensity calibration.

HydraSPEC is written with Python 3.11. It is intended to be a lightweight spectroscopy software package for stacking and calibrating spectroscopic data. The program takes 8 and 16 bit images as input in ```*.png``` format. 

If HydraSPEC does not detect a given type of calibration files, it will proceed by setting the master dark and bias frames to zero and the master flatframe to unity.

The program can be run from the command line with ```python HydraSTAQ.py```

To compile an ```*.exe``` file, use ```pyinstaller --onefile --noconsole HydraSTAQ.py```

Put your lights and calibration frames in the following structure and select the basepath from the GUI.
```
./
├── lights
├── darks
├── bias
└── flats
```

Trivia: The "Hydra" name is from the constellation Hydra which is the biggest snake in the night sky, instead of yet another software package referring to python snakes.
