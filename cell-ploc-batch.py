#!/usr/bin/env python3
import os
import time
import argparse
import requests
from bs4 import BeautifulSoup
import urllib.parse

def parse_fasta(fasta_file):
    """Parses the input FASTA file and returns a list of tuples: (header, sequence)"""
    sequences = []
    current_header = None
    current_seq = []
    
    if not os.path.exists(fasta_file):
        raise FileNotFoundError(f"Input file not found: {fasta_file}")
        
    with open(fasta_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith('>'):
                if current_header:
                    sequences.append((current_header, ''.join(current_seq)))
                # Extract the first word after '>' as the Protein ID
                current_header = line[1:].split()[0]
                current_seq = []
            else:
                current_seq.append(line)
        if current_header:
            sequences.append((current_header, ''.join(current_seq)))
            
    return sequences

def batch_predict_subcellular(fasta_input_path, output_result_path):
    base_url = "http://www.csbio.sjtu.edu.cn/bioinf/plant-multi/"
    
    # 1. Parse the FASTA file
    try:
        sequences = parse_fasta(fasta_input_path)
        print(f"\n[SUCCESS] Read FASTA file, containing {len(sequences)} protein sequences.")
    except Exception as e:
        print(f"\n[ERROR] Failed to read FASTA file: {e}")
        return

    # 2. Check and automatically create the output directory if it doesn't exist
    output_dir = os.path.dirname(output_result_path)
    if output_dir and not os.path.exists(output_dir):
        print(f"[INFO] Output directory '{output_dir}' does not exist. Creating it automatically...")
        os.makedirs(output_dir, exist_ok=True)

    # 3. Connect to the homepage to extract the valid form action URL
    print("Connecting to SJTU Plant-mPLoc server...")
    session = requests.Session()
    try:
        response = session.get(base_url, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"[ERROR] Failed to connect to the server. Please check your network or if the website is down: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    form = soup.find('form')
    if not form:
        print("[ERROR] Failed to parse the submission form from the webpage.")
        return
        
    action = form.get('action', '')
    action_url = urllib.parse.urljoin(base_url, action)
    
    # Extract any hidden input fields if present
    form_data = {}
    for inp in form.find_all('input'):
        name = inp.get('name')
        if name and name != 'S1':  # 'S1' is the textarea field name for sequences
            form_data[name] = inp.get('value', '')

    # Known target locations for accurate mapping
    known_locations = [
        "Cell membrane", "Plasma membrane", "Cell wall", "Chloroplast", "Cytoplasm", 
        "Endoplasmic reticulum", "Extracellular", "Golgi apparatus", 
        "Mitochondrion", "Nucleus", "Peroxisome", "Plastid", "Vacuole"
    ]

    # 4. Start iterative form submission
    print(f"Starting batch prediction, results will be saved in real-time to: {output_result_path}\n" + "-"*60)
    with open(output_result_path, 'w', encoding='utf-8') as out_f:
        # Write header row
        out_f.write("Protein_ID\tPredicted_Location\n")
        
        for idx, (header, seq) in enumerate(sequences, 1):
            print(f"[{idx}/{len(sequences)}] Querying: {header} ... ", end="", flush=True)
            
            fasta_payload = f">{header}\n{seq}"
            current_payload = form_data.copy()
            current_payload['S1'] = fasta_payload
            
            location_result = "Unknown"
            try:
                post_res = session.post(action_url, data=current_payload, timeout=30)
                post_res.raise_for_status()
                
                res_soup = BeautifulSoup(post_res.text, 'html.parser')
                page_text = res_soup.get_text()
                
                if "Predicted location" in page_text:
                    after_keyword = page_text.split("Predicted location")[-1]
                    found_locs = [loc for loc in known_locations if loc.lower() in after_keyword.lower()]
                    if found_locs:
                        location_result = ", ".join(found_locs)
                else:
                    cells = [td.get_text(strip=True) for td in res_soup.find_all('td')]
                    for i, cell in enumerate(cells):
                        if "Predicted location" in cell and i + 1 < len(cells):
                            next_cell = cells[i+1]
                            found_locs = [loc for loc in known_locations if loc.lower() in next_cell.lower()]
                            if found_locs:
                                location_result = ", ".join(found_locs)
                                break
            except Exception as e:
                location_result = f"Error ({str(e)})"
            
            print(location_result)
            out_f.write(f"{header}\t{location_result}\n")
            out_f.flush()
            
            # 2-second delay to comply with standard academic crawler guidelines
            time.sleep(2)
            
    print("-"*60 + f"\n[FINISHED] All predictions completed! Results successfully saved to: {output_result_path}")

if __name__ == "__main__":
    # Setup command line argument parsing
    parser = argparse.ArgumentParser(description="Plant-mPLoc Batch Predictor for Plant Protein Subcellular Localization")
    parser.add_argument("-i", "--input", help="Path to the input FASTA file")
    parser.add_argument("-o", "--output", help="Path to the output results file (optional)")
    args = parser.parse_args()

    input_fasta_path = args.input
    output_file_path = args.output

    # Whether is in the double-click interaction mode
    is_interactive = False

    # Interactive prompt if CLI arguments are missing
    if not input_fasta_path:
        is_interactive = True # 没有传参，说明是双击运行的
        print("="*60)
        print("Welcome to Plant-mPLoc Batch Predictor")
        print("Tip: On Windows/Mac, you can directly drag and drop your FASTA file into this window.")
        print("="*60)
        raw_input = input("Please enter or drag & drop your FASTA file path: ")
        input_fasta_path = raw_input.strip().strip('"').strip("'")
    
    # Generate default output name if not explicitly provided
    if not output_file_path and input_fasta_path:
        base, ext = os.path.splitext(input_fasta_path)
        output_file_path = f"{base}_subcellular_results.txt"
        print(f"--> No output file specified. Results will be saved by default to: {output_file_path}")

    # Fire the calculation
    if input_fasta_path:
        batch_predict_subcellular(input_fasta_path, output_file_path)
    else:
        print("[ERROR] No valid input file path provided.")

    # If run by double-clicking, force a pause at the end and wait for the user to press Enter before closing.
    if is_interactive:
        print("\n" + "="*60)
        input("Execution finished. Press Enter to exit...")
