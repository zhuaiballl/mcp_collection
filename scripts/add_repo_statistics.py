import json
import os
import subprocess
import argparse
from pathlib import Path
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

def extract_repo_info(github_url):
    """从GitHub URL中提取用户名和仓库名"""
    if not github_url or not isinstance(github_url, str):
        return None, None
    
    # 处理不同格式的GitHub URL
    patterns = [
        r'https://github\.com/([^/]+)/([^/]+)',  # 标准格式
        r'https://github\.com/([^/]+)/([^/]+)/tree/.*',  # 带tree的格式
        r'https://github\.com/([^/]+)/([^/]+)/blob/.*'  # 带blob的格式
    ]
    
    for pattern in patterns:
        match = re.match(pattern, github_url)
        if match:
            user = match.group(1)
            repo = match.group(2)
            # 移除可能的.git后缀
            if repo.endswith('.git'):
                repo = repo[:-4]
            return user, repo
    
    return None, None

def count_code_lines(repo_path):
    """统计仓库的代码行数"""
    try:
        # 使用git ls-files获取所有跟踪的文件，然后使用wc -l统计行数
        cmd = f"cd {repo_path} && git ls-files | xargs cat | wc -l"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            line_count = int(result.stdout.strip())
            return line_count
        else:
            print(f"统计代码行数失败 {repo_path}: {result.stderr}")
            return 0
    except Exception as e:
        print(f"统计代码行数异常 {repo_path}: {str(e)}")
        return 0

def count_commits(repo_path):
    """统计仓库的commit次数"""
    try:
        # 使用git rev-list --count HEAD统计commit次数
        cmd = f"cd {repo_path} && git rev-list --count HEAD"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            commit_count = int(result.stdout.strip())
            return commit_count
        else:
            print(f"统计commit次数失败 {repo_path}: {result.stderr}")
            return 0
    except Exception as e:
        print(f"统计commit次数异常 {repo_path}: {str(e)}")
        return 0

def get_repo_folder_name(user, repo, repo_counter):
    """获取仓库在本地的文件夹名称"""
    # 基础文件夹名称
    base_folder_name = f"{user}_{repo}"
    
    # 处理重复仓库名
    counter = repo_counter.get(base_folder_name, 0)
    folder_name = base_folder_name if counter == 0 else f"{base_folder_name}_{counter}"
    repo_counter[base_folder_name] = counter + 1
    
    return folder_name

def process_server(server, repos_dir, repo_counter):
    """处理单个服务器项目，统计信息并更新"""
    github_url = server.get('github_url', '')
    if not github_url:
        return server, False
    
    user, repo = extract_repo_info(github_url)
    if not user or not repo:
        print(f"无法从URL提取仓库信息: {github_url}")
        return server, False
    
    # 获取仓库文件夹名称
    folder_name = get_repo_folder_name(user, repo, repo_counter)
    repo_path = os.path.join(repos_dir, folder_name)
    
    # 检查仓库是否存在
    if not os.path.exists(repo_path) or not os.path.exists(os.path.join(repo_path, '.git')):
        print(f"仓库不存在: {repo_path}")
        return server, False
    
    # 统计信息
    code_lines = count_code_lines(repo_path)
    commit_count = count_commits(repo_path)
    
    # 更新服务器信息
    server['code_lines'] = code_lines
    server['commit_count'] = commit_count
    
    print(f"已更新 {server.get('name', 'Unknown')}: 代码行数={code_lines}, Commit次数={commit_count}")
    
    return server, True

def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='统计仓库代码行数和commit次数，并更新merged_servers.json')
    parser.add_argument('--json-file', default='metadata/servers/merged_servers.json', 
                       help='merged_servers.json文件路径，默认为metadata/servers/merged_servers.json')
    parser.add_argument('--repos-dir', default='../mcp_servers', 
                       help='仓库所在目录，默认为../mcp_servers')
    parser.add_argument('--output-file', default=None, 
                       help='输出文件路径，默认为覆盖原文件')
    parser.add_argument('--threads', type=int, default=4, 
                       help='并发线程数，默认为4')
    args = parser.parse_args()
    
    # 转换为绝对路径
    json_file = os.path.abspath(args.json_file)
    repos_dir = os.path.abspath(args.repos_dir)
    output_file = os.path.abspath(args.output_file) if args.output_file else json_file
    
    # 检查文件和目录是否存在
    if not os.path.exists(json_file):
        print(f"错误: 文件 {json_file} 不存在")
        return
    
    if not os.path.exists(repos_dir):
        print(f"错误: 目录 {repos_dir} 不存在")
        return
    
    # 读取merged_servers.json
    print(f"读取文件: {json_file}")
    with open(json_file, 'r', encoding='utf-8') as f:
        servers = json.load(f)
    
    if not isinstance(servers, list):
        print(f"错误: {json_file} 不是有效的JSON数组")
        return
    
    print(f"发现 {len(servers)} 个服务器项目")
    
    # 创建仓库计数器
    repo_counter = {}
    
    # 使用线程池并发处理
    updated_servers = []
    success_count = 0
    
    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        # 提交所有任务
        future_to_server = {executor.submit(process_server, server, repos_dir, repo_counter): i 
                           for i, server in enumerate(servers)}
        
        # 按完成顺序处理结果
        for future in as_completed(future_to_server):
            i = future_to_server[future]
            try:
                server, success = future.result()
                updated_servers.append((i, server))
                if success:
                    success_count += 1
            except Exception as e:
                print(f"处理项目 {i} 时出错: {str(e)}")
                updated_servers.append((i, servers[i]))
    
    # 按原顺序排序
    updated_servers.sort(key=lambda x: x[0])
    updated_servers = [server for _, server in updated_servers]
    
    # 保存更新后的文件
    print(f"保存更新后的文件到: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(updated_servers, f, ensure_ascii=False, indent=2)
    
    print(f"\n统计结果:")
    print(f"- 总项目数: {len(servers)}")
    print(f"- 成功更新: {success_count}")
    print(f"- 未更新: {len(servers) - success_count}")
    
if __name__ == '__main__':
    main()