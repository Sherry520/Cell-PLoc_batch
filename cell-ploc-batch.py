import os
import time
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
                # 只取 > 后面的第一个单词作为蛋白质 ID
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
        print(f"成功读取 FASTA 文件，共包含 {len(sequences)} 条蛋白质序列。")
    except Exception as e:
        print(f"读取 FASTA 失败: {e}")
        return

    # 2. 访问主页获取表单提交的真实路径（CGI 脚本路径）
    print("正在连接交大 Plant-mPLoc 服务器...")
    session = requests.Session()
    try:
        response = session.get(base_url, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"无法连接到服务器，请检查网络或网站是否维护: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    form = soup.find('form')
    if not form:
        print("错误：未能从网页中解析出提交表单。")
        return
        
    action = form.get('action', '')
    action_url = urllib.parse.urljoin(base_url, action)
    
    # 提取网页表单中可能存在的隐藏参数
    form_data = {}
    for inp in form.find_all('input'):
        name = inp.get('name')
        if name and name != 'S1':  # 'S1' 是输入序列的 textarea 框名
            form_data[name] = inp.get('value', '')

    # 3. 唯一定义该网站支持的 12 种植物亚细胞定位关键词，用于精确匹配
    known_locations = [
        "Cell membrane", "Plasma membrane", "Cell wall", "Chloroplast", "Cytoplasm", 
        "Endoplasmic reticulum", "Extracellular", "Golgi apparatus", 
        "Mitochondrion", "Nucleus", "Peroxisome", "Plastid", "Vacuole"
    ]

    # 4. 开始循环提交预测
    print("开始批量预测定位，结果将实时保存...")
    with open(output_result_path, 'w', encoding='utf-8') as out_f:
        # 写入表头
        out_f.write("Protein_ID\tPredicted_Location\n")
        
        for idx, (header, seq) in enumerate(sequences, 1):
            print(f"[{idx}/{len(sequences)}] 正在查询: {header} ... ", end="", flush=True)
            
            # 包装成单条 FASTA 格式
            fasta_payload = f">{header}\n{seq}"
            current_payload = form_data.copy()
            current_payload['S1'] = fasta_payload
            
            location_result = "Unknown"
            try:
                # 提交 POST 请求
                post_res = session.post(action_url, data=current_payload, timeout=30)
                post_res.raise_for_status()
                
                # 解析返回的结果网页文本
                res_soup = BeautifulSoup(post_res.text, 'html.parser')
                page_text = res_soup.get_text()
                
                # 提取定位结果：重点寻找 "Predicted location" 之后的文本
                if "Predicted location" in page_text:
                    after_keyword = page_text.split("Predicted location")[-1]
                    found_locs = [loc for loc in known_locations if loc.lower() in after_keyword.lower()]
                    if found_locs:
                        location_result = ", ".join(found_locs)
                else:
                    # 备用表格解析：遍历所有 td 单元格
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
            # 实时写入文件
            out_f.write(f"{header}\t{location_result}\n")
            out_f.flush()
            
            # 【重要】学术网站建议加上时间延迟（如 2 秒），避免因请求过快被服务器封禁 IP
            time.sleep(2)
            
    print(f"\n全部预测完成！结果已成功保存至: {output_file_path}")

if __name__ == "__main__":
    # 配置你的输入文件和输出文件路径
    input_fasta_path = "sequences.fasta"  # 你的上百个序列的 fasta 文件路径
    output_file_path = "subcellular_results.txt"  # 预测结果输出路径
    
    # 执行批量预测
    batch_predict_subcellular(input_fasta_path, output_file_path)