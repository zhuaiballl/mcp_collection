import json
import subprocess
import re
import os
import requests
from pathlib import Path
import argparse
from urllib.parse import urlparse

def process_github_url(url):
    """处理GitHub URL，提取标准格式：https://github.com/user/repo"""
    if not url or not isinstance(url, str):
        return None, None, None
    url = url.strip()
    
    # 确保URL以https开头
    if url.startswith('//github.com'):
        url = 'https:' + url
    elif url.startswith('github.com'):
        url = 'https://' + url
    elif not url.startswith('https://'):
        return None, None, None
    
    # 解析URL
    parsed_url = urlparse(url)
    if parsed_url.netloc != 'github.com':
        return None, None, None
    
    # 提取用户和仓库名
    path_parts = parsed_url.path.strip('/').split('/')
    if len(path_parts) < 2:
        return None, None, None
    
    user = path_parts[0]
    repo = path_parts[1]
    
    # 移除可能错误包含的git相关后缀
    git_suffixes = ['.git', '.gitcd', '.github', '.gitignore', '.gitmodules']
    for suffix in git_suffixes:
        if repo.endswith(suffix):
            repo = repo[:-len(suffix)]
    
    # 验证用户名和仓库名格式
    user_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-_]*[a-zA-Z0-9])?$'
    repo_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-_.]*[a-zA-Z0-9])?$'
    
    if (user and repo and 
        re.match(user_pattern, user) and re.match(repo_pattern, repo) and 
        len(user) <= 39 and len(repo) <= 100):  # GitHub限制
        return f"https://github.com/{user}/{repo}", user, repo
    
    return None, None, None

def check_repo_exists(url, headers):
    """检查仓库是否存在并可访问"""
    api_url = url.replace('https://github.com', 'https://api.github.com/repos')
    try:
        response = requests.get(api_url, headers=headers, timeout=10)
        if response.status_code == 200:
            return True
        elif response.status_code == 404:
            print(f"❌ 仓库不存在: {url}")
        else:
            print(f"❌ 检查仓库状态失败: {url}, 状态码: {response.status_code}")
        return False
    except Exception as e:
        print(f"❌ 检查仓库状态时出错: {url}, 错误: {e}")
        return False

def clone_repo(url, output_dir, user, repo, repo_counter, headers):
    """使用GitHub API克隆仓库到指定目录，处理重复仓库名"""
    # 基础文件夹名称
    base_folder_name = f"{user}_{repo}"
    
    # 处理重复仓库名
    counter = repo_counter.get(base_folder_name, 0)
    folder_name = base_folder_name if counter == 0 else f"{base_folder_name}_{counter}"
    repo_counter[base_folder_name] = counter + 1
    
    dest = output_dir / folder_name

    if dest.exists():
        print(f"已存在: {dest}")
        return None

    # 检查仓库是否存在
    if not check_repo_exists(url, headers):
        return url

    print(f"\n克隆: {dest}")
    
    # 构建带认证的URL
    github_token = headers['Authorization'].split(' ')[1]
    auth_url = url.replace('https://', f'https://{github_token}@')
    
    # 执行克隆命令
    process = subprocess.Popen(
        ["git", "clone", auth_url, str(dest)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    for line in process.stdout:
        print(f"   [{folder_name}] {line.strip()}")
    retcode = process.wait()
    if retcode != 0:
        print(f"❌ 克隆失败: {dest}")
        return url
    else:
        print(f"✅ 克隆成功: {dest}")
        return None

def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='使用GitHub API从JSON文件克隆GitHub仓库')
    parser.add_argument('input_json', help='包含github_url的JSON文件路径')
    parser.add_argument('output_dir', help='克隆仓库的输出目录')
    args = parser.parse_args()
    
    # 读取GITHUB_TOKEN环境变量
    github_token = os.environ.get('GITHUB_TOKEN')
    if not github_token:
        print("❌ 未找到GITHUB_TOKEN环境变量")
        return
    
    # 设置请求头
    headers = {
        'Authorization': f'token {github_token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # 读取JSON文件
    try:
        with open(args.input_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"读取JSON文件失败: {e}")
        return
    
    # 确保输出目录存在
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # 提取并处理GitHub URL
    url_info = []
    for item in data:
        if 'github_url' in item:
            url, user, repo = process_github_url(item['github_url'])
            if url and user and repo:
                url_info.append((url, user, repo))
    
    # 去重
    unique_url_info = list(set(url_info))
    print(f"\n📊 GitHub仓库统计:")
    print(f"   - 去重后总共有 {len(unique_url_info)} 个唯一GitHub仓库")
    
    # 克隆仓库
    print(f"\n🚀 开始克隆 {len(unique_url_info)} 个仓库...")
    failed_urls = []
    repo_counter = {}  # 用于跟踪重复的仓库名
    
    for url, user, repo in unique_url_info:
        failed = clone_repo(url, output_dir, user, repo, repo_counter, headers)
        if failed:
            failed_urls.append(failed)
    
    # 处理失败的克隆
    if failed_urls:
        with open(output_dir / "clone_failed.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(failed_urls))
        print(f"\n⚠️ {len(failed_urls)} 个仓库克隆失败，详见 clone_failed.txt")
    else:
        print("\n🎉 所有仓库克隆成功")

if __name__ == "__main__":
    main()