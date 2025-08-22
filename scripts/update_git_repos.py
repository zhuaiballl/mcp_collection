import os
import subprocess
import argparse
from pathlib import Path

def update_git_repo(repo_path):
    """更新单个Git仓库到最新版本"""
    try:
        # 检查是否是Git仓库
        if not os.path.exists(os.path.join(repo_path, '.git')):
            return False, f"{repo_path} 不是Git仓库"

        # 执行git pull
        result = subprocess.run(
            ['git', '-C', repo_path, 'pull'],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            return True, f"{repo_path} 更新成功: {result.stdout.strip()}"
        else:
            return False, f"{repo_path} 更新失败: {result.stderr.strip()}"
    except Exception as e:
        return False, f"{repo_path} 更新出错: {str(e)}"

def update_all_repos(base_dir):
    """更新指定目录下的所有Git仓库"""
    if not os.path.exists(base_dir):
        print(f"错误: 目录 {base_dir} 不存在")
        return

    # 获取目录下的所有子目录
    subdirs = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]

    if not subdirs:
        print(f"警告: 目录 {base_dir} 下没有子目录")
        return

    print(f"发现 {len(subdirs)} 个项目，开始更新...")

    success_count = 0
    fail_count = 0
    fail_details = []

    for subdir in subdirs:
        repo_path = os.path.join(base_dir, subdir)
        success, message = update_git_repo(repo_path)
        if success:
            success_count += 1
            print(f"✅ {message}")
        else:
            fail_count += 1
            fail_details.append(message)
            print(f"❌ {message}")

    print("\n更新结果总结:")
    print(f"✅ 成功更新: {success_count}")
    print(f"❌ 更新失败: {fail_count}")

    if fail_count > 0:
        print("\n失败详情:")
        for detail in fail_details:
            print(f"  - {detail}")

if __name__ == '__main__':
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='更新MCP服务器项目到最新版本')
    parser.add_argument('--dir', default='../mcp_servers', help='MCP服务器项目所在目录，默认为../mcp_servers')
    args = parser.parse_args()

    # 转换为绝对路径
    base_dir = os.path.abspath(args.dir)

    print(f"开始更新 {base_dir} 目录下的所有MCP服务器项目...")
    update_all_repos(base_dir)