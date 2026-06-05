# Cell-PLoc_batch
A Python tool for batch predicting plant protein subcellular localization via Plant-mPLoc.

This project provides a Python script designed to automate batch submissions to the [Plant-mPLoc](http://www.csbio.sjtu.edu.cn/bioinf/plant-multi/) server developed by the CSBio Laboratory at Shanghai Jiao Tong University. It overcomes the web interface's limitation of only allowing one query at a time by automatically parsing and exporting results from large FASTA files.

---

## 🚀 Features

- **Batch Processing**: Supports querying hundreds of plant protein sequences at once using a standard FASTA file.
- **Dual Mode**: Offers an **interactive drag-and-drop** interface for beginners and a **Command Line Interface (CLI)** for automation.
- **Smart Parsing**: Accurately extracts results, including multi-site predictions (proteins localized to multiple cellular components).
- **Server-Friendly**: Features a built-in 2-second delay between requests to prevent overloading the academic server and avoid IP bans.

---

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone https://github.com/Sherry520/Cell-PLoc_batch.git
cd Cell-PLoc_batch
```

### 2. Install Dependencies
The script is built on _`Python 3`_. Ensure you have the required external libraries (`requests` and `beautifulsoup4`) installed before running the script:
```bash
pip install requests beautifulsoup4
```

## 💻 Usage
The script supports two flexible modes of operation:

#### Mode 1: Interactive Mode (Easiest / Drag & Drop)
Simply run the script. It will prompt you to enter the path, where you can directly drag and drop your FASTA file into the terminal window:
```bash
python cell-ploc-batch.py
```
Note: If no output path is specified, the script will automatically generate an output file named `[input_filename]_subcellular_results.txt` in the same directory as your input file.

#### Mode 2: Command Line Interface (Best for Automation)
Pass the input (`-i`) and output (`-o`) paths directly as arguments in your terminal:

```Bash
# Provide only the input file (output is auto-generated)
python cell-ploc-batch.py -i sequences.fasta

# Provide both input and explicit output files
python cell-ploc-batch.py -i ./data/sequences.fasta -o ./results/my_results.txt
```

#### 💡 Linux/macOS Execution Shortcut:
To run the script directly as an executable without typing python, grant it execution permissions:

```Bash
chmod +x cell-ploc-batch.py
./cell-ploc-batch.py -i sequences.fasta
```
_Troubleshooting: If you encounter a `\r: No such file or directory` error on Linux, it means the file contains Windows line endings. Fix it by running:_ `sed -i 's/\r$//' cell-ploc-batch.py`.

## 📦 Building a Standalone Binary
You can bundle this script into a standalone executable that runs on machines without a Python environment using `PyInstaller`.

**⚠️ Important**: PyInstaller is not a cross-compiler. The executable will target the operating system on which it was built (building on Windows creates a `.exe`, while building on Linux creates a extensionless binary).

#### 1. Install PyInstaller
```Bash
pip install pyinstaller
```

#### 2. Build the Executable
```Bash
pyinstaller -F cell-ploc-batch.py
```

#### 3. Locate the Binary
Once completed, find your standalone application inside the newly created `dist/` directory:

- Windows: `dist/cell-ploc-batch.exe`

- Linux/macOS: `dist/cell-ploc-batch`

## 📄 Output Example
The output is exported as a standard tab-separated values (`.txt` / `.tsv`) file. It can be opened directly with Excel or any text editor:

```Plaintext
Protein_ID  Predicted_Location
Zm00001eb010460 Cell membrane
Zm00001eb018230 Cell membrane
Zm00001eb018250 Cell membrane
```

## 🤝 Citations & Disclaimer
1. This tool serves strictly as an automation wrapper for submitting web forms. The core predictive algorithm and hosting services belong entirely to the CSBio Laboratory at Shanghai Jiao Tong University.

2. If you use results obtained via this tool in an academic publication, please make sure to cite the official Plant-mPLoc paper:

    *Kuo-Chen Chou and Hong-Bin Shen, "Plant-mPLoc: a top-down strategy to augment the power for predicting plant protein subcellular localization", PLoS ONE, 2010, 5: e11335.*

3. Please use this tool responsibly. Do not remove the time delays or abuse the academic server with excessive concurrent requests.
