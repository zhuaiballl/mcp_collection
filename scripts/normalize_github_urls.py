import json
import re
import sys
import os
from pathlib import Path

def normalize_github_url(url):
    """
    规范化 GitHub URL 为标准格式 https://github.com/owner/reponame
    如果无法规范化，则返回 None
    """
    if not url:
        return None

    # 标准格式匹配
    standard_match = re.match(r'^https://github\.com/([^/]+)/([^/]+)/?$', url)
    if standard_match:
        return url.rstrip('/')  # 移除末尾可能的斜杠

    # SSH 格式匹配 git@github.com:owner/reponame.git
    ssh_match = re.match(r'^git@github\.com:([^/]+)/([^/]+)(\.git)?/?$', url)
    if ssh_match:
        owner, repo = ssh_match.groups()[0], ssh_match.groups()[1]
        return f'https://github.com/{owner}/{repo}'

    # 没有协议的格式匹配 github.com/owner/reponame
    no_proto_match = re.match(r'^github\.com/([^/]+)/([^/]+)/?$', url)
    if no_proto_match:
        owner, repo = no_proto_match.groups()
        return f'https://github.com/{owner}/{repo}'

    # 包含分支、子目录或文件的格式匹配
    path_match = re.match(r'^https://github\.com/([^/]+)/([^/]+)/(?:tree|blob)/.*$', url)
    if path_match:
        owner, repo = path_match.groups()
        return f'https://github.com/{owner}/{repo}'

    # 其他可能的格式
    other_match = re.match(r'^https://github\.com/([^/]+)/([^/]+)', url)
    if other_match:
        owner, repo = other_match.groups()
        return f'https://github.com/{owner}/{repo}'

    # 无法识别的格式
    return None


def process_json_file(input_file, output_file=None):
    """处理 JSON 文件，规范化其中的 GitHub URL"""
    try:
        # 读取输入文件
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not isinstance(data, list):
            raise ValueError("JSON 文件内容必须是数组格式")

        # 处理每个条目
        log_messages = []
        for i, item in enumerate(data):
            if 'github_url' in item:
                original_url = item['github_url']
                normalized_url = normalize_github_url(original_url)

                if normalized_url is None:
                    log_messages.append(f"条目 {i}: 无法规范化 GitHub URL: {original_url}")
                    item['github_url'] = ''
                elif normalized_url != original_url:
                    log_messages.append(f"条目 {i}: 规范化 GitHub URL: {original_url} -> {normalized_url}")
                    item['github_url'] = normalized_url

        # 确定输出文件路径
        if output_file is None:
            # 在输入文件名前添加 'normalized_' 前缀
            input_path = Path(input_file)
            output_file = input_path.parent / f'normalized_{input_path.name}'

        # 写入输出文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # 打印日志
        print(f"成功处理文件: {input_file}")
        print(f"输出文件: {output_file}")
        if log_messages:
            print("\n日志信息:")
            for message in log_messages:
                print(f"- {message}")
        else:
            print("\n没有需要规范化的 GitHub URL")

        return True

    except Exception as e:
        print(f"处理文件时出错: {str(e)}", file=sys.stderr)
        return False


def main():
    if len(sys.argv) < 2:
        print("用法: python normalize_github_urls.py <输入JSON文件> [输出JSON文件]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    if not os.path.exists(input_file):
        print(f"错误: 输入文件 '{input_file}' 不存在")
        sys.exit(1)

    process_json_file(input_file, output_file)


if __name__ == '__main__':
    main()