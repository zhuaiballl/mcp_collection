import json
import os
import sys
import matplotlib.pyplot as plt
from datetime import datetime
from collections import defaultdict, Counter
from typing import Dict, List, Set, Any
import matplotlib
import matplotlib.font_manager as fm
# 设置matplotlib支持中文显示
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun', 'KaiTi', 'FangSong', 'Arial Unicode MS']
matplotlib.rcParams['axes.unicode_minus'] = False  # 解决保存图像时负号'-'显示为方块的问题

def check_chinese_font_available():
    """
    检查系统是否有可用的中文字体
    
    Returns:
        tuple: (是否有中文字体, 可用的中文字体名称)
    """
    # 需要检查的中文字体
    chinese_fonts = ['SimHei', 'Microsoft YaHei', 'SimSun', 'KaiTi', 'FangSong', 'Arial Unicode MS', 
                     'WenQuanYi Micro Hei', 'WenQuanYi Zen Hei', 'Noto Sans CJK SC', 'Source Han Sans CN']
    
    # 获取系统字体列表
    font_names = [f.name for f in fm.fontManager.ttflist]
    
    # 查找可用的中文字体
    available_fonts = []
    for font in chinese_fonts:
        if font in font_names:
            available_fonts.append(font)
    
    return len(available_fonts) > 0, available_fonts

def analyze_threats(json_file_path: str) -> tuple[Dict[str, int], Dict[str, Set[str]]]:
    """
    分析JSON文件中的威胁类型
    
    Args:
        json_file_path: JSON文件路径
    
    Returns:
        tuple: (威胁类型计数, 每种威胁类型对应的服务器列表)
    """
    # 检查文件是否存在
    if not os.path.exists(json_file_path):
        print(f"错误: 文件 {json_file_path} 不存在")
        sys.exit(1)
    
    try:
        # 读取JSON文件
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 初始化威胁类型计数器和服务器映射
        threat_counts = Counter()
        servers_by_threat = defaultdict(set)
        print(f"共有{len(data)}个服务器含有可能有威胁的代码")
        # 遍历每个服务器
        for server_name, server_data in data.items():
            # 获取该服务器的威胁类型
            if "threat_types" in server_data:
                for threat_type in server_data["threat_types"].keys():
                    # 同一个服务器的同一类型威胁只统计一次
                    threat_counts[threat_type] += 1
                    servers_by_threat[threat_type].add(server_name)
        
        return dict(threat_counts), dict(servers_by_threat)
    
    except json.JSONDecodeError:
        print(f"错误: 无法解析JSON文件 {json_file_path}")
        sys.exit(1)
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)

