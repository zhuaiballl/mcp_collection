#!/usr/bin/env python3
"""
提取merged_servers.json中的name和commit_count字段并写入CSV文件
"""
import json
import csv
import os
import argparse
from typing import List, Dict, Any


def extract_server_commit_counts(json_file: str, output_csv: str) -> None:
    """
    从JSON文件中提取name和commit_count字段并写入CSV文件
    
    Args:
        json_file: 包含服务器数据的JSON文件路径
        output_csv: 输出的CSV文件路径
    """
    try:
        # 读取JSON文件
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # 确保数据是列表格式
        if not isinstance(data, list):
            data = [data]
            
        # 准备CSV数据
        csv_data = []
        skipped_count = 0
        
        for item in data:
            # 提取name字段
            name = item.get('name', 'Unknown')
            
            # 只处理有commit_count字段且不为None的项目
            commit_count = item.get('commit_count')
            if commit_count is not None:
                csv_data.append({
                    'name': name,
                    'commit_count': commit_count
                })
            else:
                skipped_count += 1
        
        # 确保输出目录存在
        output_dir = os.path.dirname(output_csv)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 写入CSV文件
        with open(output_csv, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['name', 'commit_count']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            # 写入表头
            writer.writeheader()
            
            # 写入数据
            writer.writerows(csv_data)
        
        print(f"成功提取了 {len(csv_data)} 条服务器数据")
        print(f"跳过了 {skipped_count} 个缺少commit_count字段的项目")
        print(f"数据已保存到: {output_csv}")
        
    except Exception as e:
        print(f"处理过程中发生错误: {str(e)}")
        raise


if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='提取merged_servers.json中的name和commit_count字段')
    parser.add_argument('--json-file', 
                        default='/Users/ghc/code/mcp_collection/metadata/servers/merged_servers.json',
                        help='输入的JSON文件路径')
    parser.add_argument('--output-csv', 
                        default='/Users/ghc/code/mcp_collection/analysis/server_commit_counts.csv',
                        help='输出的CSV文件路径')
    
    args = parser.parse_args()
    
    # 执行提取操作
    extract_server_commit_counts(args.json_file, args.output_csv)