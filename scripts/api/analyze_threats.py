#!/usr/bin/env python
import os
import sys
import argparse
from threat_analyzer import analyze_threats, generate_chart, save_server_details

def main():
    parser = argparse.ArgumentParser(description='分析MCP Server威胁类型')
    parser.add_argument('-f', '--file', help='要分析的JSON文件路径', default='')
    parser.add_argument('-o', '--output-dir', help='输出目录', default='./output')
    args = parser.parse_args()
    
    # 如果没有指定文件，尝试使用最新的分析结果文件
    if not args.file:
        output_dir = args.output_dir
        if not os.path.exists(output_dir):
            print(f"错误: 输出目录 {output_dir} 不存在")
            sys.exit(1)
        
        json_files = [f for f in os.listdir(output_dir) if f.startswith('analysis_result_') and f.endswith('.json')]
        if not json_files:
            print(f"错误: 在 {output_dir} 中没有找到分析结果文件")
            sys.exit(1)
        
        latest_file = max(json_files)
        args.file = os.path.join(output_dir, latest_file)
        print(f"使用最新的分析结果文件: {args.file}")
    
    # 确保文件存在
    if not os.path.exists(args.file):
        print(f"错误: 文件 {args.file} 不存在")
        sys.exit(1)
    
    # 分析威胁
    print(f"正在分析文件: {args.file}...")
    threat_counts, servers_by_threat = analyze_threats(args.file)
    
    # 生成图表
    print("正在生成图表...")
    chart_file = generate_chart(threat_counts, args.output_dir)
    
    # 保存服务器详情
    print("正在保存服务器详情...")
    server_file = save_server_details(servers_by_threat, args.output_dir)
    
    # 打印结果摘要
    print(f"\n分析完成!")
    print(f"{'='*50}")
    print(f"威胁类型统计 (共 {sum(threat_counts.values())} 个服务器受影响):")
    
    for threat_type, count in sorted(threat_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {threat_type}: {count} 个服务器")
    
    print(f"\n图表已保存至: {chart_file}")
    print(f"服务器详情已保存至: {server_file}")

if __name__ == "__main__":
    # 生成图表
    
    main() 