def generate_chart(threat_counts: Dict[str, int], output_dir: str = './output') -> str:
    """
    根据威胁类型计数生成图表
    
    Args:
        threat_counts: 威胁类型计数字典
        output_dir: 输出目录
    
    Returns:
        str: 图表文件路径
    """
    # 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 排序威胁类型，按数量从大到小
    sorted_threats = sorted(threat_counts.items(), key=lambda x: x[1], reverse=True)
    threat_types = [item[0] for item in sorted_threats]
    counts = [item[1] for item in sorted_threats]
    
    # 检查中文字体是否可用
    has_chinese_font, available_fonts = check_chinese_font_available()
    if has_chinese_font:
        # 设置找到的第一个中文字体
        matplotlib.rcParams['font.sans-serif'] = [available_fonts[0]] + matplotlib.rcParams['font.sans-serif']
        print(f"使用中文字体: {available_fonts[0]}")
    else:
        print("警告: 系统中未找到中文字体，将使用英文显示")
    
    # 尝试设置中文字体
    try:
        # 创建图表
        plt.figure(figsize=(14, 10))
        
        # 如果有中文字体可用，使用中文标题和标签
        # if has_chinese_font:
        if False:
            # 创建主图表
            bars = plt.bar(threat_types, counts, color='cornflowerblue')
            
            # 添加标题和标签
            plt.title('MCP Server 威胁类型分布', fontsize=18, fontweight='bold')
            plt.xlabel('威胁类型', fontsize=14)
            plt.ylabel('COUNT', fontsize=14)
            plt.xticks(rotation=45, ha='right', fontsize=12)
            plt.yticks(fontsize=12)
        else:
            # 创建英文版本的图表
            bars = plt.bar(threat_types, counts, color='cornflowerblue')
            
            # 添加英文标题和标签
            plt.title('MCP Server Threat Type Distribution', fontsize=18, fontweight='bold')
            plt.xlabel('Threat Type', fontsize=14)
            plt.ylabel('Number of Affected Servers', fontsize=14)
            plt.xticks(rotation=45, ha='right', fontsize=12)
            plt.yticks(fontsize=12)
        
        # 在每个柱子上添加数值
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{height:.0f}', ha='center', va='bottom', fontsize=12)
    
    except Exception as e:
        print(f"警告: 图表创建失败 ({e})，切换到基本英文显示...")
        plt.close()
        
        # 创建基本英文版本的图表
        plt.figure(figsize=(14, 10))
        bars = plt.bar(threat_types, counts, color='cornflowerblue')
        
        # 添加英文标题和标签
        plt.title('MCP Server Threat Type Distribution', fontsize=18, fontweight='bold')
        plt.xlabel('Threat Type', fontsize=14)
        plt.ylabel('Number of Affected Servers', fontsize=14)
        plt.xticks(rotation=45, ha='right', fontsize=12)
        plt.yticks(fontsize=12)
        
        # 在每个柱子上添加数值
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{height:.0f}', ha='center', va='bottom', fontsize=12)
    
    plt.tight_layout()
    
    # 生成带时间戳的输出文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    chart_file = os.path.join(output_dir, f'threat_distribution_{timestamp}.png')
    
    # 保存图表，使用高DPI以获得更清晰的图像
    plt.savefig(chart_file, dpi=300)
    plt.close()
    
    return chart_file

def save_server_details(servers_by_threat: Dict[str, Set[str]], output_dir: str = './output') -> str:
    """
    保存每种威胁类型对应的服务器列表到文件
    
    Args:
        servers_by_threat: 每种威胁类型对应的服务器集合
        output_dir: 输出目录
    
    Returns:
        str: 输出文件路径
    """
    # 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 生成带时间戳的输出文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f'threat_servers_{timestamp}.txt')
    
    # 写入文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("MCP Server 威胁类型详情\n")
        f.write("=" * 50 + "\n\n")
        
        # 按威胁类型数量排序
        sorted_threats = sorted(servers_by_threat.items(), key=lambda x: len(x[1]), reverse=True)
        
        for threat_type, servers in sorted_threats:
            f.write(f"{threat_type} (影响 {len(servers)} 个服务器):\n")
            for server in sorted(servers):
                f.write(f"  - {server}\n")
            f.write("\n")
    
    return output_file

def main():
    # 检查命令行参数
    if len(sys.argv) < 2:
        print("使用方法: python threat_analyzer.py <json_file_path>")
        print("示例: python threat_analyzer.py ../output/analysis_result_20250506_114553.json")
        
        # 查找最新的分析结果文件
        output_dir = './output'
        if os.path.exists(output_dir):
            json_files = [f for f in os.listdir(output_dir) if f.startswith('analysis_result_') and f.endswith('.json')]
            if json_files:
                latest_file = max(json_files)
                json_file_path = os.path.join(output_dir, latest_file)
                print(f"\n找到最新的分析结果文件: {json_file_path}")
                print(f"使用此文件进行分析...\n")
            else:
                print("\n错误: 未找到分析结果文件")
                sys.exit(1)
        else:
            print("\n错误: 输出目录不存在")
            sys.exit(1)
    else:
        json_file_path = sys.argv[1]
    
    # 分析威胁
    threat_counts, servers_by_threat = analyze_threats(json_file_path)
    
    # 生成图表
    chart_file = generate_chart(threat_counts)
    
    # 保存服务器详情
    server_file = save_server_details(servers_by_threat)
    
    # 打印结果摘要
    print(f"\n分析完成!")
    print(f"{'='*50}")
    print(f"威胁类型统计 (共 {sum(threat_counts.values())} 个服务器受影响):")
    
    for threat_type, count in sorted(threat_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {threat_type}: {count} 个服务器")
    
    print(f"\n图表已保存至: {chart_file}")
    print(f"服务器详情已保存至: {server_file}")

if __name__ == "__main__":
    # 对最新的分析结果生成统计图表
    main() 
