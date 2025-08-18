import os
import json
import csv
import re
import argparse
from collections import defaultdict, Counter
from pathlib import Path
import xml.etree.ElementTree as ET
import tomli  # 用于解析Cargo.toml

class LibraryAnalyzer:
    def __init__(self):
        # 支持的语言和对应的依赖文件模式
        self.LANGUAGE_PATTERNS = {
            'Python': {'file': 'requirements.txt', 'parser': self.parse_python_requirements},
            'JavaScript': {'file': 'package.json', 'parser': self.parse_package_json},
            'Java': {'file': 'pom.xml', 'parser': self.parse_pom_xml},
            'Go': {'file': 'go.mod', 'parser': self.parse_go_mod},
            'Rust': {'file': 'Cargo.toml', 'parser': self.parse_cargo_toml},
            'Ruby': {'file': 'Gemfile', 'parser': self.parse_gemfile}
        }

        # 语言文件扩展名映射
        self.LANGUAGE_EXTENSIONS = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.jsx': 'JavaScript',
            '.ts': 'JavaScript',
            '.tsx': 'JavaScript',
            '.java': 'Java',
            '.go': 'Go',
            '.rs': 'Rust',
            '.rb': 'Ruby'
        }

        # 标准库映射，用于过滤非第三方依赖
        self.STANDARD_LIBRARIES = {
            'Python': set([
                'os', 'sys', 'json', 're', 'collections', 'datetime', 'pathlib',
                'math', 'random', 'time', 'io', 'csv', 'logging', 'argparse',
                'subprocess', 'tempfile', 'shutil', 'hashlib', 'itertools', 'functools',
                'threading', 'multiprocessing', 'socket', 'http', 'urllib', 'email'
            ]),
            'JavaScript': set([
                'fs', 'path', 'http', 'https', 'url', 'os', 'crypto', 'stream',
                'events', 'util', 'buffer', 'querystring', 'child_process'
            ]),
            'Java': set([
                'java.lang', 'java.util', 'java.io', 'java.net', 'java.nio',
                'java.time', 'java.text', 'java.math', 'java.security',
                'java.sql', 'java.awt', 'javax.swing'
            ]),
            'Go': set([
                'fmt', 'strings', 'strconv', 'time', 'encoding/json', 'os',
                'path/filepath', 'sync', 'io', 'net/http', 'reflect', 'errors'
            ]),
            'Rust': set([
                'std', 'core', 'alloc', 'collections', 'time', 'fs', 'io',
                'net', 'path', 'thread', 'sync'
            ]),
            'Ruby': set([
                'Kernel', 'Object', 'Module', 'Class', 'String', 'Array',
                'Hash', 'Integer', 'Float', 'Fixnum', 'Bignum', 'File', 'Dir',
                'IO', 'Time', 'Regexp', 'Exception', 'Enumerable'
            ])
        }

        # 依赖分类映射，用于将依赖映射到更高层次的类别
        self.DEPENDENCY_CATEGORIES = {
            'Web框架': {
                'Python': ['flask', 'django', 'fastapi', 'bottle', 'tornado', 'pyramid'],
                'JavaScript': ['express', 'react', 'vue', 'angular', 'koa', 'nest'],
                'Java': ['spring', 'jakarta', 'quarkus', 'micronaut', 'play'],
                'Go': ['gin', 'echo', 'fiber', 'gorilla', 'beego'],
                'Rust': ['actix', 'rocket', 'warp', 'axum', 'tide'],
                'Ruby': ['rails', 'sinatra', 'rack', 'hanami', 'padrino']
            },
            '数据库': {
                'Python': ['sqlalchemy', 'pymongo', 'django.db', 'psycopg2', 'mysql-connector', 'sqlite3'],
                'JavaScript': ['mongoose', 'sequelize', 'typeorm', 'prisma', 'knex'],
                'Java': ['hibernate', 'mybatis', 'jdbc', 'jpa', 'spring-data'],
                'Go': ['gorm', 'sqlx', 'go-sql-driver/mysql', 'lib/pq'],
                'Rust': ['diesel', 'sqlx', 'tokio-postgres', 'mongodb'],
                'Ruby': ['activerecord', 'mongoid', 'sequel']
            },
            'AI/机器学习': {
                'Python': ['tensorflow', 'pytorch', 'scikit-learn', 'numpy', 'pandas', 'matplotlib', 'keras'],
                'JavaScript': ['tensorflow.js', 'brain.js', 'synaptic', 'ml5.js'],
                'Java': ['dl4j', 'weka', 'h2o', 'deeplearning4j'],
                'Go': ['gorgonia', 'goml'],
                'Rust': ['tract', 'linfa', 'ndarray'],
                'Ruby': ['sciruby', 'nmatrix']
            },
            '测试工具': {
                'Python': ['pytest', 'unittest', 'nose', 'mock', 'coverage'],
                'JavaScript': ['jest', 'mocha', 'chai', 'jasmine', 'cypress'],
                'Java': ['junit', 'testng', 'mockito', 'assertj'],
                'Go': ['testing', 'testify', 'gocheck'],
                'Rust': ['tokio-test', 'assert_cmd', 'proptest'],
                'Ruby': ['rspec', 'minitest', 'cucumber']
            },
            'API工具': {
                'Python': ['requests', 'aiohttp', 'flask-restful', 'fastapi'],
                'JavaScript': ['axios', 'superagent', 'fetch'],
                'Java': ['retrofit', 'okhttp', 'feign'],
                'Go': ['go-json-rest', 'resty', 'grequests'],
                'Rust': ['reqwest', 'hyper'],
                'Ruby': ['faraday', 'httparty', 'rest-client']
            },
            '安全工具': {
                'Python': ['pycryptodome', 'bcrypt', 'cryptography', 'jwt'],
                'JavaScript': ['crypto-js', 'bcryptjs', 'jsonwebtoken'],
                'Java': ['bouncycastle', 'spring-security', 'jbcrypt'],
                'Go': ['crypto', 'bcrypt', 'jwt-go'],
                'Rust': ['ring', 'bcrypt', 'jsonwebtoken'],
                'Ruby': ['bcrypt', 'devise', 'omniauth']
            }
        }

    def detect_language(self, repo_path):
        """检测仓库的主要编程语言"""
        language_counts = defaultdict(int)
        # 通过文件扩展名检测
        for root, _, files in os.walk(repo_path):
            for file in files:
                ext = Path(file).suffix.lower()
                language = self.LANGUAGE_EXTENSIONS.get(ext)
                if language:
                    language_counts[language] += 1
                
                # 也通过依赖文件检测
                if file in [info['file'] for info in self.LANGUAGE_PATTERNS.values()] and root == repo_path:
                    for lang, info in self.LANGUAGE_PATTERNS.items():
                        if file == info['file']:
                            language_counts[lang] += 5  # 依赖文件权重更高
        
        if not language_counts:
            return 'Unknown'
        
        # 返回文件数最多的语言
        return max(language_counts.items(), key=lambda x: x[1])[0]

    def parse_python_requirements(self, file_path):
        """解析Python的requirements.txt文件"""
        dependencies = set()
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and line != '\n':
                        # 处理类似 package==1.0.0 的格式
                        match = re.match(r'([a-zA-Z0-9_\-\.]+)', line)
                        if match:
                            lib_name = match.group(1).lower()
                            # 过滤标准库
                            if lib_name not in self.STANDARD_LIBRARIES.get('Python', set()):
                                dependencies.add(lib_name)
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
        return dependencies

    def parse_package_json(self, file_path):
        """解析JavaScript的package.json文件"""
        dependencies = set()
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                # 获取生产依赖
                if 'dependencies' in data:
                    for lib_name in data['dependencies']:
                        if lib_name.lower() not in self.STANDARD_LIBRARIES.get('JavaScript', set()):
                            dependencies.add(lib_name.lower())
                # 获取开发依赖
                if 'devDependencies' in data:
                    for lib_name in data['devDependencies']:
                        if lib_name.lower() not in self.STANDARD_LIBRARIES.get('JavaScript', set()):
                            dependencies.add(lib_name.lower())
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
        return dependencies

    def parse_pom_xml(self, file_path):
        """解析Java的pom.xml文件"""
        dependencies = set()
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            ns = {'maven': 'http://maven.apache.org/POM/4.0.0'}
            
            for dep in root.findall('.//maven:dependency', ns):
                group_id = dep.find('maven:groupId', ns)
                artifact_id = dep.find('maven:artifactId', ns)
                
                if group_id is not None and artifact_id is not None:
                    # 检查是否是标准库
                    group_id_text = group_id.text
                    is_standard = False
                    for std_lib in self.STANDARD_LIBRARIES.get('Java', set()):
                        if std_lib in group_id_text:
                            is_standard = True
                            break
                    
                    if not is_standard:
                        dependencies.add(artifact_id.text.lower())
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
        return dependencies

    def parse_go_mod(self, file_path):
        """解析Go的go.mod文件"""
        dependencies = set()
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    # 匹配 require 行
                    if line.startswith('require'):
                        parts = line.split()
                        if len(parts) >= 2:
                            # 跳过 require 关键字
                            if parts[1] != '(':  # 处理多行 require
                                dep = parts[1].split('/')[-1]  # 获取最后一部分作为库名
                                if dep.lower() not in self.STANDARD_LIBRARIES.get('Go', set()):
                                    dependencies.add(dep.lower())
                        continue
                    # 处理多行 require 中的依赖
                    if line and not line.startswith('//') and line != ')':
                        parts = line.split()
                        if parts:
                            dep = parts[0].split('/')[-1]  # 获取最后一部分作为库名
                            if dep.lower() not in self.STANDARD_LIBRARIES.get('Go', set()):
                                dependencies.add(dep.lower())
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
        return dependencies

    def parse_cargo_toml(self, file_path):
        """解析Rust的Cargo.toml文件"""
        dependencies = set()
        try:
            with open(file_path, 'rb') as f:
                data = tomli.load(f)
                # 获取依赖
                if 'dependencies' in data:
                    for lib_name in data['dependencies']:
                        if lib_name.lower() not in self.STANDARD_LIBRARIES.get('Rust', set()):
                            dependencies.add(lib_name.lower())
                # 获取开发依赖
                if 'dev-dependencies' in data:
                    for lib_name in data['dev-dependencies']:
                        if lib_name.lower() not in self.STANDARD_LIBRARIES.get('Rust', set()):
                            dependencies.add(lib_name.lower())
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
        return dependencies

    def parse_gemfile(self, file_path):
        """解析Ruby的Gemfile文件"""
        dependencies = set()
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    # 匹配 gem 'name' 或 gem "name"
                    match = re.match(r'gem\s+[\'"]([a-zA-Z0-9_\-]+)[\'"]', line)
                    if match:
                        lib_name = match.group(1).lower()
                        if lib_name not in self.STANDARD_LIBRARIES.get('Ruby', set()):
                            dependencies.add(lib_name)
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
        return dependencies

    def categorize_dependency(self, lib_name, language):
        """将依赖映射到类别"""
        categories = []
        for category, lang_libs in self.DEPENDENCY_CATEGORIES.items():
            if language in lang_libs:
                for keyword in lang_libs[language]:
                    if keyword in lib_name:
                        categories.append(category)
                        break
        return categories if categories else ['其他']

    def analyze_repository(self, repo_path):
        """分析单个仓库的依赖情况"""
        result = {
            'path': str(repo_path),
            'language': 'Unknown',
            'dependencies': set(),
            'category_dependencies': defaultdict(int)
        }
        
        # 检测主要语言
        result['language'] = self.detect_language(repo_path)
        
        # 解析依赖
        lang_info = self.LANGUAGE_PATTERNS.get(result['language'])
        if lang_info:
            dep_file = repo_path / lang_info['file']
            if dep_file.exists():
                # 调用相应的解析函数
                parser_func = lang_info['parser']
                result['dependencies'] = parser_func(dep_file)
            
            # 尝试在子目录中查找依赖文件
            for root, _, files in os.walk(repo_path):
                if lang_info['file'] in files and root != repo_path:
                    dep_file = Path(root) / lang_info['file']
                    parser_func = lang_info['parser']
                    sub_deps = parser_func(dep_file)
                    result['dependencies'].update(sub_deps)
        
        # 映射到依赖类别
        for dep in result['dependencies']:
            categories = self.categorize_dependency(dep, result['language'])
            for category in categories:
                result['category_dependencies'][category] += 1
        
        return result

    def run_analysis(self, repos_dir, output_dir, min_count=1):
        """运行完整的分析并输出结果"""
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 分析所有仓库
        all_results = []
        total_repos = 0
        error_count = 0
        
        print(f"开始分析仓库，目录: {repos_dir}")
        
        # 获取仓库列表
        repo_paths = []
        for item in os.listdir(repos_dir):
            item_path = os.path.join(repos_dir, item)
            if os.path.isdir(item_path):
                repo_paths.append(Path(item_path))
        
        total_repos = len(repo_paths)
        print(f"发现 {total_repos} 个仓库")
        
        # 处理每个仓库
        for i, repo in enumerate(repo_paths, 1):
            print(f'分析仓库 {i}/{total_repos}: {repo.name}')
            try:
                result = self.analyze_repository(repo)
                all_results.append(result)
            except Exception as e:
                error_count += 1
                print(f'分析 {repo.name} 时出错: {e}')
        
        # 统计结果
        self._generate_statistics(all_results, output_dir, total_repos, min_count)
        
        print(f'\n分析完成!')
        print(f'- 总仓库数: {total_repos}')
        print(f'- 成功分析: {len(all_results)}')
        print(f'- 分析错误: {error_count}')
        print(f'- 结果已保存到 {output_dir}')

    def _generate_statistics(self, all_results, output_dir, total_repos, min_count):
        """生成并保存统计结果"""
        # 统计语言分布
        language_stats = defaultdict(int)
        for result in all_results:
            language_stats[result['language']] += 1
        
        # 统计库使用频率
        library_stats = defaultdict(int)
        category_stats = defaultdict(int)
        lang_library_stats = defaultdict(Counter)
        
        for result in all_results:
            for dep in result['dependencies']:
                library_stats[dep] += 1
                lang_library_stats[result['language']][dep] += 1
            for category, count in result['category_dependencies'].items():
                category_stats[category] += count
        
        # 过滤低频次的库
        filtered_library_stats = {k: v for k, v in library_stats.items() if v >= min_count}
        
        # 保存详细结果到JSON
        final_results = {
            'total_repositories': total_repos,
            'analyzed_repositories': len(all_results),
            'language_distribution': dict(language_stats),
            'library_usage': dict(filtered_library_stats),
            'category_usage': dict(category_stats),
            'detailed_results': all_results
        }
        
        output_json = Path(output_dir) / 'library_usage_detail.json'
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(final_results, f, ensure_ascii=False, indent=2)
        
        # 保存到CSV（适合GraphPad Prism使用的格式）
        self._save_to_csv(filtered_library_stats, output_dir, 'library_statistics.csv', total_repos)
        self._save_to_csv(category_stats, output_dir, 'category_statistics.csv', total_repos)
        
        # 按语言保存库使用统计
        for lang, stats in lang_library_stats.items():
            lang_output = Path(output_dir) / f'library_statistics_{lang.lower()}.csv'
            # 过滤该语言的低频次库
            filtered_lang_stats = {k: v for k, v in stats.items() if v >= min_count}
            self._save_to_csv(filtered_lang_stats, output_dir, f'library_statistics_{lang.lower()}.csv', 
                            language_stats.get(lang, 1))
    
    def _save_to_csv(self, stats, output_dir, filename, total_count):
        """将统计结果保存为CSV格式"""
        output_csv = Path(output_dir) / filename
        
        with open(output_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # CSV头部，适合GraphPad Prism使用
            writer.writerow(['名称', '数量', '百分比'])
            
            # 按使用次数排序
            for name, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / total_count) * 100 if total_count > 0 else 0
                writer.writerow([name, count, f'{percentage:.2f}'])

def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='分析多个仓库的库引用频率')
    parser.add_argument('--repo-dir', type=str, default='/path/to/cloned/repos', 
                      help='包含仓库的目录路径')
    parser.add_argument('--output-dir', type=str, default='analysis', 
                      help='输出结果的目录路径')
    parser.add_argument('--min-count', type=int, default=1, 
                      help='最小统计次数，低于此值的库将被过滤')
    
    args = parser.parse_args()
    
    # 验证仓库目录是否存在
    if not os.path.exists(args.repo_dir):
        print(f"错误：仓库目录不存在: {args.repo_dir}")
        print("请使用 --repo-dir 参数指定正确的仓库目录路径")
        return
    
    # 创建分析器实例并运行分析
    analyzer = LibraryAnalyzer()
    analyzer.run_analysis(args.repo_dir, args.output_dir, args.min_count)

if __name__ == '__main__':
    main()