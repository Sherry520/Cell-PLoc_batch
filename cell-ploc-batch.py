#!/usr/bin/env python3
import os
import time
import argparse
import requests
from bs4 import BeautifulSoup
import urllib.parse

def parse_fasta(fasta_file):
    """解析输入的 FASTA 文件，返回一个包含 (header, sequence) 的列表"""
    sequences = []
    current_header = None
    current_seq = []
    
    if not os.path.exists(fasta_file):
        raise FileNotFoundError(f"未找到输入文件: {fasta_file}")
        
    with open(fasta_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith('>'):
                if current_header:
                    sequences.append((current_header, ''.join(current_seq)))
                current_header = line[1:].split()[0]
                current_seq = []
            else:
                current_seq.append(line)
        if current_header:
            sequences.append((current_header, ''.join(current_seq)))
            
    return sequences

def batch_predict_subcellular(fasta_input_path, output_result_path):
    base_url = "http://www.csbio.sjtu.edu.cn/bioinf/plant-multi/"
    
    # 1. 解析 FASTA 文件
    try:
        sequences = parse_fasta(fasta_input_path)
        print(f"\n[成功] 读取 FASTA 文件，共包含 {len(sequences)} 条蛋白质序列。")
    except Exception as e:
        print(f"\n[错误] 读取 FASTA 失败: {e}")
        return

    # ⭐ 【核心修改点】检查并自动生成输出目录
    output_dir = os.path.dirname(output_result_path)
    if output_dir and not os.path.exists(output_dir):
        print(f"[提示] 输出目录 '{output_dir}' 不存在，正在自动创建...")
        os.makedirs(output_dir, exist_ok=True)

    # 2. 访问主页获取表单提交的真实路径
    print("正在连接交大 Plant-mPLoc 服务器...")
    session = requests.Session()
    try:
        response = session.get(base_url, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"[错误] 无法连接到服务器，请检查网络或网站是否维护: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    form = soup.find('form')
    if not form:
        print("[错误] 未能从网页中解析出提交表单。")
        return
        
    action = form.get('action', '')
    action_url = urllib.parse.urljoin(base_url, action)
    
    form_data = {}
    for inp in form.find_all('input'):
        name = inp.get('name')
        if name and name != 'S1':
            form_data[name] = inp.get('value', '')

    known_locations = [
        "Cell membrane", "Plasma membrane", "Cell wall", "Chloroplast", "Cytoplasm", 
        "Endoplasmic reticulum", "Extracellular", "Golgi apparatus", 
        "Mitochondrion", "Nucleus", "Peroxisome", "Plastid", "Vacuole"
    ]

    # 3. 开始循环提交预测
    print(f"开始批量预测，结果将实时保存至: {output_result_path}\n" + "-"*50)
    with open(output_result_path, 'w', encoding='utf-8') as out_f:
        out_f.write("Protein_ID\tPredicted_Location\n")
        
        for idx, (header, seq) in enumerate(sequences, 1):
            print(f"[{idx}/{len(sequences)}] 正在查询: {header} ... ", end="", flush=True)
            
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
            
            time.sleep(2)
            
    print("-"*50 + f"\n[完成] 全部预测结束！结果已成功保存至: {output_result_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Plant-mPLoc 批量植物蛋白亚细胞定位预测工具")
    parser.add_argument("-i", "--input", help="输入的 FASTA 文件路径")
    parser.add_argument("-o", "--output", help="输出的结果文件路径（可选）")
    args = parser.parse_args()

    input_fasta_path = args.input
    output_file_path = args.output

    if not input_fasta_path:
        print("="*60)
        print("欢迎使用 Plant-mPLoc 批量预测工具")
        print("提示：在 Windows/Mac 中，您可以直接把 FASTA 文件拖拽到本窗口内自动输入路径")
        print("="*60)
        raw_input = input("请输入或拖入您的 FASTA 文件路径: ")
        input_fasta_path = raw_input.strip().strip('"').strip("'")
    
    if not output_file_path:
        base, ext = os.path.splitext(input_fasta_path)
        output_file_path = f"{base}_subcellular_results.txt"
        print(f"--> 未指定输出文件，结果将默认保存至: {output_file_path}")

    if input_fasta_path:
        batch_predict_subcellular(input_fasta_path, output_file_path)
    else:
        print("[错误] 未提供有效的输入文件路径。")