import os
import json
import csv
import re
import argparse
import subprocess
from collections import defaultdict, Counter
from pathlib import Path
import xml.etree.ElementTree as ET
import tomli  # 用于解析Cargo.toml
from typing import Dict, List, Set, Tuple, Optional

class EnhancedRepoAnalyzer:
    def __init__(self):
        # 支持的语言和对应的依赖文件模式
        # 修改LANGUAGE_PATTERNS配置，支持多种Python依赖文件格式
        self.LANGUAGE_PATTERNS = {
            'Python': {
                'files': [
                    {'file': 'requirements.txt', 'parser': self.parse_python_requirements},
                    {'file': 'pyproject.toml', 'parser': self.parse_pyproject_toml},
                    {'file': 'setup.py', 'parser': self.parse_setup_py},
                    {'file': 'Pipfile', 'parser': self.parse_pipfile},
                    {'file': 'poetry.lock', 'parser': self.parse_poetry_lock}
                ]
            },
            'JavaScript': {
                'files': [{'file': 'package.json', 'parser': self.parse_package_json}]
            },
            'Java': {
                'files': [{'file': 'pom.xml', 'parser': self.parse_pom_xml}]
            },
            'Go': {
                'files': [{'file': 'go.mod', 'parser': self.parse_go_mod}]
            },
            'Rust': {
                'files': [{'file': 'Cargo.toml', 'parser': self.parse_cargo_toml}]
            },
            'Ruby': {
                'files': [{'file': 'Gemfile', 'parser': self.parse_gemfile}]
            }
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
                'Python': ['tensorflow', 'pytorch', 'scikit-learn', 'numpy', 'pandas', 'matplotlib', 'keras', 'langchain'],
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
                'Python': ['requests', 'aiohttp', 'httpx', 'flask-restful', 'fastapi'],
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

        # 部署方式检测配置
        self.DEPLOYMENT_PATTERNS = {
            'Docker': {
                'files': ['Dockerfile', 'docker-compose.yml', 'docker-compose.yaml'],
                'confidence': 'high'
            },
            'Vercel': {
                'files': ['vercel.json'],
                'keywords': ['vercel'],
                'confidence': 'high'
            },
            'Railway': {
                'files': ['railway.json'],
                'keywords': ['railway'],
                'confidence': 'high'
            },
            'Heroku': {
                'files': ['Procfile', 'heroku.yml'],
                'keywords': ['heroku'],
                'confidence': 'high'
            },
            'AWS': {
                'keywords': ['aws', 'amazon web services', 'lambda', 's3', 'ec2'],
                'confidence': 'medium'
            },
            'Google Cloud': {
                'keywords': ['gcp', 'google cloud', 'cloud run', 'firebase'],
                'confidence': 'medium'
            },
            'GitHub Pages': {
                'files': ['.github/workflows/deploy.yml'],
                'keywords': ['github pages', 'gh-pages'],
                'confidence': 'medium'
            }
        }

        # 核心框架检测配置
        self.FRAMEWORK_DETECTION = {
            'Python': {
                'Flask': {'imports': ['from flask import Flask'], 'dependencies': ['flask']},
                'Django': {'imports': ['from django.db import', 'from django.http import'], 'dependencies': ['django']},
                'FastAPI': {'imports': ['from fastapi import FastAPI'], 'dependencies': ['fastapi']},
                'LangChain': {'imports': ['import langchain'], 'dependencies': ['langchain']}
            },
            'JavaScript': {
                'Express': {'imports': ['const express = require(\'express\')', 'import express from \'express\''], 'dependencies': ['express']},
                'React': {'imports': ['import React from \'react\''], 'dependencies': ['react']},
                'Vue': {'imports': ['import Vue from \'vue\''], 'dependencies': ['vue']},
                'NestJS': {'dependencies': ['@nestjs/core']}
            },
            'Go': {
                'Gin': {'dependencies': ['github.com/gin-gonic/gin']},
                'Echo': {'dependencies': ['github.com/labstack/echo/v4']}
            },
            'Rust': {
                'Actix': {'dependencies': ['actix-web']},
                'Rocket': {'dependencies': ['rocket']}
            }
        }

    def detect_language(self, repo_path: Path) -> str:
        """检测仓库的主要编程语言"""
        language_counts = defaultdict(int)
        # 通过文件扩展名检测
        for root, _, files in os.walk(repo_path):
            for file in files:
                ext = Path(file).suffix.lower()
                language = self.LANGUAGE_EXTENSIONS.get(ext)
                if language:
                    language_counts[language] += 1
                
                # 也通过依赖文件检测 - 修复这里！
                if root == repo_path:
                    for lang, info in self.LANGUAGE_PATTERNS.items():
                        if 'files' in info:
                            for file_config in info['files']:
                                if file == file_config['file']:
                                    language_counts[lang] += 5  # 依赖文件权重更高
        
        if not language_counts:
            return 'Unknown'
        
        # 返回文件数最多的语言
        return max(language_counts.items(), key=lambda x: x[1])[0]

    # 修复parse_pyproject_toml方法
    def parse_pyproject_toml(self, file_path: Path) -> Set[str]:
        """解析pyproject.toml文件中的依赖"""
        dependencies = set()
        try:
            # 使用二进制模式打开文件
            with open(file_path, 'rb') as f:
                data = tomli.load(f)
                # 解析poetry依赖
                if 'tool' in data and 'poetry' in data['tool'] and 'dependencies' in data['tool']['poetry']:
                    for lib_name in data['tool']['poetry']['dependencies']:
                        # 跳过python自身
                        if lib_name.lower() != 'python' and lib_name.lower() not in self.STANDARD_LIBRARIES.get('Python', set()):
                            dependencies.add(lib_name.lower())
                # 解析setuptools依赖
                if 'project' in data and 'dependencies' in data['project']:
                    for dep in data['project']['dependencies']:
                        # 处理形如 "package>=1.0.0" 的格式
                        match = re.match(r'([a-zA-Z0-9_\-\.]+)', dep)
                        if match:
                            lib_name = match.group(1).lower()
                            if lib_name not in self.STANDARD_LIBRARIES.get('Python', set()):
                                dependencies.add(lib_name)
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
        return dependencies
    
    # 修复parse_python_requirements方法，增加编码处理
    def parse_python_requirements(self, file_path: Path) -> Set[str]:
        """解析Python的requirements.txt文件"""
        dependencies = set()
        try:
            # 尝试不同的编码
            encodings = ['utf-8', 'latin-1', 'cp1252']
            content = None
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.readlines()
                    break  # 成功读取后跳出循环
                except UnicodeDecodeError:
                    continue
                
            if content:
                for line in content:
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
    


    def parse_setup_py(self, file_path: Path) -> Set[str]:
        """解析setup.py文件中的依赖"""
        dependencies = set()
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                # 尝试提取install_requires参数
                install_requires_match = re.search(r'install_requires\s*=\s*\[(.*?)\]', content, re.DOTALL)
                if install_requires_match:
                    deps_str = install_requires_match.group(1)
                    # 提取所有依赖名称
                    for match in re.finditer(r'["\']([a-zA-Z0-9_\-\.]+)', deps_str):
                        lib_name = match.group(1).lower()
                        if lib_name not in self.STANDARD_LIBRARIES.get('Python', set()):
                            dependencies.add(lib_name)
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
        return dependencies

    def parse_pipfile(self, file_path: Path) -> Set[str]:
        """解析Pipfile文件中的依赖"""
        dependencies = set()
        try:
            # 尝试不同的编码
            encodings = ['utf-8', 'latin-1', 'cp1252']
            data = None
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                        # 处理可能的JSON解析问题
                        if content.strip():
                            data = json.loads(content)
                    break  # 成功读取后跳出循环
                except (UnicodeDecodeError, json.JSONDecodeError):
                    continue
            
            if data is not None:
                # 解析default依赖
                if 'default' in data:
                    for lib_name in data['default']:
                        if lib_name.lower() not in self.STANDARD_LIBRARIES.get('Python', set()):
                            dependencies.add(lib_name.lower())
                # 解析develop依赖
                if 'develop' in data:
                    for lib_name in data['develop']:
                        if lib_name.lower() not in self.STANDARD_LIBRARIES.get('Python', set()):
                            dependencies.add(lib_name.lower())
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
        return dependencies

    def parse_poetry_lock(self, file_path: Path) -> Set[str]:
        """解析poetry.lock文件中的依赖"""
        dependencies = set()
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                # 提取所有package名称
                for match in re.finditer(r'name\s*=\s*["\']([a-zA-Z0-9_\-\.]+)["\']', content):
                    lib_name = match.group(1).lower()
                    if lib_name not in self.STANDARD_LIBRARIES.get('Python', set()):
                        dependencies.add(lib_name)
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
        return dependencies

    def parse_package_json(self, file_path: Path) -> Set[str]:
        """解析JavaScript的package.json文件"""
        dependencies = set()
        try:
            # 如果是node_modules目录下的文件，采取更高效的处理方式
            if 'node_modules' in str(file_path).split(os.sep):
                # 对于node_modules中的文件，可以采用更简单快速的解析方式
                # 尝试使用快速的二进制读取
                content = None
                try:
                    with open(file_path, 'rb') as f:
                        content = f.read().decode('utf-8', errors='replace')
                except:
                    # 如果读取失败，直接返回空集合，避免在node_modules上花费太多时间
                    return dependencies
            else:
                # 非node_modules目录，使用完整的编码处理
                content = None
                for encoding in ['utf-8', 'utf-16', 'latin-1']:
                    try:
                        with open(file_path, 'rb') as f:
                            content = f.read().decode(encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                
                if content is None:
                    # 如果所有编码都失败，使用chardet尝试检测编码
                    try:
                        import chardet
                        with open(file_path, 'rb') as f:
                            raw_data = f.read()
                            result = chardet.detect(raw_data)
                            encoding = result['encoding'] or 'utf-8'
                            content = raw_data.decode(encoding, errors='replace')
                    except ImportError:
                        # 如果没有chardet库，使用默认编码并替换错误
                        with open(file_path, 'rb') as f:
                            content = f.read().decode('utf-8', errors='replace')
            
            # 保存原始内容用于最后的备选解析
            original_content = content
            
            # 尝试修复常见的JSON语法问题
            # 1. 修复多余的逗号
            content = re.sub(r',\s*}', '}', content)
            content = re.sub(r',\s*\]', ']', content)
            
            # 2. 修复单引号
            content = re.sub(r"'([^']+)'", r'"\1"', content)
            
            # 3. 移除行注释
            content = re.sub(r'//.*$', '', content, flags=re.MULTILINE)
            
            # 4. 移除多行注释
            content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
            
            # 5. 尝试解析修复后的JSON
            try:
                data = json.loads(content)
            except json.JSONDecodeError:
                # 如果基本修复失败，尝试使用更宽松的解析库
                try:
                    import json5
                    data = json5.loads(content)
                except (ImportError, Exception):
                    # 如果没有json5库或者仍解析失败，尝试使用增强的正则表达式作为最后的备选
                    try:
                        # 增强版正则表达式，更灵活地匹配dependencies和devDependencies
                        # 处理不同的空格和换行情况
                        dep_pattern = r'"dependencies"\s*:\s*\{([\s\S]*?)\}'
                        dev_dep_pattern = r'"devDependencies"\s*:\s*\{([\s\S]*?)\}'
                        
                        # 提取依赖项块
                        all_deps_content = ''
                        for pattern in [dep_pattern, dev_dep_pattern]:
                            match = re.search(pattern, original_content, re.DOTALL)
                            if match:
                                all_deps_content += match.group(1)
                        
                        # 从依赖内容中提取包名，使用更健壮的正则表达式
                        # 匹配各种合法的npm包名格式，包括@scope/package形式
                        lib_pattern = r'"(@?[a-zA-Z0-9\-_\.]+(?:/[a-zA-Z0-9\-_\.]+)?)"\s*:'
                        lib_matches = re.findall(lib_pattern, all_deps_content)
                        
                        for lib_name in lib_matches:
                            if lib_name.lower() not in self.STANDARD_LIBRARIES.get('JavaScript', set()):
                                dependencies.add(lib_name.lower())
                        
                        # 如果找到依赖，返回结果，不输出错误
                        if dependencies:
                            return dependencies
                        
                        # 作为最后的备选方案，尝试匹配任何看起来像包名的字符串
                        # 这种方法可能会有一些误报，但总比什么都不返回要好
                        fallback_pattern = r'"(@?[a-zA-Z0-9\-_\.]+(?:/[a-zA-Z0-9\-_\.]+)?)"'
                        fallback_matches = re.findall(fallback_pattern, original_content)
                        
                        for lib_name in fallback_matches:
                            # 过滤掉明显不是包名的字符串
                            if len(lib_name) > 2 and lib_name.lower() not in ['name', 'version', 'description', 'main', 'scripts', 'author', 'license', 'keywords', 'repository', 'homepage', 'bugs']:
                                if lib_name.lower() not in self.STANDARD_LIBRARIES.get('JavaScript', set()):
                                    dependencies.add(lib_name.lower())
                        
                        # 如果通过fallback方法找到依赖，静默返回
                        if dependencies:
                            return dependencies
                        
                        # 只有在所有方法都失败且没有找到任何依赖时才输出错误信息
                        if 'node_modules' not in str(file_path).split(os.sep):
                            print(f"Error parsing {file_path}: Invalid JSON format, even with enhanced regex fallback")
                    except Exception as e:
                        if 'node_modules' not in str(file_path).split(os.sep):
                            print(f"Error parsing {file_path}: {str(e)[:100]}...")
                    return dependencies
            
            # 从成功解析的JSON中提取依赖
            if 'dependencies' in data:
                for lib_name in data['dependencies']:
                    if lib_name.lower() not in self.STANDARD_LIBRARIES.get('JavaScript', set()):
                        dependencies.add(lib_name.lower())
            if 'devDependencies' in data:
                for lib_name in data['devDependencies']:
                    if lib_name.lower() not in self.STANDARD_LIBRARIES.get('JavaScript', set()):
                        dependencies.add(lib_name.lower())
        except Exception as e:
            if 'node_modules' not in str(file_path).split(os.sep):
                print(f"Error parsing {file_path}: {str(e)[:100]}...")  # 限制错误信息长度
        return dependencies

    def parse_pom_xml(self, file_path: Path) -> Set[str]:
        """解析Java的pom.xml文件"""
        dependencies = set()
        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # 定义命名空间映射
            namespaces = {
                'maven': 'http://maven.apache.org/POM/4.0.0'
            }
            
            # 查找所有依赖项
            for dependency in root.findall('.//maven:dependency', namespaces):
                # 获取groupId和artifactId
                group_id = dependency.find('maven:groupId', namespaces)
                artifact_id = dependency.find('maven:artifactId', namespaces)
                
                if group_id is not None and artifact_id is not None:
                    # 组合groupId和artifactId以获得完整标识符
                    full_id = f"{group_id.text}.{artifact_id.text}"
                    if full_id.lower() not in self.STANDARD_LIBRARIES.get('Java', set()):
                        dependencies.add(full_id.lower())
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
        return dependencies

    def parse_go_mod(self, file_path: Path) -> Set[str]:
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
                            if parts[1] != '(':
                                dep = self._extract_meaningful_go_dependency(parts[1])
                                if dep and dep.lower() not in self.STANDARD_LIBRARIES.get('Go', set()):
                                    dependencies.add(dep.lower())
                        continue
                    # 处理多行 require 中的依赖
                    if line and not line.startswith('//') and line != ')':
                        parts = line.split()
                        if parts:
                            dep = self._extract_meaningful_go_dependency(parts[0])
                            if dep and dep.lower() not in self.STANDARD_LIBRARIES.get('Go', set()):
                                dependencies.add(dep.lower())
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
        return dependencies
    
    def _extract_meaningful_go_dependency(self, full_path: str) -> str:
        """从完整的Go依赖路径中提取有意义的库名"""
        try:
            # 分割路径
            parts = full_path.split('/')
            
            # 如果路径太短，返回原始的最后一部分
            if len(parts) <= 2:
                return parts[-1].split('@')[0]  # 移除版本信息
            
            # 检查是否包含版本号后缀 (如 /v2, /v3)
            main_part = parts[-2] if len(parts) > 2 and parts[-1].startswith('v') and parts[-1][1:].isdigit() else parts[-1]
            
            # 移除版本信息
            main_part = main_part.split('@')[0]
            
            # 对于常见的通用组件名，尝试获取更具体的部分
            common_generic_terms = {'sdk', 'api', 'client', 'server', 'core', 'common', 'utils', 'tools'}
            if main_part.lower() in common_generic_terms and len(parts) > 2:
                # 尝试组合前一部分和当前部分
                return f"{parts[-2].split('@')[0]}_{main_part}" if not (parts[-2].startswith('v') and parts[-2][1:].isdigit()) else main_part
            
            return main_part
        except:
            # 如果处理失败，回退到原始方法
            return full_path.split('/')[-1].split('@')[0]

    def parse_cargo_toml(self, file_path: Path) -> Set[str]:
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

    def parse_gemfile(self, file_path: Path) -> Set[str]:
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

    def categorize_dependency(self, lib_name: str, language: str) -> List[str]:
        """将依赖映射到类别"""
        categories = []
        for category, lang_libs in self.DEPENDENCY_CATEGORIES.items():
            if language in lang_libs:
                for keyword in lang_libs[language]:
                    if keyword in lib_name:
                        categories.append(category)
                        break
        return categories if categories else ['其他']

    def detect_deployment_methods(self, repo_path: Path) -> Dict[str, str]:
        """检测仓库的部署方式"""
        deployment_methods = {}
        
        # 1. 检查配置文件
        for method, config in self.DEPLOYMENT_PATTERNS.items():
            if 'files' in config:
                for file_name in config['files']:
                    if (repo_path / file_name).exists():
                        deployment_methods[method] = config['confidence']
                        break
        
        # 2. 搜索README和文档文件中的关键词
        readme_files = []
        for file_name in ['README.md', 'README', 'README.rst', 'docs/deployment.md']:
            file_path = repo_path / file_name
            if file_path.exists():
                readme_files.append(file_path)
        
        # 3. 搜索GitHub Actions配置
        github_actions_dir = repo_path / '.github' / 'workflows'
        if github_actions_dir.exists():
            for file_name in os.listdir(github_actions_dir):
                if file_name.endswith('.yml') or file_name.endswith('.yaml'):
                    readme_files.append(github_actions_dir / file_name)
        
        # 搜索关键词
        for method, config in self.DEPLOYMENT_PATTERNS.items():
            if method in deployment_methods:  # 已通过文件检测确认
                continue
                
            if 'keywords' in config:
                for file_path in readme_files:
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read().lower()
                            if any(keyword.lower() in content for keyword in config['keywords']):
                                deployment_methods[method] = config['confidence']
                                break
                    except Exception:
                        continue
        
        return deployment_methods

    def detect_frameworks(self, repo_path: Path, language: str, dependencies: Set[str]) -> Dict[str, str]:
        """检测仓库使用的核心框架"""
        frameworks = {}
        
        # 1. 通过依赖检测
        if language in self.FRAMEWORK_DETECTION:
            for framework, config in self.FRAMEWORK_DETECTION[language].items():
                if 'dependencies' in config:
                    for dep in config['dependencies']:
                        # 对于Go和其他语言，需要处理完整的包名
                        if language == 'Go':
                            # 检查依赖中是否包含完整的包名
                            for repo_dep in dependencies:
                                if dep.split('/')[-1] == repo_dep:
                                    frameworks[framework] = 'dependency'
                                    break
                        elif dep in dependencies:
                            frameworks[framework] = 'dependency'
                            break
        
        # 2. 通过代码导入语句检测
        if language in self.FRAMEWORK_DETECTION:
            # 查找可能的入口文件
            entry_files = []
            if language == 'Python':
                entry_files = ['main.py', 'app.py', '__init__.py']
            elif language in ['JavaScript', 'TypeScript']:
                entry_files = ['index.js', 'server.js', 'app.js']
            elif language == 'Go':
                entry_files = ['main.go']
            
            # 搜索根目录下的文件
            for file_name in os.listdir(repo_path):
                if file_name in entry_files:
                    entry_files = [repo_path / file_name]
                    break
            
            # 搜索代码文件中的导入语句
            for framework, config in self.FRAMEWORK_DETECTION[language].items():
                if framework in frameworks:  # 已通过依赖检测确认
                    continue
                    
                if 'imports' in config:
                    for file_path in entry_files:
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                if any(imp_statement in content for imp_statement in config['imports']):
                                    frameworks[framework] = 'code'
                                    break
                        except Exception:
                            continue
        
        return frameworks

    def analyze_repository(self, repo_path: Path) -> Dict:
        """分析单个仓库"""
        result = {
            'name': repo_path.name,
            'path': str(repo_path),
            'language': 'Unknown',
            'dependencies': [],
            'category_dependencies': defaultdict(int),
            'deployment_methods': {},
            'frameworks': {}
        }
        
        try:
            # 检测主要语言
            result['language'] = self.detect_language(repo_path)
            
            # 解析依赖
            lang_info = self.LANGUAGE_PATTERNS.get(result['language'])
            if lang_info and 'files' in lang_info:
                for file_config in lang_info['files']:
                    # 检查根目录
                    dep_file = repo_path / file_config['file']
                    if dep_file.exists():
                        try:
                            parser_func = file_config['parser']
                            deps = parser_func(dep_file)
                            result['dependencies'].extend(list(deps))
                        except Exception as e:
                            print(f"解析文件 {dep_file} 时出错: {str(e) or repr(e)}")
                    
                    # 尝试在子目录中查找依赖文件
                    for root, _, files in os.walk(repo_path):
                        if file_config['file'] in files and root != repo_path:
                            dep_file = Path(root) / file_config['file']
                            try:
                                parser_func = file_config['parser']
                                sub_deps = parser_func(dep_file)
                                result['dependencies'].extend(list(sub_deps))
                            except Exception as e:
                                print(f"解析文件 {dep_file} 时出错: {str(e) or repr(e)}")
            
            # 去重依赖列表
            result['dependencies'] = list(set(result['dependencies']))
            
            # 映射到依赖类别
            for dep in result['dependencies']:
                categories = self.categorize_dependency(dep, result['language'])
                for category in categories:
                    result['category_dependencies'][category] += 1
            
            # 检测部署方式
            result['deployment_methods'] = self.detect_deployment_methods(repo_path)
            
            # 检测使用的框架
            result['frameworks'] = self.detect_frameworks(repo_path, result['language'], result['dependencies'])
            
        except Exception as e:
            # 捕获所有其他异常并提供详细信息
            print(f"分析仓库 {repo_path.name} 时发生意外错误: {str(e) or repr(e)}")
            # 即使出错也返回已收集的结果
        
        return result

    def run_analysis(self, repos_dir: str, output_dir: str, min_count: int = 1):
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

    def _generate_statistics(self, all_results: List[Dict], output_dir: str, total_repos: int, min_count: int):
        """生成并保存统计结果"""
        # 统计语言分布
        language_stats = defaultdict(int)
        for result in all_results:
            language_stats[result['language']] += 1
        
        # 统计库使用频率
        library_stats = defaultdict(int)
        category_stats = defaultdict(int)
        lang_library_stats = defaultdict(Counter)
        
        # 统计部署方式
        deployment_stats = defaultdict(int)
        deployment_confidence_stats = defaultdict(lambda: defaultdict(int))
        
        # 统计框架使用情况
        framework_stats = defaultdict(int)
        lang_framework_stats = defaultdict(Counter)
        
        for result in all_results:
            # 统计库
            for dep in result['dependencies']:
                library_stats[dep] += 1
                lang_library_stats[result['language']][dep] += 1
            for category, count in result['category_dependencies'].items():
                category_stats[category] += count
            
            # 统计部署方式
            for method, confidence in result['deployment_methods'].items():
                deployment_stats[method] += 1
                deployment_confidence_stats[method][confidence] += 1
            
            # 统计框架
            for framework in result['frameworks']:
                framework_stats[framework] += 1
                lang_framework_stats[result['language']][framework] += 1
        
        # 过滤低频次的库
        filtered_library_stats = {k: v for k, v in library_stats.items() if v >= min_count}
        
        # 保存详细结果到JSON
        final_results = {
            'total_repositories': total_repos,
            'analyzed_repositories': len(all_results),
            'language_distribution': dict(language_stats),
            'library_usage': dict(filtered_library_stats),
            'category_usage': dict(category_stats),
            'deployment_methods': dict(deployment_stats),
            'deployment_confidence': {k: dict(v) for k, v in deployment_confidence_stats.items()},
            'framework_usage': dict(framework_stats),
            'detailed_results': all_results
        }
        
        output_json = Path(output_dir) / 'enhanced_analysis_detail.json'
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(final_results, f, ensure_ascii=False, indent=2)
        
        # 保存到CSV（适合GraphPad Prism使用的格式）
        self._save_to_csv(filtered_library_stats, output_dir, 'library_statistics.csv', total_repos)
        self._save_to_csv(category_stats, output_dir, 'category_statistics.csv', total_repos)
        self._save_to_csv(deployment_stats, output_dir, 'deployment_statistics.csv', total_repos)
        self._save_to_csv(framework_stats, output_dir, 'framework_statistics.csv', total_repos)
        
        # 按语言保存库使用统计
        for lang, stats in lang_library_stats.items():
            lang_output = Path(output_dir) / f'library_statistics_{lang.lower()}.csv'
            # 过滤该语言的低频次库
            filtered_lang_stats = {k: v for k, v in stats.items() if v >= min_count}
            self._save_to_csv(filtered_lang_stats, output_dir, f'library_statistics_{lang.lower()}.csv', 
                            language_stats.get(lang, 1))
            
        # 按语言保存框架统计
        for lang, stats in lang_framework_stats.items():
            self._save_to_csv(dict(stats), output_dir, f'framework_statistics_{lang.lower()}.csv', 
                            language_stats.get(lang, 1))

    def _save_to_csv(self, stats: Dict[str, int], output_dir: str, filename: str, total_count: int):
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

    def clone_repos_from_json(self, json_path: str, output_dir: str, github_token: str):
        """从JSON文件中克隆仓库"""
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 设置请求头
        headers = {
            'Authorization': f'token {github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        # 读取JSON文件
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"读取JSON文件失败: {e}")
            return
        
        # 提取并处理GitHub URL
        url_info = []
        for item in data:
            if 'github_url' in item:
                url = item['github_url']
                # 处理不同格式的GitHub URL
                if isinstance(url, str) and url:
                    # 简化的URL处理
                    if 'github.com' in url:
                        # 提取用户名和仓库名的简单实现
                        parts = url.strip('/').split('/')
                        if len(parts) >= 2:
                            # 找到用户名和仓库名的索引
                            user_idx = parts.index('github.com') + 1 if 'github.com' in parts else None
                            if user_idx and user_idx + 1 < len(parts):
                                user = parts[user_idx]
                                repo = parts[user_idx + 1]
                                # 移除.git后缀
                                if repo.endswith('.git'):
                                    repo = repo[:-4]
                                url_info.append((f'https://github.com/{user}/{repo}', user, repo))
        
        # 去重
        unique_url_info = list({url: (url, user, repo) for url, user, repo in url_info}.values())
        print(f"\n📊 GitHub仓库统计:")
        print(f"   - 去重后总共有 {len(unique_url_info)} 个唯一GitHub仓库")
        
        # 克隆仓库
        print(f"\n🚀 开始克隆 {len(unique_url_info)} 个仓库...")
        failed_urls = []
        repo_counter = {}  # 用于跟踪重复的仓库名
        
        for url, user, repo in unique_url_info:
            failed = self._clone_repo(url, output_dir, user, repo, repo_counter, headers)
            if failed:
                failed_urls.append(failed)
        
        # 处理失败的克隆
        if failed_urls:
            with open(Path(output_dir) / "clone_failed.txt", "w", encoding="utf-8") as f:
                f.write("\n".join(failed_urls))
            print(f"\n⚠️ {len(failed_urls)} 个仓库克隆失败，详见 clone_failed.txt")
        else:
            print("\n🎉 所有仓库克隆成功")

    def _clone_repo(self, url: str, output_dir: str, user: str, repo: str, repo_counter: Dict[str, int], headers: Dict[str, str]) -> Optional[str]:
        """使用GitHub API克隆仓库到指定目录，处理重复仓库名"""
        # 基础文件夹名称
        base_folder_name = f"{user}_{repo}"
        
        # 处理重复仓库名
        counter = repo_counter.get(base_folder_name, 0)
        folder_name = base_folder_name if counter == 0 else f"{base_folder_name}_{counter}"
        repo_counter[base_folder_name] = counter + 1
        
        dest = Path(output_dir) / folder_name

        if dest.exists():
            print(f"已存在: {dest}")
            return None

        # 检查仓库是否存在
        if not self._check_repo_exists(url, headers):
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

    def _check_repo_exists(self, url: str, headers: Dict[str, str]) -> bool:
        """检查仓库是否存在并可访问"""
        api_url = url.replace('https://github.com', 'https://api.github.com/repos')
        try:
            response = requests.get(api_url, headers=headers, timeout=10)
            return response.status_code == 200
        except Exception:
            return False

# 为了支持独立运行克隆功能，添加requests导入检查
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='增强版MCP仓库分析工具')
    subparsers = parser.add_subparsers(dest='command', help='选择要执行的命令')
    
    # 克隆命令
    clone_parser = subparsers.add_parser('clone', help='从JSON文件克隆仓库')
    clone_parser.add_argument('json_path', help='包含github_url的JSON文件路径')
    clone_parser.add_argument('output_dir', help='克隆仓库的输出目录')
    clone_parser.add_argument('--token', help='GitHub个人访问令牌，如果未提供则从环境变量GITHUB_TOKEN获取')
    
    # 分析命令
    analyze_parser = subparsers.add_parser('analyze', help='分析仓库')
    analyze_parser.add_argument('--repo-dir', type=str, required=True, 
                              help='包含仓库的目录路径')
    analyze_parser.add_argument('--output-dir', type=str, default='analysis', 
                              help='输出结果的目录路径')
    analyze_parser.add_argument('--min-count', type=int, default=1, 
                              help='最小统计次数，低于此值的库将被过滤')
    
    args = parser.parse_args()
    
    # 执行命令
    analyzer = EnhancedRepoAnalyzer()
    
    if args.command == 'clone':
        # 检查requests库是否可用
        if not HAS_REQUESTS:
            print("错误：缺少requests库，请运行 'pip install requests' 安装")
            return
        
        # 获取GitHub令牌
        github_token = args.token or os.environ.get('GITHUB_TOKEN')
        if not github_token:
            print("错误：未找到GitHub令牌，请通过--token参数提供或设置GITHUB_TOKEN环境变量")
            return
        
        analyzer.clone_repos_from_json(args.json_path, args.output_dir, github_token)
    
    elif args.command == 'analyze':
        # 验证仓库目录是否存在
        if not os.path.exists(args.repo_dir):
            print(f"错误：仓库目录不存在: {args.repo_dir}")
            return
        
        analyzer.run_analysis(args.repo_dir, args.output_dir, args.min_count)
    
    else:
        parser.print_help()

if __name__ == '__main__':
    main()

