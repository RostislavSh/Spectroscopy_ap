# Spectroscopy_ap
Calculation of the luminescence quantum yield using the relative method from spectroscopic data
# 🔬 Project Overview
This application streamlines the process of calculating quantum yield by matching standard and sample data. It handles raw spectroscopic files, performs data cleaning (cropping), and executes precise mathematical integration.
# 🚀 Key Features
* Multilingual Interface: Full support for both English and Russian languages.
* Batch Processing: Load entire folders of data simultaneously.
* Automatic Spectrum Matching: Automatically pairs emission and absorption spectra for each sample based on filenames.
* Data Preprocessing: Built-in functionality to crop data ranges as needed.
* Advanced Numerical Integration: Choose between Trapezoidal rule and Simpson's rule (optimized for non-uniform grids).
# 🛠 Tech Stack & Dependencies
* Python 3.x
* PyQt5 — Graphical User Interface.
* NumPy — High-performance array processing.
* Matplotlib — Data visualization and plotting.
* SciPy.
* Built-in modules: os, sys, math.
# 📋 How to Use
Prepare your data:
* Place absorption spectra (.txt) and emission spectra (.tit) in their respective folders.
* Note: Absorption and emission files for the same sample must have identical names.
Run the application:
*Select the folders for the Standard and the Sample.
*(Optional) Set the desired cropping range for the spectra.
# Calculate:
* Click the Calculate button.
* Copy the resulting Quantum Yield value from the output field.
# ⚙️ Installation
1. Clone the repository:
  bash
  git clone https://github.com/RostislavSh/Spectroscopy_ap/
2. Install required libraries:
  bash
  pip install -r requirements.txt
3. Run the script:
  bash
  python spectroscopy_app.py

Developed by Rostislav Shulepov
