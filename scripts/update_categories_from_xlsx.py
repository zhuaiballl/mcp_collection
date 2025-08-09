import json
import os
import argparse
import pandas as pd
from pathlib import Path

# 设置命令行参数
parser = argparse.ArgumentParser(description='Update categories in JSON file from Excel files')
parser.add_argument('--excel_prefix', default='smithery', help='Prefix of Excel files to process (default: smithery)')
parser.add_argument('--excel_dir', default='metadata/servers/xlsx/category_lists', help='Directory containing Excel files (default: metadata/servers/xlsx/category_lists)')
parser.add_argument('--json_dir', default='metadata/servers', help='Directory containing target JSON files (default: metadata/servers)')
args = parser.parse_args()

# 确定目标JSON文件路径
json_filename = f'{args.excel_prefix}.json'
json_path = os.path.join(args.json_dir, json_filename)

# 检查JSON文件是否存在
if not os.path.exists(json_path):
    print(f"Error: JSON file not found at {json_path}")
    exit(1)

# 创建备份
backup_path = f'{json_path}.backup'
with open(json_path, 'r', encoding='utf-8') as f:
    with open(backup_path, 'w', encoding='utf-8') as backup:
        backup.write(f.read())
print(f"Created backup of JSON file: {backup_path}")

# 读取JSON数据
with open(json_path, 'r', encoding='utf-8') as f:
    json_data = json.load(f)

# 创建detail_url到条目的映射
url_to_entry = {entry['detail_url']: entry for entry in json_data}
print(f"Loaded {len(json_data)} entries from {json_path}")

# 获取Excel目录中的所有匹配文件
excel_dir = args.excel_dir
if not os.path.exists(excel_dir):
    print(f"Error: Excel directory not found at {excel_dir}")
    exit(1)

# 遍历所有匹配的Excel文件
excel_files = [f for f in os.listdir(excel_dir) if f.startswith(args.excel_prefix) and f.endswith('.xlsx')]
if not excel_files:
    print(f"No Excel files found with prefix '{args.excel_prefix}' in {excel_dir}")
    exit(1)

added_count = 0
updated_count = 0

for excel_file in excel_files:
    # 从文件名提取分类标签（去掉前缀和扩展名）
    category = excel_file[len(args.excel_prefix):-5].strip()
    # 去除前导下划线（如果有）
    if category.startswith('_'):
        category = category[1:]
    # 将剩余下划线替换为空格
    category = category.replace('_', ' ')
    if not category:
        category = args.excel_prefix
    print(f"Processing {excel_file} with category '{category}'")

    # 读取Excel文件
    excel_path = os.path.join(excel_dir, excel_file)
    try:
        df = pd.read_excel(excel_path)
        print(f"Loaded {len(df)} rows from {excel_file}")
    except Exception as e:
        print(f"Error reading {excel_file}: {e}")
        continue

    # 检查必要的列是否存在
    required_columns = ['name', 'description', 'server-href']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"Warning: Missing required columns in {excel_file}: {missing_columns}")
        continue

    # 处理每一行
    for _, row in df.iterrows():
        server_href = row['server-href']
        if pd.isna(server_href):
            continue

        server_href = str(server_href).strip()
        if not server_href:
            continue

        # 检查是否存在于JSON中
        if server_href in url_to_entry:
            # 存在则更新分类
            entry = url_to_entry[server_href]
            if 'categories' not in entry:
                entry['categories'] = []
            if category not in entry['categories']:
                entry['categories'].append(category)
                updated_count += 1
        else:
            # 不存在则创建新条目
            new_entry = {
                'name': str(row['name']).strip() if not pd.isna(row['name']) else '',
                'description': str(row['description']).strip() if not pd.isna(row['description']) else '',
                'detail_url': server_href,
                'categories': [category]
            }
            # 添加github_url如果存在
            if 'github_url-href' in df.columns and not pd.isna(row['github_url-href']):
                new_entry['github_url'] = str(row['github_url-href']).strip()
            # 添加到JSON数据
            json_data.append(new_entry)
            url_to_entry[server_href] = new_entry
            added_count += 1

# 写回JSON文件
with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(json_data, f, indent=2, ensure_ascii=False)

print(f"Updated {updated_count} entries and added {added_count} new entries in {json_path}")
print("Task completed successfully!")