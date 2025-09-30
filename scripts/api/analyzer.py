import os
import sys
import json
import traceback
from typing import Dict, List, Any
import ast
import time
from datetime import datetime
from dangerous_apis import get_checker
import argparse
import re
import pandas as pd  # 新增pandas用于处理Excel数据
import requests      # 新增requests用于调用GitHub API
from collections import defaultdict  # 新增defaultdict用于数据统计

# ... existing code ...
class CodeAnalyzer:
    def __init__(self, base_dir: str = "../mcp_servers", max_servers: int = None, excel_path: str = None, json_path: str = None):
        # 确保base_dir是绝对路径
        self.base_dir = os.path.abspath(base_dir)
        self.max_servers = max_servers  # None表示不限制
        self.excel_path = excel_path    # 新增Excel文件路径
        self.json_path = json_path      # 新增JSON文件路径
        self.results: Dict[str, List[Dict[str, Any]]] = {} 
        self.analyzed_servers = set()  # 用于跟踪已分析的服务器

        # 新增用于存储仓库类别和星星数量的字典
        self.repo_categories = defaultdict(list)  # 用于存储仓库->类别列表的映射
        self.repo_stars = {}                      # 用于存储仓库->星星数量的映射
        self.repo_to_server_mapping = {}          # 用于存储仓库到服务器的映射
        self.server_to_repo_mapping = {}          # 用于存储服务器到仓库的映射

        # 添加需要排除的目录
        self.excluded_dirs = {
            'node_modules',
            'venv',
            '.git',
            '__pycache__',
            'dist',
            'build',
            'target',  # Rust的构建目录
            'vendor',  # Go的依赖目录
            'packages', # NuGet包目录
            'bin',
            'obj',     # .NET构建目录
            'lib',
            'libs',
            'external',
            'third_party',
            'third-party',
            'ext',
            'deps',
            'dependencies'
        }
        
    def load_json_data(self):
        """加载merged_servers.json文件中的仓库数据"""
        if not self.json_path or not os.path.exists(self.json_path):
            print(f"JSON文件不存在或未指定: {self.json_path}")
            return False
            
        try:
            print(f"\n加载JSON数据: {self.json_path}")
            with open(self.json_path, 'r', encoding='utf-8') as f:
                servers_data = json.load(f)
                
            # 处理数据创建仓库映射
            for server_info in servers_data:
                # 获取GitHub仓库URL
                repo_url = server_info.get('github_url', '')
                if not repo_url or not isinstance(repo_url, str):
                    continue
                       
                # 获取服务器名称
                server_name = server_info.get('name', '')
                if not server_name:
                    # 尝试从URL提取服务器名称
                    if 'github.com' in repo_url:
                        url_parts = repo_url.split('/')
                        if len(url_parts) >= 2:
                            server_name = url_parts[-1]
                            if server_name.endswith('.git'):
                                server_name = server_name[:-4]
                    else:
                        continue
                       
                # 从URL提取仓库名称 (格式: https://github.com/owner/repo)
                if 'github.com' in repo_url:
                    repo_name = repo_url.replace('https://github.com/', '')
                    if repo_name.endswith('.git'):
                        repo_name = repo_name[:-4]
                    repo_name = repo_name.rstrip('/')
                    
                    # 将仓库名与服务器名关联起来
                    self.repo_to_server_mapping[repo_name] = server_name
                    self.server_to_repo_mapping[server_name] = repo_name
                    
                    # 处理类别信息
                    categories = server_info.get('categories', [])
                    metadata_categories = server_info.get('metadata', {}).get('categories', [])
                    
                    # 合并所有类别
                    all_categories = []
                    if isinstance(categories, list):
                        all_categories.extend(categories)
                    if isinstance(metadata_categories, list):
                        all_categories.extend(metadata_categories)
                    
                    # 添加到仓库类别列表
                    for category in all_categories:
                        if category and isinstance(category, str):
                            self.repo_categories[repo_name].append(category)
                    
                    # 如果没有类别信息，设置为Unknown
                    if not all_categories:
                        self.repo_categories[repo_name].append('Unknown')
                    
                    print(f"仓库 {repo_name} 添加到映射，服务器名称: {server_name}")
            
            print(f"成功从JSON加载 {len(self.repo_categories)} 个仓库的信息")
            return True
        except Exception as e:
            print(f"加载JSON数据时出错: {str(e)}")
            traceback.print_exc()
            return False
            
    def analyze_all(self) -> Dict[str, List[Dict[str, Any]]]:
        """分析所有支持的语言的源码并获取Git仓库信息"""
        # 初始化结果字典，支持所有语言
        self.results = {
            'python': [],
            'typescript': [],
            'rust': [],
            'go': [],
            'java': [],
            'c': [],
            'cpp': [],
            'csharp': [],
            'ruby': [],
            'php': [],
            'swift': [],
            'kotlin': []
        }
        
        # 用于跟踪已有分析结果的服务器
        servers_with_cached_results = set()
        
        print(f"\n{'='*50}")
        if self.max_servers:
            print(f"开始分析 (限制为 {self.max_servers} 个服务器)...")
        else:
            print(f"开始分析所有服务器...")
        print(f"{'='*50}")
        
        # 确保使用绝对路径
        base_dir = os.path.abspath(self.base_dir)
        
        # 初始化映射关系
        self.server_to_repo_mapping = {}  # 服务器名称到仓库的映射
        self.repo_stars = {}  # 仓库名称 -> 星星数
        self.repo_categories = defaultdict(list)  # 仓库名称 -> 类别列表
        
        # 从JSON或Excel加载GitHub URL和信息
        json_data = []  # 存储处理后的JSON数据
        excel_data = []  # 存储处理后的Excel数据，包含所有必要信息
        
        if self.json_path and os.path.exists(self.json_path):
            try:
                with open(self.json_path, 'r', encoding='utf-8') as f:
                    servers_data = json.load(f)
                
                print(f"\n从JSON加载仓库数据: {self.json_path}")
                print(f"JSON数据服务器数量: {len(servers_data)}")
                
                # 处理JSON数据
                for server_info in servers_data:
                    github_url = server_info.get('github_url', '')
                    server_name = server_info.get('name', '')
                    categories = server_info.get('categories', [])
                    metadata_categories = server_info.get('metadata', {}).get('categories', [])
                    
                    # 确保GitHub URL是有效的
                    if not github_url or not isinstance(github_url, str):
                        continue
                    
                    # 如果没有服务器名称，尝试从URL提取
                    if not server_name:
                        if 'github.com' in github_url:
                            url_parts = github_url.split('/')
                            if len(url_parts) >= 2:
                                server_name = url_parts[-1]
                                if server_name.endswith('.git'):
                                    server_name = server_name[:-4]
                        else:
                            continue
                    
                    # 添加到处理后的JSON数据
                    json_data.append({
                        'github_url': github_url,  # 保持原始URL格式
                        'normalized_url': self.normalize_github_url(github_url),  # 标准化后的URL
                        'server_name': server_name,
                        'categories': categories,
                        'metadata_categories': metadata_categories
                    })
                
                print(f"从JSON处理了 {len(json_data)} 条有效记录")
                
            except Exception as e:
                print(f"从JSON加载数据时出错: {str(e)}")
                traceback.print_exc()
        elif self.excel_path and os.path.exists(self.excel_path):
            try:
                df = pd.read_excel(self.excel_path)
                print(f"\n从Excel加载仓库数据: {self.excel_path}")
                print(f"Excel数据行数: {len(df)}")
                
                # 处理Excel数据
                for _, row in df.iterrows():
                    github_url = row.get('github_url-href', '')
                    star_count = row.get('github_star_num', 0)
                    category = row.get('url', '')
                    server_url = row.get('web-scraper-start-url', '')
                    
                    # 确保GitHub URL是有效的
                    if not github_url or not isinstance(github_url, str):
                        continue
                    
                    # 处理星星数
                    try:
                        star_count = int(star_count)
                    except (ValueError, TypeError):
                        if isinstance(star_count, str) and star_count.strip():
                            try:
                                # 处理可能带逗号的数字
                                star_count = int(star_count.replace(',', ''))
                            except:
                                star_count = 0
                        else:
                            star_count = 0
                    
                    # 添加到处理后的Excel数据
                    excel_data.append({
                        'github_url': github_url,  # 保持原始URL格式
                        'normalized_url': self.normalize_github_url(github_url),  # 标准化后的URL
                        'stars': star_count,
                        'category': category,
                        'server_url': server_url
                    })
                
                print(f"从Excel处理了 {len(excel_data)} 条有效记录")
                
            except Exception as e:
                print(f"从Excel加载数据时出错: {str(e)}")
                traceback.print_exc()
        
        # 遍历服务器目录，根据文件夹名称进行匹配
        try:
            # 第一次遍历：获取服务器到GitHub URL的映射
            print("\n从服务器目录获取Git仓库信息...")
            
            # 初始化服务器路径映射
            server_paths = {}
            
            # 遍历所有目录，查找符合{user}_{repo}或{user}_{repo}_{counter}格式的文件夹
            for item in os.listdir(base_dir):
                item_path = os.path.join(base_dir, item)
                if not os.path.isdir(item_path) or item in self.excluded_dirs:
                    continue
                
                server_paths[item] = item_path
            
            print(f"在 {base_dir} 中找到 {len(server_paths)} 个目录")
            
            # 根据文件夹名称进行匹配
            for server_name, server_path in server_paths.items():
                # 检查是否达到服务器数量限制
                if self.max_servers and len(self.analyzed_servers) >= self.max_servers:
                    print(f"\n已达到最大分析服务器数量 ({self.max_servers})")
                    break
                
                # 添加到已分析服务器列表
                self.analyzed_servers.add(server_name)
                
                # 尝试从.git目录加载已有的分析结果
                cached_results = self.load_analysis_result(server_path)
                # if cached_results:
                #     print(f"使用服务器 {server_name} 的缓存分析结果")
                #     # 更新结果字典
                #     for lang, issues in cached_results.items():
                #         if lang in self.results:
                #             self.results[lang].extend(issues)
                #     
                #     # 记录此服务器已有分析结果
                #     servers_with_cached_results.add(server_name)
                #     continue
                
                # 根据文件夹名称提取user和repo信息
                # 支持格式: {user}_{repo} 或 {user}_{repo}_{counter}
                parts = server_name.split('_')
                if len(parts) >= 2:
                    # 提取user和repo
                    # 处理可能包含下划线的仓库名称
                    # 假设第一个下划线分隔的是用户名，其余部分合并为仓库名
                    user = parts[0]
                    repo_parts = parts[1:]
                    
                    # 检查最后一部分是否是数字（计数器）
                    if len(repo_parts) > 1 and repo_parts[-1].isdigit():
                        # 去掉计数器部分
                        repo = '_'.join(repo_parts[:-1])
                    else:
                        repo = '_'.join(repo_parts)
                    
                    # 构建完整的仓库名称 (owner/repo)
                    repo_name = f"{user}/{repo}"
                    
                    # 设置映射关系
                    self.server_to_repo_mapping[server_name] = repo_name
                    
                    print(f"服务器 {server_name} -> 仓库 {repo_name}")
                    
                    # 寻找匹配的元数据
                    match_found = False
                    # 先尝试在JSON数据中匹配
                    if json_data:
                        for item in json_data:
                            if 'github.com' in item['github_url'] and repo_name in item['github_url'].lower():
                                # 合并所有类别
                                all_categories = []
                                if isinstance(item['categories'], list):
                                    all_categories.extend(item['categories'])
                                if isinstance(item['metadata_categories'], list):
                                    all_categories.extend(item['metadata_categories'])
                                  
                                for category in all_categories:
                                    if category and isinstance(category, str):
                                        self.repo_categories[repo_name].append(category)
                                  
                                # 如果没有类别信息，设置为Unknown
                                if not all_categories:
                                    self.repo_categories[repo_name].append('Unknown')
                                  
                                match_found = True
                                print(f"  成功匹配! {server_name} -> {repo_name}")
                                break
                    # 如果JSON匹配失败，尝试Excel数据
                    if not match_found and excel_data:
                        for item in excel_data:
                            if 'github.com' in item['github_url'] and repo_name in item['github_url'].lower():
                                self.repo_stars[repo_name] = item['stars']
                                self.repo_categories[repo_name].append(item['category'])
                                match_found = True
                                print(f"  成功匹配! {server_name} -> {repo_name} (星星: {item['stars']})")
                                break
                    
                    if not match_found:
                        print(f"  警告: 服务器 '{server_name}' 的仓库名称 '{repo_name}' 在元数据中没有匹配项")
                else:
                    print(f"  警告: 服务器名称 '{server_name}' 不符合预期格式")
            
            # 输出匹配结果
            print(f"\n成功匹配了 {len(self.server_to_repo_mapping)}/{len(self.analyzed_servers)} 个服务器到元数据中的仓库")
            
            # 打印星星数分布信息
            star_ranges = [
                (0, 10),
                (11, 100),
                (101, 500),
                (501, 1000),
                (1001, 10000),
                (10001, 50000),
                (50001, float('inf'))
            ]
            
            range_counts = [0] * len(star_ranges)
            for _, stars in self.repo_stars.items():
                for i, (min_val, max_val) in enumerate(star_ranges):
                    if min_val <= stars <= max_val:
                        range_counts[i] += 1
                        break
            
            print("\n仓库星星数范围分布:")
            for i, (min_val, max_val) in enumerate(star_ranges):
                range_label = f"{min_val}-{max_val if max_val != float('inf') else '+'}"
                print(f"  {range_label}: {range_counts[i]} 个仓库")
            
            # 每个服务器的分析结果 {服务器名称 -> {语言 -> 问题列表}}
            server_results = {}
            
            # 第二次遍历：进行代码分析
            for server_name, server_path in server_paths.items():
                # 检查是否达到服务器数量限制
                if self.max_servers and len(self.analyzed_servers) >= self.max_servers:
                    print(f"\n已达到最大分析服务器数量 ({self.max_servers})")
                    break
                     
                # 如果服务器不在已分析列表中，则跳过
                if server_name not in self.analyzed_servers:
                    continue
                # 如果服务器已有缓存结果，则跳过
                if server_name in servers_with_cached_results:
                    continue
                     
                # 遍历服务器目录下的所有文件
                for root, dirs, files in os.walk(server_path):
                    # 从遍历列表中移除需要排除的目录
                    dirs[:] = [d for d in dirs if d not in self.excluded_dirs]
                     
                    for file in files:
                        try:
                            file_path = os.path.join(root, file)
                            file_path = os.path.normpath(file_path)  # 标准化路径
                             
                            # 检查文件是否在排除目录中
                            if any(excluded in file_path.split(os.sep) for excluded in self.excluded_dirs):
                                continue
                                 
                            language = self.get_language_by_extension(file_path)
                             
                            # 只处理支持的语言
                            if language in self.results:
                                print(f"\n分析 {language} 文件: {file_path}")
                                # 分析单个文件并将结果添加到对应语言的列表中
                                file_results = self.analyze_file(file_path, language)
                                if file_results:
                                    print(f"发现 {len(file_results)} 个潜在问题")
                                    self.results[language].extend(file_results)
                                     
                                    # 添加到服务器特定结果
                                    if server_name not in server_results:
                                        server_results[server_name] = {lang: [] for lang in self.results}
                                    server_results[server_name][language].extend(file_results)
                                     
                        except Exception as e:
                            print(f"分析文件时出错: {str(e)}")
                            continue
            
            # 保存每个服务器的分析结果到.git目录
            print("\n保存分析结果到各服务器的.git目录...")
            for server_name, results in server_results.items():
                if server_name in server_paths:
                    self.save_analysis_result(server_paths[server_name], results)
                    # print(f"保存成功,{results}")
                else:
                    print(f"警告: 找不到服务器 {server_name} 的路径，无法保存分析结果")
                     
        except Exception as e:
            print(f"遍历目录结构时出错: {str(e)}")
            traceback.print_exc()
        
        # 打印分析结果统计
        print(f"\n{'='*50}")
        print(f"分析摘要:")
        print(f"{'='*50}")
        print(f"已分析的服务器 ({len(self.analyzed_servers)}):")
        print(f"  - 使用缓存结果: {len(servers_with_cached_results)} 个服务器")
        print(f"  - 重新分析: {len(self.analyzed_servers) - len(servers_with_cached_results)} 个服务器")
        
        for server in sorted(self.analyzed_servers):
            repo = self.server_to_repo_mapping.get(server, "未知")
            stars = self.repo_stars.get(repo, "未知")
            cached = "✓" if server in servers_with_cached_results else "✗"
            # print(f"  - {server} -> {repo} (星星数: {stars}, 使用缓存: {cached})")
        
        print(f"\n各语言的问题统计:")
        total_issues = 0
        for language in self.results:
            issue_count = len(self.results[language])
            total_issues += issue_count
            if issue_count > 0:
                print(f"{language}: 发现 {issue_count} 个问题")
        print(f"\n问题总数: {total_issues}")
            
        return self.results


    def analyze_file(self, file_path: str, language: str) -> List[Dict[str, Any]]:
        """分析单个文件中的高危API使用"""
        findings = []
        checker = get_checker(language)
        
        try:
            abs_path = os.path.abspath(file_path)
            try:
                with open(abs_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                # pass
                content = ''
                # 如果 UTF-8 失败，尝试 GBK
                # with open(abs_path, 'r', encoding='gbk') as f:
                #     content = f.read()
                
            # 根据不同语言选择分析方法
            if language == "python":
                try:
                    findings.extend(self._analyze_python_file_ast(content, abs_path, checker))
                except SyntaxError as e:
                    print(f"\nSyntax error in Python file: {abs_path}")
                    print(f"Error details: {str(e)}")
                    print("Falling back to text-based analysis...")
                    findings.extend(self._analyze_file_by_text(content, abs_path, checker))
            else:
                # 对其他语言使用文本分析
                findings.extend(self._analyze_file_by_text(content, abs_path, checker))
                
        except Exception as e:
            print(f"\nError analyzing {abs_path}")
            print(f"Error type: {type(e).__name__}")
            print(f"Error message: {str(e)}")
            print("Stack trace:")
            traceback.print_exc()
            
        return findings
    
    def _analyze_python_file_ast(self, content: str, file_path: str, checker: Any) -> List[Dict[str, Any]]:
        """使用AST分析Python文件"""
        findings = []
        content = content.replace('\x00', '')  # 移除空字节
        tree = ast.parse(content)
        
        # 获取所有函数定义，用于上下文信息
        function_stack = []
        
        class FunctionVisitor(ast.NodeVisitor):
            def visit_FunctionDef(self, node):
                function_stack.append(node.name)
                self.generic_visit(node)
                function_stack.pop()
                
            def visit_Call(self, node):
                if isinstance(node.func, ast.Name):
                    api_name = node.func.id
                    if checker.is_dangerous_api(api_name):
                        findings.append({
                            "file": file_path,
                            "line": node.lineno,
                            "column": node.col_offset,
                            "api_name": api_name,
                            "function": function_stack[-1] if function_stack else "<module>",
                            "description": checker.get_api_description(api_name),
                            "threat_type": checker.get_api_threat_type(api_name)
                        })
                elif isinstance(node.func, ast.Attribute):
                    if isinstance(node.func.value, ast.Name):
                        api_name = f"{node.func.value.id}.{node.func.attr}"
                        if checker.is_dangerous_api(api_name):
                            findings.append({
                                "file": file_path,
                                "line": node.lineno,
                                "column": node.col_offset,
                                "api_name": api_name,
                                "function": function_stack[-1] if function_stack else "<module>",
                                "description": checker.get_api_description(api_name),
                                "threat_type": checker.get_api_threat_type(api_name)
                            })
                self.generic_visit(node)
        
        visitor = FunctionVisitor()
        visitor.visit(tree)
        return findings
    
    def _analyze_file_by_text(self, content: str, file_path: str, checker: Any) -> List[Dict[str, Any]]:
        """基于文本的分析方法"""
        findings = []
        
        # 各语言的注释标记
        comment_markers = {
            "python": "#",
            "typescript": "//",
            "javascript": "//",
            "java": "//",
            "cpp": "//",
            "c": "//",
            "csharp": "//",
            "rust": "//",
            "go": "//",
            "php": "//",
            "ruby": "#",
            "swift": "//",
            "kotlin": "//"
        }
        
        # 各语言的函数定义模式
        function_patterns = {
            "python": r"def\s+(\w+)\s*\(",
            "typescript": r"(function\s+(\w+)|(\w+)\s*=\s*function|(\w+)\s*\([^)]*\)\s*=>|\s*(\w+)\s*\([^)]*\)\s*{)",
            "javascript": r"(function\s+(\w+)|(\w+)\s*=\s*function|(\w+)\s*\([^)]*\)\s*=>|\s*(\w+)\s*\([^)]*\)\s*{)",
            "java": r"(?:public|private|protected|static|\s)+[\w\<\>\[\]]+\s+(\w+)\s*\([^\)]*\)\s*(?:\{|[^;])",
            "cpp": r"[\w\<\>\[\]]+\s+(\w+)\s*\([^\)]*\)\s*(?:\{|[^;])",
            "c": r"[\w\<\>\[\]]+\s+(\w+)\s*\([^\)]*\)\s*(?:\{|[^;])",
            "csharp": r"(?:public|private|protected|internal|static|\s)+[\w\<\>\[\]]+\s+(\w+)\s*\([^\)]*\)\s*(?:\{|[^;])",
            "rust": r"fn\s+(\w+)\s*\(",
            "go": r"func\s+(\w+)\s*\(",
            "php": r"function\s+(\w+)\s*\(",
            "ruby": r"def\s+(\w+)\s*(?:\(|$)",
            "swift": r"func\s+(\w+)\s*\(",
            "kotlin": r"fun\s+(\w+)\s*\("
        }
        
        # 获取文件扩展名
        ext = os.path.splitext(file_path)[1].lower()
        
        # 确定语言
        language = self.get_language_by_extension(file_path)
        
        # 获取对应的注释标记和函数定义模式
        comment_marker = comment_markers.get(language, "#")
        function_pattern = function_patterns.get(language, r"\w+")
        
        # 初始化变量
        lines = content.split("\n")
        current_function = "<module>"  # 默认为模块级别
        
        for i, line in enumerate(lines, 1):
            # 更新当前函数名
            match = re.search(function_pattern, line)
            if match:
                current_function = match.group(1)
                
            # 检查危险API
            for api in checker.dangerous_apis:
                if api in line:
                    # 检查是否是注释行
                    stripped_line = line.lstrip()
                    if stripped_line.startswith(comment_marker):
                        continue
                        
                    # 确保这是一个完整的API调用，而不是变量名的一部分
                    if self._is_valid_api_usage(api, line):
                        findings.append({
                            "file": file_path,
                            "line": i,
                            "column": line.index(api),
                            "api_name": api,
                            "function": current_function,
                            "description": checker.get_api_description(api),
                            "threat_type": checker.get_api_threat_type(api)
                        })
        
        return findings
    
    def _is_valid_api_usage(self, api: str, line: str) -> bool:
        """检查是否是有效的API使用，而不是变量名或注释的一部分"""
        # 简单的检查：API前后应该是空白字符、括号、点或者行的开始/结束
        index = line.find(api)
        if index == -1:
            return False
            
        # 检查API前面的字符
        if index > 0:
            prev_char = line[index - 1]
            if prev_char.isalnum() or prev_char == '_':
                return False
                
        # 检查API后面的字符
        api_end = index + len(api)
        if api_end < len(line):
            next_char = line[api_end]
            if next_char.isalnum() or next_char == '_':
                return False
                
        return True
    
    def scan_directory(self, language: str = None) -> List[Dict[str, Any]]:
        """扫描指定语言或所有语言的源码文件"""
        findings = []
        
        if not os.path.exists(self.base_dir):
            print(f"Base directory not found: {self.base_dir}")
            return findings
            
        # 遍历所有文件
        for root, dirs, files in os.walk(self.base_dir):
            # 从遍历列表中移除需要排除的目录
            dirs[:] = [d for d in dirs if d not in self.excluded_dirs]
            
            # 检查是否达到服务器数量限制
            if self.max_servers and len(self.analyzed_servers) >= self.max_servers:
                print(f"\nReached maximum number of servers to analyze ({self.max_servers})")
                break
                
            for file in files:
                file_path = os.path.join(root, file)
                file_path = os.path.normpath(file_path)  # 标准化路径
                
                # 检查文件是否在排除目录中
                if any(excluded in file_path.split(os.sep) for excluded in self.excluded_dirs):
                    continue
                    
                # 获取服务器名称
                try:
                    path_parts = file_path.split(os.sep)
                    mcp_servers_index = path_parts.index("mcp_servers")
                    # 确保路径结构符合 mcp_servers/language/server_name
                    if len(path_parts) > mcp_servers_index + 2:
                        language_dir = path_parts[mcp_servers_index + 1]  # 语言目录
                        server_name = path_parts[mcp_servers_index + 2]   # 服务器名称
                        # 如果已经达到最大服务器数且不是已分析的服务器，则跳过
                        if self.max_servers and len(self.analyzed_servers) >= self.max_servers and server_name not in self.analyzed_servers:
                            continue
                        self.analyzed_servers.add(server_name)
                except ValueError:
                    continue
                    
                # 获取文件语言
                file_language = self.get_language_by_extension(file_path)
                
                # 如果指定了语言，只分析该语言的文件
                if language and file_language != language:
                    continue
                    
                # 只处理支持的语言
                if file_language in self.results:
                    print(f"\nAnalyzing {file_language} file: {file_path}")
                    file_findings = self.analyze_file(file_path, file_language)
                    if file_findings:
                        print(f"Found {len(file_findings)} potential issues")
                        findings.extend(file_findings)
                        
        return findings
    
    def get_language_by_extension(self, file_path: str) -> str:
        """根据文件后缀确定编程语言"""
        ext = os.path.splitext(file_path)[1].lower()
        language_map = {
            # Python
            '.py': 'python',
            '.pyw': 'python',
            '.pyx': 'python',
            '.pxd': 'python',
            
            # TypeScript/JavaScript
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.js': 'typescript',
            '.jsx': 'typescript',
            '.mjs': 'typescript',
            
            # Rust
            '.rs': 'rust',
            '.rlib': 'rust',
            
            # Go
            '.go': 'go',
            
            # Java
            '.java': 'java',
            '.jar': 'java',
            
            # C/C++
            '.c': 'c',
            '.cpp': 'cpp',
            '.cc': 'cpp',
            '.h': 'c',
            '.hpp': 'cpp',
            
            # C#
            '.cs': 'csharp',
            
            # Ruby
            '.rb': 'ruby',
            '.rake': 'ruby',
            
            # PHP
            '.php': 'php',
            
            # Swift
            '.swift': 'swift',
            
            # Kotlin
            '.kt': 'kotlin',
            '.kts': 'kotlin'
        }
        return language_map.get(ext, 'unknown')



    def save_analysis_result(self, server_path, language_results):
        """
        保存分析结果到服务器的.git目录
        
        Args:
            server_path: 服务器目录路径
            language_results: 分析结果字典
        """
        git_dir = os.path.join(server_path, '.git')
        if not os.path.exists(git_dir):
            print(f"警告: {server_path} 不是一个Git仓库")
            return False
            
        # 创建分析结果文件
        result_file = os.path.join(git_dir, 'code_analysis_result.json')
        
        # 添加元数据
        analysis_data = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'version': '1.0',  # 分析工具版本
            'results': language_results,
        }
        
        try:
            # 保存到JSON文件
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(analysis_data, f, ensure_ascii=False, indent=2)
            print(f"分析结果已保存到: {result_file}")
            return True
        except Exception as e:
            print(f"保存分析结果到 {result_file} 失败: {str(e)}")
            return False

    def load_analysis_result(self, server_path):
        """
        从.git目录加载已保存的分析结果
        
        Args:
            server_path: 服务器目录路径
        
        Returns:
            分析结果字典，如果不存在则返回None
        """
        result_file = os.path.join(server_path, '.git', 'code_analysis_result.json')
        
        if not os.path.exists(result_file):
            return None
            
        try:
            with open(result_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # 检查数据是否有效
            if 'timestamp' not in data or 'results' not in data:
                print(f"警告: {result_file} 中的数据格式无效")
                return None
                
            # 检查数据是否过期（可选，例如超过7天）
            # timestamp = datetime.strptime(data['timestamp'], "%Y-%m-%d %H:%M:%S")
            # days_old = (datetime.now() - timestamp).days
            # if days_old > 7:  # 如果结果超过7天
            #     print(f"警告: {result_file} 中的分析结果已过期 ({days_old} 天前)")
            #     return None
                
            print(f"从 {result_file} 加载了已存在的分析结果（{data['timestamp']}）")
            return data['results']
        except Exception as e:
            print(f"读取 {result_file} 时出错: {str(e)}")
            return None

    def analyze_all(self) -> Dict[str, List[Dict[str, Any]]]:
        """分析所有支持的语言的源码并获取Git仓库信息"""
        # 初始化结果字典，支持所有语言
        self.results = {
            'python': [],
            'typescript': [],
            'rust': [],
            'go': [],
            'java': [],
            'c': [],
            'cpp': [],
            'csharp': [],
            'ruby': [],
            'php': [],
            'swift': [],
            'kotlin': []
        }
        
        # 用于跟踪已有分析结果的服务器
        servers_with_cached_results = set()
        
        print(f"\n{'='*50}")
        if self.max_servers:
            print(f"开始分析 (限制为 {self.max_servers} 个服务器)...")
        else:
            print(f"开始分析所有服务器...")
        print(f"{'='*50}")
        
        # 确保使用绝对路径
        base_dir = os.path.abspath(self.base_dir)
        
        # 初始化映射关系
        self.server_to_repo_mapping = {}  # 服务器名称到仓库的映射
        self.repo_stars = {}  # 仓库名称 -> 星星数
        self.repo_categories = defaultdict(list)  # 仓库名称 -> 类别列表
        
        # 从JSON或Excel加载仓库数据
        json_data = []  # 存储处理后的JSON数据
        excel_data = []  # 存储处理后的Excel数据，包含所有必要信息
        
        if self.json_path and os.path.exists(self.json_path):
            try:
                with open(self.json_path, 'r', encoding='utf-8') as f:
                    servers_data = json.load(f)
                
                print(f"\n从JSON加载仓库数据: {self.json_path}")
                print(f"JSON数据服务器数量: {len(servers_data)}")
                
                # 处理JSON数据
                for server_info in servers_data:
                    github_url = server_info.get('github_url', '')
                    server_name = server_info.get('name', '')
                    categories = server_info.get('categories', [])
                    metadata_categories = server_info.get('metadata', {}).get('categories', [])
                    
                    # 确保GitHub URL是有效的
                    if not github_url or not isinstance(github_url, str):
                        continue
                    
                    # 如果没有服务器名称，尝试从URL提取
                    if not server_name:
                        if 'github.com' in github_url:
                            url_parts = github_url.split('/')
                            if len(url_parts) >= 2:
                                server_name = url_parts[-1]
                                if server_name.endswith('.git'):
                                    server_name = server_name[:-4]
                        else:
                            continue
                    
                    # 添加到处理后的JSON数据
                    json_data.append({
                        'github_url': github_url,  # 保持原始URL格式
                        'normalized_url': self.normalize_github_url(github_url),  # 标准化后的URL
                        'server_name': server_name,
                        'categories': categories,
                        'metadata_categories': metadata_categories
                    })
                
                print(f"从JSON处理了 {len(json_data)} 条有效记录")
                
            except Exception as e:
                print(f"从JSON加载数据时出错: {str(e)}")
                traceback.print_exc()
        elif self.excel_path and os.path.exists(self.excel_path):
            try:
                df = pd.read_excel(self.excel_path)
                print(f"\n从Excel加载仓库数据: {self.excel_path}")
                print(f"Excel数据行数: {len(df)}")
                
                # 处理Excel数据
                for _, row in df.iterrows():
                    github_url = row.get('github_url-href', '')
                    star_count = row.get('github_star_num', 0)
                    category = row.get('url', '')
                    server_url = row.get('web-scraper-start-url', '')
                    
                    # 确保GitHub URL是有效的
                    if not github_url or not isinstance(github_url, str):
                        continue
                    
                    # 处理星星数
                    try:
                        star_count = int(star_count)
                    except (ValueError, TypeError):
                        if isinstance(star_count, str) and star_count.strip():
                            try:
                                # 处理可能带逗号的数字
                                star_count = int(star_count.replace(',', ''))
                            except:
                                star_count = 0
                        else:
                            star_count = 0
                    
                    # 添加到处理后的Excel数据
                    excel_data.append({
                        'github_url': github_url,  # 保持原始URL格式
                        'normalized_url': self.normalize_github_url(github_url),  # 标准化后的URL
                        'stars': star_count,
                        'category': category,
                        'server_url': server_url
                    })
                
                print(f"从Excel处理了 {len(excel_data)} 条有效记录")
                
            except Exception as e:
                print(f"从Excel加载数据时出错: {str(e)}")
                traceback.print_exc()
        
        # 遍历服务器目录，直接通过文件夹名称匹配
        try:
            # 第一次遍历：获取服务器目录并匹配元数据
            print("\n从服务器目录获取并匹配仓库信息...")
            
            # 创建服务器路径映射
            server_paths = {}
            
            # 遍历目录结构
            for language_dir in os.listdir(base_dir):
                language_path = os.path.join(base_dir, language_dir)
                if not os.path.isdir(language_path) or language_dir in self.excluded_dirs:
                    continue
                
                for server_name in os.listdir(language_path):
                    server_path = os.path.join(language_path, server_name)
                    if not os.path.isdir(server_path) or server_name in self.excluded_dirs:
                        continue
                    
                    # 检查是否达到服务器数量限制
                    if self.max_servers and len(self.analyzed_servers) >= self.max_servers:
                        print(f"\n已达到最大分析服务器数量 ({self.max_servers})")
                        break
                    
                    # 添加到已分析服务器列表
                    self.analyzed_servers.add(server_name)
                    
                    # 添加到服务器路径映射
                    server_paths[server_name] = server_path
                    
                    # 尝试匹配元数据
                    match_found = False
                    
                    # 先尝试在JSON数据中匹配
                    if json_data:
                        for item in json_data:
                            # 从文件夹名提取用户和仓库名
                            # 格式通常为 user_repo 或 user_repo_counter
                            user_repo_parts = server_name.split('_')
                            if len(user_repo_parts) >= 2:
                                # 处理可能的计数器后缀
                                if user_repo_parts[-1].isdigit():
                                    user_repo = '_'.join(user_repo_parts[:-1])
                                else:
                                    user_repo = server_name
                                
                                # 匹配条件：文件夹名（去掉计数器）与仓库名匹配，或URL中的仓库部分匹配
                                repo_in_url = item['normalized_url'].replace('/', '_') if item['normalized_url'] else ''
                                if user_repo == item['server_name'] or user_repo == repo_in_url:
                                    # 从原始URL提取仓库名称 (owner/repo)
                                    if 'github.com' in item['github_url']:
                                        repo_name = item['github_url'].split('github.com/')[1]
                                        if repo_name.endswith('.git'):
                                            repo_name = repo_name[:-4]
                                        repo_name = repo_name.rstrip('/')
                                    else:
                                        # 如果没有有效的GitHub URL，使用文件夹名作为仓库名
                                        repo_name = user_repo
                                    
                                    self.server_to_repo_mapping[server_name] = repo_name
                                    
                                    # 合并所有类别
                                    all_categories = []
                                    if isinstance(item['categories'], list):
                                        all_categories.extend(item['categories'])
                                    if isinstance(item['metadata_categories'], list):
                                        all_categories.extend(item['metadata_categories'])
                                    
                                    for category in all_categories:
                                        if category and isinstance(category, str):
                                            self.repo_categories[repo_name].append(category)
                                    
                                    # 如果没有类别信息，设置为Unknown
                                    if not all_categories:
                                        self.repo_categories[repo_name].append('Unknown')
                                    
                                    match_found = True
                                    print(f"  成功匹配! {server_name} -> {repo_name}")
                                    break
                    
                    # 如果JSON匹配失败，尝试Excel数据
                    if not match_found and excel_data:
                        for item in excel_data:
                            # 从文件夹名提取用户和仓库名
                            user_repo_parts = server_name.split('_')
                            if len(user_repo_parts) >= 2:
                                # 处理可能的计数器后缀
                                if user_repo_parts[-1].isdigit():
                                    user_repo = '_'.join(user_repo_parts[:-1])
                                else:
                                    user_repo = server_name
                                
                                # 匹配条件：文件夹名（去掉计数器）与URL中的仓库部分匹配
                                repo_in_url = item['normalized_url'].replace('/', '_') if item['normalized_url'] else ''
                                if user_repo == repo_in_url:
                                    # 从原始URL提取仓库名称 (owner/repo)
                                    if 'github.com/' in item['github_url']:
                                        repo_name = item['github_url'].split('github.com/')[1]
                                        if repo_name.endswith('.git'):
                                            repo_name = repo_name[:-4]
                                        repo_name = repo_name.rstrip('/')
                                    else:
                                        # 如果没有有效的GitHub URL，使用文件夹名作为仓库名
                                        repo_name = user_repo
                                    
                                    self.server_to_repo_mapping[server_name] = repo_name
                                    self.repo_stars[repo_name] = item['stars']
                                    self.repo_categories[repo_name].append(item['category'])
                                    match_found = True
                                    print(f"  成功匹配! {server_name} -> {repo_name} (星星: {item['stars']})")
                                    break
                    
                    if not match_found:
                        # 如果没有匹配到元数据，使用文件夹名作为仓库名
                        user_repo_parts = server_name.split('_')
                        if len(user_repo_parts) >= 2:
                            # 处理可能的计数器后缀
                            if user_repo_parts[-1].isdigit():
                                repo_name = '_'.join(user_repo_parts[:-1])
                            else:
                                repo_name = server_name
                            
                            self.server_to_repo_mapping[server_name] = repo_name
                            self.repo_categories[repo_name].append('Unknown')
                            print(f"  未找到匹配元数据，使用文件夹名作为仓库名: {server_name} -> {repo_name}")
            
            # 输出匹配结果
            print(f"\n成功匹配了 {len(self.server_to_repo_mapping)}/{len(self.analyzed_servers)} 个服务器")
            
            # 打印星星数分布信息
            star_ranges = [
                (0, 10),
                (11, 100),
                (101, 500),
                (501, 1000),
                (1001, 10000),
                (10001, 50000),
                (50001, float('inf'))
            ]
            
            range_counts = [0] * len(star_ranges)
            for _, stars in self.repo_stars.items():
                for i, (min_val, max_val) in enumerate(star_ranges):
                    if min_val <= stars <= max_val:
                        range_counts[i] += 1
                        break
            
            print("\n仓库星星数范围分布:")
            for i, (min_val, max_val) in enumerate(star_ranges):
                range_label = f"{min_val}-{max_val if max_val != float('inf') else '+'}"
                print(f"  {range_label}: {range_counts[i]} 个仓库")
            
            # 每个服务器的分析结果 {服务器名称 -> {语言 -> 问题列表}}
            server_results = {}
            
            # 第二次遍历：进行代码分析
            for root, dirs, files in os.walk(base_dir):
                # 从遍历列表中移除需要排除的目录
                dirs[:] = [d for d in dirs if d not in self.excluded_dirs]
                
                for file in files:
                    try:
                        file_path = os.path.join(root, file)
                        file_path = os.path.normpath(file_path)  # 标准化路径
                        
                        # 检查文件是否在排除目录中
                        if any(excluded in file_path.split(os.sep) for excluded in self.excluded_dirs):
                            continue
                            
                        # 获取服务器名称 - 基于目录结构解析
                        path_parts = file_path.split(os.sep)
                        
                        # 查找服务器名称（假设目录结构是 base_dir/language/server_name/...）
                        # 找到语言目录的索引
                        try:
                            # 查找base_dir在路径中的位置
                            base_dir_parts = base_dir.split(os.sep)
                            base_index = 0
                            for i, part in enumerate(path_parts):
                                if i < len(base_dir_parts) and part == base_dir_parts[i]:
                                    base_index = i
                                else:
                                    break
                            
                            # 确保路径结构足够深
                            if len(path_parts) > base_index + 2:
                                server_name = path_parts[base_index + 2]  # 服务器名称
                                # 如果服务器不在已分析列表中，则跳过
                                if server_name not in self.analyzed_servers:
                                    continue
                                # 如果服务器已有缓存结果，则跳过
                                if server_name in servers_with_cached_results:
                                    continue
                        except (ValueError, IndexError):
                            # 如果无法解析路径，跳过该文件
                            continue
                            
                        language = self.get_language_by_extension(file_path)
                        
                        # 只处理支持的语言
                        if language in self.results:
                            print(f"\n分析 {language} 文件: {file_path}")
                            # 分析单个文件并将结果添加到对应语言的列表中
                            file_results = self.analyze_file(file_path, language)
                            if file_results:
                                print(f"发现 {len(file_results)} 个潜在问题")
                                self.results[language].extend(file_results)
                                
                                # 添加到服务器特定结果
                                if server_name not in server_results:
                                    server_results[server_name] = {lang: [] for lang in self.results}
                                server_results[server_name][language].extend(file_results)
                                
                    except Exception as e:
                        print(f"分析文件时出错: {str(e)}")
                        continue
            
            # 保存每个服务器的分析结果
            print("\n保存分析结果...")
            for server_name, results in server_results.items():
                print(f"  保存服务器 {server_name} 的分析结果")
                
        except Exception as e:
            print(f"遍历目录结构时出错: {str(e)}")
            traceback.print_exc()
        
        # 打印分析结果统计
        print(f"\n{'='*50}")
        print(f"分析摘要:")
        print(f"{'='*50}")
        print(f"已分析的服务器 ({len(self.analyzed_servers)}):")
        
        for server in sorted(self.analyzed_servers):
            repo = self.server_to_repo_mapping.get(server, "未知")
            stars = self.repo_stars.get(repo, "未知")
            print(f"  - {server} -> {repo} (星星数: {stars})")
        
        print(f"\n各语言的问题统计:")
        total_issues = 0
        for language in self.results:
            issue_count = len(self.results[language])
            total_issues += issue_count
            if issue_count > 0:
                print(f"{language}: 发现 {issue_count} 个问题")
        print(f"\n问题总数: {total_issues}")
            
        return self.results

    def normalize_github_url(self, url):
        """标准化GitHub URL以便进行一致比较"""
        if not url or not isinstance(url, str):
            return ""
            
        # 移除协议前缀
        if '://' in url:
            url = url.split('://', 1)[1]
        
        # 移除www.前缀
        if url.lower().startswith('www.'):
            url = url[4:]
        
        # 确保以github.com开头
        if not url.lower().startswith('github.com'):
            return ""
        
        # 获取仓库路径部分
        parts = url.split('/', 1)
        if len(parts) < 2:
            return ""
            
        repo_path = parts[1]
        
        # 移除.git后缀和尾部斜杠
        if repo_path.endswith('.git'):
            repo_path = repo_path[:-4]
        repo_path = repo_path.rstrip('/')
        
        # 返回标准化的路径 (转为小写)
        return repo_path.lower()

    
    def normalize_github_url(self, url):
        """标准化GitHub URL以便进行一致比较"""
        if not url or not isinstance(url, str):
            return ""
            
        # 移除协议前缀
        if '://' in url:
            url = url.split('://', 1)[1]
        
        # 移除www.前缀
        if url.lower().startswith('www.'):
            url = url[4:]
        
        # 确保以github.com开头
        if not url.lower().startswith('github.com'):
            return ""
        
        # 获取仓库路径部分
        parts = url.split('/', 1)
        if len(parts) < 2:
            return ""
        
        repo_path = parts[1]
        
        # 移除.git后缀和尾部斜杠
        if repo_path.endswith('.git'):
            repo_path = repo_path[:-4]
        repo_path = repo_path.rstrip('/')
        
        # 返回标准化的路径 (转为小写)
        return repo_path.lower()

    def save_results(self, output_dir: str = './output', generate_security_table: bool = True):
        """
        将分析结果保存为JSON格式，并可选地生成安全统计表
        """
        # 确保输出目录存在
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # 初始化最终的结果字典，按服务器归类
        final_results = {}
        
        # 处理每种语言的分析结果
        for language, findings in self.results.items():
            # 只处理有结果的语言
            if not findings:
                continue
                
            # 处理该语言下的每个发现
            for finding in findings:
                # 标准化路径，确保使用正确的路径分隔符
                file_path = finding.get('file', '')
                normalized_path = os.path.normpath(file_path)
                
                # 从路径中提取服务器名称
                path_parts = normalized_path.replace('\\', '/').split('/')
                server_name = None
                
                # 查找服务器名称（假设目录结构是 base_dir/language/server_name/...）
                # 找到base_dir在路径中的位置
                base_dir = os.path.abspath(self.base_dir)
                base_dir_parts = base_dir.replace('\\', '/').split('/')
                base_index = -1
                
                # 查找base_dir在路径中的位置
                for i in range(len(path_parts) - len(base_dir_parts) + 1):
                    if path_parts[i:i+len(base_dir_parts)] == base_dir_parts:
                        base_index = i + len(base_dir_parts) - 1
                        break
                
                if base_index != -1 and base_index + 2 < len(path_parts):
                    server_language = path_parts[base_index + 1]
                    server_name = path_parts[base_index + 2]
                    
                    # 初始化服务器结果
                    if server_name not in final_results:
                        final_results[server_name] = {
                            "language": server_language,
                            "api_calls": [],
                            "threat_types": {},
                            "resource_types": {}  # 新增资源类型统计
                        }
                    
                # 获取API名称和威胁类型
                api_name = finding.get('api_name', '')
                
                # 获取API威胁类型和资源类型
                lang_checker = self.get_language_api_checker(language)
                if lang_checker and api_name:
                    threat_type = lang_checker.get_api_threat_type(api_name)
                    resource_type = lang_checker._dangerous_apis.get(api_name, {}).get('resource_type', 'UNKNOWN')
                else:
                    threat_type = finding.get('threat_type', 'UNKNOWN')
                    resource_type = finding.get('resource_type', 'UNKNOWN')
                
                if server_name:
                    # 构建完整的API调用信息
                    api_call_info = {
                        "path": normalized_path,
                        "line": finding.get('line', 0),
                        "column": finding.get('column', 0),
                        "api_call": api_name,
                        "function": finding.get('function', ''),
                        "description": finding.get('description', ''),
                        "threat_type": threat_type,
                        "resource_type": resource_type  # 新增资源类型字段
                    }
                    
                    # 添加到API调用列表
                    final_results[server_name]["api_calls"].append(api_call_info)
                    
                    # 更新威胁类型统计
                    if threat_type not in final_results[server_name]["threat_types"]:
                        final_results[server_name]["threat_types"][threat_type] = 0
                    final_results[server_name]["threat_types"][threat_type] += 1
                    
                    # 更新资源类型统计
                    if resource_type not in final_results[server_name]["resource_types"]:
                        final_results[server_name]["resource_types"][resource_type] = 0
                    final_results[server_name]["resource_types"][resource_type] += 1
        
        # 生成带时间戳的输出文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f'analysis_result_{timestamp}.json')
        
        # 写入JSON文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_results, f, ensure_ascii=False, indent=2)
        
        print(f"分析结果已保存到: {output_file}")
        
        # 打印威胁统计摘要
        print("\n分析结果摘要:")
        for server, data in final_results.items():
            print(f"\n服务器: {server} ({data['language']})")
            
            # 尝试找到对应的仓库
            repo_name = self.server_to_repo_mapping.get(server, "Unknown")
            if repo_name != "Unknown" and repo_name in self.repo_stars:
                print(f"对应仓库: {repo_name} (星星数: {self.repo_stars[repo_name]})")
                
            # 显示类别信息
            if repo_name in self.repo_categories:
                categories = self.repo_categories[repo_name]
                print(f"类别: {', '.join(categories)}")
                
            print("威胁类型统计:")
            for threat_type, count in data["threat_types"].items():
                print(f"  - {threat_type}: {count}个API调用")
                
            print("资源类型统计:")
            for resource_type, count in data["resource_types"].items():
                print(f"  - {resource_type}: {count}个API调用")
        
        # 如果需要，生成安全统计表
        if generate_security_table:
            table_file = self.generate_security_table(final_results, output_dir, timestamp)
            print(f"\n安全统计表已保存到: {table_file}")
        
        return output_file

    def get_language_api_checker(self, language: str):
        """
        根据语言获取对应的API检查器
        """
        from dangerous_apis import (
            PythonAPIChecker, TypeScriptAPIChecker, JavaAPIChecker, 
            CppAPIChecker, RustAPIChecker, GoAPIChecker, 
            CSharpAPIChecker, PHPAPIChecker, RubyAPIChecker,
            SwiftAPIChecker, KotlinAPIChecker
        )
        
        language = language.lower()
        if language == 'python':
            return PythonAPIChecker()
        elif language in ('javascript', 'typescript', 'js', 'ts'):
            return TypeScriptAPIChecker()
        elif language == 'java':
            return JavaAPIChecker()
        elif language in ('c', 'cpp', 'c++'):
            return CppAPIChecker()
        elif language == 'rust':
            return RustAPIChecker()
        elif language == 'go':
            return GoAPIChecker()
        elif language in ('csharp', 'c#'):
            return CSharpAPIChecker()
        elif language == 'php':
            return PHPAPIChecker()
        elif language == 'ruby':
            return RubyAPIChecker()
        elif language == 'swift':
            return SwiftAPIChecker()
        elif language == 'kotlin':
            return KotlinAPIChecker()
        else:
            return None

    def load_json_data(self):
        """加载merged_servers.json文件中的仓库数据"""
        if not self.json_path or not os.path.exists(self.json_path):
            print(f"JSON文件不存在或未指定: {self.json_path}")
            return False
            
        try:
            print(f"\n加载JSON数据: {self.json_path}")
            with open(self.json_path, 'r', encoding='utf-8') as f:
                servers_data = json.load(f)
                
            # 处理数据创建仓库映射
            for server_info in servers_data:
                # 获取GitHub仓库URL
                repo_url = server_info.get('github_url', '')
                if not repo_url or not isinstance(repo_url, str):
                    continue
                      
                # 获取服务器名称
                server_name = server_info.get('name', '')
                if not server_name:
                    # 尝试从URL提取服务器名称
                    if 'github.com' in repo_url:
                        url_parts = repo_url.split('/')
                        if len(url_parts) >= 2:
                            server_name = url_parts[-1]
                            if server_name.endswith('.git'):
                                server_name = server_name[:-4]
                    else:
                        continue
                      
                # 从URL提取仓库名称 (格式: https://github.com/owner/repo)
                if 'github.com' in repo_url:
                    repo_name = repo_url.replace('https://github.com/', '')
                    if repo_name.endswith('.git'):
                        repo_name = repo_name[:-4]
                    repo_name = repo_name.rstrip('/')
                    
                    # 将仓库名与服务器名关联起来
                    self.repo_to_server_mapping[repo_name] = server_name
                    self.server_to_repo_mapping[server_name] = repo_name
                    
                    # 处理类别信息
                    categories = server_info.get('categories', [])
                    metadata_categories = server_info.get('metadata', {}).get('categories', [])
                    
                    # 合并所有类别
                    all_categories = []
                    if isinstance(categories, list):
                        all_categories.extend(categories)
                    if isinstance(metadata_categories, list):
                        all_categories.extend(metadata_categories)
                    
                    # 添加到仓库类别列表
                    for category in all_categories:
                        if category and isinstance(category, str):
                            self.repo_categories[repo_name].append(category)
                    
                    # 如果没有类别信息，设置为Unknown
                    if not all_categories:
                        self.repo_categories[repo_name].append('Unknown')
                    
                    print(f"仓库 {repo_name} 添加到映射，服务器名称: {server_name}")
            
            print(f"成功从JSON加载 {len(self.repo_categories)} 个仓库的信息")
            return True
        except Exception as e:
            print(f"加载JSON数据时出错: {str(e)}")
            traceback.print_exc()
            return False
            
    def load_excel_data(self):
        """加载Excel文件中的仓库数据"""
        if not self.excel_path or not os.path.exists(self.excel_path):
            print(f"Excel文件不存在或未指定: {self.excel_path}")
            return False
            
        try:
            print(f"\n加载Excel数据: {self.excel_path}")
            df = pd.read_excel(self.excel_path)
            
            # 确保必要的列存在
            required_columns = ['github_url-href', 'url']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                print(f"Excel文件缺少必要的列: {missing_columns}")
                return False
            
            # 处理数据框创建仓库->类别映射
            for _, row in df.iterrows():
                # 获取GitHub仓库URL
                repo_url = row.get('github_url-href', '')
                if not repo_url or not isinstance(repo_url, str):
                    continue
                    
                # 获取该仓库的类别(从url列)
                category = row.get('url', '')
                if not category or not isinstance(category, str):
                    continue
                    
                # 从URL提取仓库名称 (格式: https://github.com/owner/repo)
                if 'github.com' in repo_url:
                    repo_name = repo_url.replace('https://github.com/', '')
                    
                    # 从仓库URL中提取服务器名称（通常是仓库名部分）
                    repo_parts = repo_name.split('/')
                    if len(repo_parts) >= 2:
                        owner, repo = repo_parts[0], repo_parts[1]
                        server_name = repo
                        
                        # 将仓库名与服务器名关联起来
                        self.repo_to_server_mapping[repo_name] = server_name
                        self.server_to_repo_mapping[server_name] = repo_name
                    
                    # 将类别添加到仓库的类别列表中
                    # 重要：一个仓库可能有多个类别，所以使用列表存储
                    self.repo_categories[repo_name].append(category)
                    print(f"仓库 {repo_name} 添加类别: {category}")
            
            # 输出一些统计信息以便于调试
            for repo_name, categories in self.repo_categories.items():
                print(f"仓库 {repo_name} 的所有类别: {categories}")
                
            print(f"成功加载 {len(self.repo_categories)} 个仓库的类别信息")
            return True
        except Exception as e:
            print(f"加载Excel数据时出错: {str(e)}")
            traceback.print_exc()
            return False
    
    def fetch_github_stars(self, env_path=None):
        """从GitHub API获取Excel表中未填写星星数量的仓库数据，避免重复请求，并逐个保存结果"""
        print("\n从GitHub API获取未填写的仓库星星数量...")
        
        # 尝试从.env文件加载token
        token = None
        try:
            from dotenv import load_dotenv
            import os
            
            # 加载指定的.env文件或默认.env
            if env_path and os.path.exists(env_path):
                load_dotenv(env_path)
                print(f"从 {env_path} 加载环境变量")
            else:
                load_dotenv()
                print(f"从默认位置加载环境变量")
            
            # 获取GitHub token
            token = os.getenv('GITHUB_TOKEN')
            if token:
                print("成功从.env文件加载GitHub token")
            else:
                print("警告: 未在.env文件中找到GITHUB_TOKEN")
        except ImportError:
            print("警告: 未安装python-dotenv包，无法从.env文件加载token")
        except Exception as e:
            print(f"加载.env文件时出错: {str(e)}")
        
        # 重新加载Excel数据，获取星星数量信息
        if not self.excel_path or not os.path.exists(self.excel_path):
            print(f"Excel文件不存在或未指定: {self.excel_path}")
            return
        
        try:
            # 读取Excel文件
            df = pd.read_excel(self.excel_path)
            
            # 确保必要的列存在
            if 'github_url-href' not in df.columns:
                print("Excel文件中缺少 'github_url-href' 列")
                return
                    
            # 检查是否有github_star_num列
            has_star_column = 'github_star_num' in df.columns
            if not has_star_column:
                # 如果没有星星数列，创建一个
                df['github_star_num'] = None
                has_star_column = True
                print("在Excel中创建新列 'github_star_num'")
                
            # 创建一个仓库URL到所有行索引的映射
            repo_to_row_indices = {}
            # 记录哪些仓库需要获取星星数
            repos_to_fetch = set()
            
            # 第一次遍历收集所有需要获取星星数的仓库和它们对应的行索引
            for idx, row in df.iterrows():
                repo_url = row.get('github_url-href', '')
                if not repo_url or not isinstance(repo_url, str) or 'github.com' not in repo_url:
                    continue
                    
                # 提取仓库名称
                repo_name = repo_url.replace('https://github.com/', '')
                
                # 检查是否需要获取星星数
                need_to_fetch = False
                if has_star_column:
                    star_value = row.get('github_star_num')
                    # 只有当值为NaN或空字符串时才认为是未填写
                    if pd.isna(star_value) or star_value == '':
                        need_to_fetch = True
                else:
                    # 如果没有星星数列，则所有仓库都需要获取
                    need_to_fetch = True
                
                # 保存每个仓库对应的所有行索引
                if repo_name not in repo_to_row_indices:
                    repo_to_row_indices[repo_name] = []
                repo_to_row_indices[repo_name].append(idx)
                
                # 如果需要获取星星数，加入待获取列表
                if need_to_fetch:
                    repos_to_fetch.add(repo_name)
            
            print(f"找到 {len(repos_to_fetch)} 个需要获取星星数的唯一仓库")
            
            # 获取星星数并逐个保存
            repos_fetched = 0
            for repo_name in repos_to_fetch:
                try:
                    # 如果已经获取过这个仓库的星星数，则跳过
                    if repo_name in self.repo_stars:
                        print(f"仓库 {repo_name} 的星星数已经获取过，使用缓存值: {self.repo_stars[repo_name]}")
                        continue
                    
                    # GitHub API请求获取仓库信息
                    api_url = f"https://api.github.com/repos/{repo_name}"
                    
                    # 设置请求头
                    headers = {'User-Agent': 'MCP-Code-Analyzer'}
                    if token:
                        headers['Authorization'] = f'token {token}'
                    
                    print(f"请求 {api_url}")
                    response = requests.get(api_url, headers=headers)
                    
                    star_count = 0
                    if response.status_code == 200:
                        repo_data = response.json()
                        star_count = repo_data.get('stargazers_count', 0)
                        self.repo_stars[repo_name] = star_count
                        print(f"仓库 {repo_name} 有 {star_count} 颗星")
                        
                        # 更新Excel中对应的所有行
                        rows_updated = 0
                        if repo_name in repo_to_row_indices:
                            for idx in repo_to_row_indices[repo_name]:
                                star_value = df.loc[idx, 'github_star_num']
                                if pd.isna(star_value) or star_value == '':
                                    df.loc[idx, 'github_star_num'] = star_count
                                    rows_updated += 1
                        
                        # 每获取一个仓库就立即保存Excel文件
                        if rows_updated > 0:
                            print(f"更新Excel文件中的星星数量数据，更新了 {rows_updated} 行")
                            
                            # 尝试保存文件，如果失败则重试几次
                            max_retries = 3
                            for retry in range(max_retries):
                                try:
                                    df.to_excel(self.excel_path, index=False)
                                    print(f"成功保存Excel文件")
                                    break
                                except Exception as save_error:
                                    print(f"保存Excel失败，尝试第 {retry+1}/{max_retries} 次: {str(save_error)}")
                                    if retry == max_retries - 1:
                                        print("达到最大重试次数，无法保存Excel文件")
                        
                        repos_fetched += 1
                    else:
                        print(f"获取 {repo_name} 的星星数量失败: HTTP {response.status_code}")
                        print(f"响应内容: {response.text[:100]}...")
                        self.repo_stars[repo_name] = 0
                        
                    # 添加延迟以避免触发GitHub API速率限制
                    import time
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"获取 {repo_name} 的星星数量时出错: {str(e)}")
                    self.repo_stars[repo_name] = 0
            
            print(f"成功获取并处理 {repos_fetched} 个唯一仓库的星星数量")
            
        except Exception as e:
            print(f"处理Excel文件时发生错误: {str(e)}")
            traceback.print_exc()
        
        return self.repo_stars


    def get_repo_from_git_config(self, server_dir):
        """从服务器目录的.git/config文件中获取GitHub仓库URL"""
        config_path = os.path.join(server_dir, '.git', 'config')
        if not os.path.exists(config_path):
            return None
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_content = f.read()
            
            # 尝试从配置中提取GitHub仓库URL
            import re
            # 匹配GitHub URL格式
            patterns = [
                r'url\s*=\s*https://github\.com/([^/\s]+/[^/\s.]+)(?:\.git)?',  # HTTPS格式
                r'url\s*=\s*git@github\.com:([^/\s]+/[^/\s.]+)(?:\.git)?'       # SSH格式
            ]
            
            for pattern in patterns:
                match = re.search(pattern, config_content)
                if match:
                    return match.group(1)  # 返回owner/repo格式
        
        except Exception as e:
            print(f"读取Git配置文件时出错: {str(e)}")
        
        return None


    def analyze_all_with_categories(self):
        """分析所有支持的语言的源码并按照类别进行统计"""
        print("\n开始完整分析流程...")
        
        # 首先加载数据
        if self.json_path:
            if not self.load_json_data():
                print("加载JSON数据失败，无法进行类别分析")
                return
        elif self.excel_path:
            if not self.load_excel_data():
                print("加载Excel数据失败，无法进行类别分析")
                return
        else:
            print("未指定JSON或Excel文件路径，无法进行类别分析")
            return
        
        # 获取GitHub仓库的星星数
        if self.excel_path:
            self.fetch_github_stars()
        
        # 运行正常的代码分析
        self.analyze_all()
        
        # 保存结果并生成安全统计表
        return self.save_results(generate_security_table=True)


    def generate_security_table(self, results, output_dir, timestamp):
        """生成安全统计表并保存到文件"""
        print("\n生成安全统计表...")
        print(f"当前日期和时间 (UTC): {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"当前用户登录: {getattr(self, 'user_login', '1528344561')}")
        
        # 初始化用于存储统计数据的结构
        category_stats = defaultdict(lambda: {
            # 'secure': 0,
            'total': 0,
            'resource_types': defaultdict(int),
            'server_count': 0
        })
        
        # 按下载范围(星星数)的统计
        star_range_stats = defaultdict(lambda: {
            # 'secure': 0,
            'total': 0,
            'resource_types': defaultdict(int),
            'server_count': 0
        })
        
        # 定义星星数范围
        star_ranges = [
            (0, 10),
            (11, 100),
            (101, 1000),
            (1001, 10000),
            (10001, 50000),
            (50001, float('inf'))
        ]
        
        # 定义以便在表格中显示的范围标签
        star_range_labels = [
            '0-10',
            '11-100',
            '101-1000',
            '1001-10000',
            '10001-50000',
            '50000+'
        ]
        
        # 获取所有唯一的资源类型
        all_resource_types = set()
        
        # 预处理: 找出所有的资源类型
        for server_name, server_data in results.items():
            for resource_type in server_data.get("resource_types", {}):
                all_resource_types.add(resource_type)
        
        # 处理每个服务器的结果
        skipped_servers = 0
        for server_name, server_data in results.items():
            # 查找对应的仓库
            repo_name = self.server_to_repo_mapping.get(server_name)
            if not repo_name:
                print(f"警告: 服务器 '{server_name}' 没有找到对应的仓库，跳过")
                skipped_servers += 1
                continue
                
            # 检查仓库是否在Excel中有星星数记录
            if repo_name not in self.repo_stars:
                print(f"仓库 '{repo_name}' 不在Excel中，跳过")
                skipped_servers += 1
                continue
                
            # 获取仓库的星星数量
            star_count = self.repo_stars[repo_name]
            
            # 找到适合的星星数范围
            star_range_idx = 0
            for i, (min_stars, max_stars) in enumerate(star_ranges):
                if min_stars <= star_count <= max_stars:
                    star_range_idx = i
                    break
            
            star_range = star_range_labels[star_range_idx]
            print(f"服务器 {server_name} -> 仓库 {repo_name} -> 星星数 {star_count} -> 范围 {star_range}")
            
            # 获取服务器的类别（如果有的话）
            categories = self.repo_categories.get(repo_name, ["未分类"])
            
            # 检查这个服务器是否有危险的API调用
            api_calls = server_data.get("api_calls", [])
            has_insecure_calls = len(api_calls) > 0
            
            # 更新每个类别的统计信息
            for category in categories:
                category_stats[category]['total'] += 1
                category_stats[category]['server_count'] += 1
                
                # if not has_insecure_calls:
                #     category_stats[category]['secure'] += 1
                
                # 统计每种资源类型的数量（不管是否安全）
                for resource_type, count in server_data.get("resource_types", {}).items():
                    category_stats[category]['resource_types'][resource_type] += 1
            
            # 更新星星数范围的统计信息
            star_range_stats[star_range]['total'] += 1
            star_range_stats[star_range]['server_count'] += 1
            
            # if not has_insecure_calls:
            #     star_range_stats[star_range]['secure'] += 1
            
            # 统计每种资源类型的数量
            for resource_type, count in server_data.get("resource_types", {}).items():
                star_range_stats[star_range]['resource_types'][resource_type] += 1
        
        print(f"\n跳过了 {skipped_servers} 个没有在Excel中找到星星数的服务器")
        
        # 打印星星范围统计的结果
        print("\n星星范围统计结果:")
        for range_label, stats in star_range_stats.items():
            if stats['server_count'] > 0:
                print(f"- 范围 {range_label}: {stats['server_count']} 个服务器")
        
        # 计算百分比并生成表格
        # 首先按资源类型排序
        sorted_resource_types = sorted(all_resource_types)
        
        # 创建表头
        resource_headers = " | ".join([f"{rt}" for rt in sorted_resource_types])
        # table = f"| Dimension | Secure | Total | {resource_headers} |\n"
        table = f"| Dimension | Total | {resource_headers} |\n"

        table += f"|-----------|--------|-------|{'-|' * len(sorted_resource_types)}\n"
        
        # 添加类别部分
        table += "| **Category** |\n"
        for category, stats in sorted(category_stats.items()):
            if stats['server_count'] == 0:
                continue
                
            # secure_count = stats['secure']
            total_count = stats['server_count']
            # row = f"| {category} | {secure_count} | {total_count} |"
            row = f"| {category} | {total_count} |"
            
            # 添加每种资源类型的具体数量
            for resource_type in sorted_resource_types:
                count = stats['resource_types'].get(resource_type, 0)
                row += f" {count} |"
                
            table += row + "\n"
        
        # 添加下载范围(星星数)部分
        table += "| **Stars Range** |\n"
        for star_range in star_range_labels:
            stats = star_range_stats[star_range]
            if stats['server_count'] == 0:
                continue
                
            # secure_count = stats['secure']
            total_count = stats['server_count']
            row = f"| {star_range} | {total_count} |"
            
            # 添加每种资源类型的具体数量
            for resource_type in sorted_resource_types:
                count = stats['resource_types'].get(resource_type, 0)
                row += f" {count} |"
                
            table += row + "\n"
        
        # 添加表格底部的时间和用户信息
        footer = f"\n\n生成时间: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} (UTC)\n"
        footer += f"用户: {getattr(self, 'user_login', '1528344561')}"
        
        # 保存表格到文件
        table_file = os.path.join(output_dir, f'security_table_{timestamp}.md')
        with open(table_file, 'w', encoding='utf-8') as f:
            f.write(table)
            f.write(footer)
        
        print(f"安全统计表已保存到: {table_file}")
        return table_file

def main():
    parser = argparse.ArgumentParser(description='分析MCP服务器中的危险API使用')
    parser.add_argument('--max-servers', type=int, help='最多分析的服务器数量 (默认: 不限制)')
    parser.add_argument('--language', type=str, help='仅分析指定语言的文件')
    parser.add_argument('--excel', type=str, help='Excel文件路径，包含仓库的类别信息')
    parser.add_argument('--json', type=str, help='JSON文件路径，包含仓库的类别信息 (merged_servers.json)')
    parser.add_argument('--output-dir', type=str, default='./output', help='输出目录 (默认: ./output)')
    args = parser.parse_args()
    
    # 优先使用JSON文件
    if args.json:
        analyzer = CodeAnalyzer(max_servers=args.max_servers, json_path=args.json)
        # 使用完整的分析流程（包括类别分析）
        analyzer.analyze_all_with_categories()
    else:
        analyzer = CodeAnalyzer(max_servers=args.max_servers, excel_path=args.excel)
        
        if args.excel:
            # 使用完整的分析流程（包括类别分析）
            analyzer.analyze_all_with_categories()
        else:
            # 使用原始分析流程
            if args.language:
                analyzer.scan_directory(args.language)
            else:
                analyzer.analyze_all()
            analyzer.save_results(output_dir=args.output_dir)


if __name__ == "__main__":
    main()