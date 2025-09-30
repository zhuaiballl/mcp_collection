from abc import ABC, abstractmethod
from typing import Set, Dict, Optional

# 定义威胁类型
THREAT_TYPES = {
    'COMMAND_EXECUTION': '命令执行',
    'FILE_OPERATION': '文件操作',
    'CODE_INJECTION': '代码注入',
    'DESERIALIZATION': '反序列化',
    'DATABASE_OPERATION': '数据库操作',
    'NETWORK_REQUEST': '网络请求',
    'MEMORY_SAFETY': '内存安全',
    'PATH_TRAVERSAL': '路径穿越',
    'INFORMATION_LEAK': '信息泄露',
    'XXE': 'XML外部实体',
    'XSS': '跨站脚本',
    'DYNAMIC_LOADING': '动态加载',
    'CRYPTO_WEAKNESS': '密码学弱点',
    'OS_COMMAND_INJECTION': '系统命令注入',
    'PRIVILEGE_ESCALATION': '权限提升',
    'CREDENTIAL_EXPOSURE': '凭证暴露',
    'SYSTEM_MODIFICATION': '系统修改',
    'RESOURCE_EXHAUSTION': '资源耗尽',
    'INSECURE_TEMP_FILE': '不安全的临时文件',
    'ENVIRONMENT_MANIPULATION': '环境变量操作',
    'MEMORY_CORRUPTION': '内存破坏',
    'WEAK_ENCRYPTION': '弱加密'
}

class APIChecker(ABC):
    """API检查器的基类"""
    
    @property
    @abstractmethod
    def dangerous_apis(self) -> Set[str]:
        """返回危险API列表"""
        pass
        
    @abstractmethod
    def is_dangerous_api(self, api_name: str) -> bool:
        """检查是否是危险API"""
        pass
        
    @abstractmethod
    def get_api_description(self, api_name: str) -> str:
        """获取API的描述信息"""
        pass
        
    @abstractmethod
    def get_api_threat_type(self, api_name: str) -> str:
        """获取API的威胁类型"""
        pass

class PythonAPIChecker(APIChecker):
    """Python语言的API检查器"""
    def __init__(self):
        self._dangerous_apis = {
            # 命令执行 - 高风险
            'os.system': {
                'description': '执行系统命令，可能导致任意代码执行',
                'threat_type': 'COMMAND_EXECUTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'os.popen': {
                'description': '执行系统命令并获取输出，可能导致任意代码执行',
                'threat_type': 'COMMAND_EXECUTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'subprocess.run': {
                'description': '执行系统命令，可能导致任意代码执行',
                'threat_type': 'COMMAND_EXECUTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'subprocess.Popen': {
                'description': '执行系统命令，可能导致任意代码执行',
                'threat_type': 'COMMAND_EXECUTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'subprocess.call': {
                'description': '执行系统命令，可能导致任意代码执行',
                'threat_type': 'COMMAND_EXECUTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'subprocess.check_call': {
                'description': '执行系统命令，可能导致任意代码执行',
                'threat_type': 'COMMAND_EXECUTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'subprocess.check_output': {
                'description': '执行系统命令并获取输出，可能导致任意代码执行',
                'threat_type': 'COMMAND_EXECUTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            
            # 危险文件操作 - 高风险
            'os.unlink': {
                'description': '删除文件，可能导致意外删除重要文件',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            'os.remove': {
                'description': '删除文件，可能导致意外删除重要文件',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            'os.rmdir': {
                'description': '删除目录，可能导致意外删除重要目录',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            'shutil.rmtree': {
                'description': '递归删除目录，可能导致意外删除重要目录',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            'os.open': {
                'description': '绕过路径安全检查，导致路径遍历',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            'os.rename': {
                'description': '替换系统文件，可能导致系统不稳定',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            'os.chmod': {
                'description': '修改文件权限导致敏感信息暴露',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            'os.symlink': {
                'description': '创建恶意符号链接指向特权文件',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            'os.link': {
                'description': '创建硬链接指向特权文件用于提权',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            'os.mkdir': {
                'description': '创建高权限目录',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            'os.stat': {
                'description': '泄露文件元数据',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            'os.utime': {
                'description': '修改文件时间戳掩盖攻击痕迹',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            'os.truncate': {
                'description': '清空文件内容',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            'os.path.exists': {
                'description': '探测敏感文件路径',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            'os.access': {
                'description': '误判文件可写性导致意外覆盖',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            'os.lchmod': {
                'description': '修改符号链接权限',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            'os.makedirs': {
                'description': '创建多层目录导致权限配置错误',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            'os.chown': {
                'description': '修改文件所有者破坏权限模型',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            'os.fdopen': {
                'description': '手动创建文件未处理竞争条件',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            'shutil.copy': {
                'description': '覆盖目标文件',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            'shutil.move': {
                'description': '移动文件到恶意路径',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            'shutil.chown': {
                'description': '修改文件所有者导致权限混乱',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            'tempfile.mktemp': {
                'description': '临时文件名可预测，导致竞态条件被劫持',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            'tempfile.NamedTemporaryFile': {
                'description': '临时文件未自动删除，残留敏感数据',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            'pathlib.Path.write_text': {
                'description': '未校验路径导致任意文件写入',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            'pathlib.Path.unlink': {
                'description': '删除文件未校验路径',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            'io.open': {
                'description': '类似os.open的路径遍历风险',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            
            # 代码执行 - 高风险
            'eval': {
                'description': '执行Python表达式，可能导致任意代码执行',
                'threat_type': 'CODE_INJECTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'exec': {
                'description': '执行Python代码，可能导致任意代码执行',
                'threat_type': 'CODE_INJECTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'compile': {
                'description': '编译Python代码，可能导致代码注入',
                'threat_type': 'CODE_INJECTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            
            # 网络操作 - 高风险
            'socket.connect': {
                'description': '连接外部恶意服务器',
                'threat_type': 'NETWORK_REQUEST',
                'resource_type': 'NETWORK_RESOURCE'
            },
            'socket.bind': {
                'description': '开放高危端口导致未授权访问',
                'threat_type': 'NETWORK_REQUEST',
                'resource_type': 'NETWORK_RESOURCE'
            },
            'socket.send': {
                'description': '明文传输敏感数据',
                'threat_type': 'NETWORK_REQUEST',
                'resource_type': 'NETWORK_RESOURCE'
            },
            'socket.recv': {
                'description': '接收恶意构造数据包导致缓冲区溢出',
                'threat_type': 'NETWORK_REQUEST',
                'resource_type': 'NETWORK_RESOURCE'
            },
            'socket.listen': {
                'description': '监听未授权端口暴露服务',
                'threat_type': 'NETWORK_REQUEST',
                'resource_type': 'NETWORK_RESOURCE'
            },
            'requests.get': {
                'description': 'SSRF攻击内网',
                'threat_type': 'NETWORK_REQUEST',
                'resource_type': 'NETWORK_RESOURCE'
            },
            'requests.post': {
                'description': '未校验请求参数导致恶意数据提交',
                'threat_type': 'NETWORK_REQUEST',
                'resource_type': 'NETWORK_RESOURCE'
            },
            'urllib.request.urlopen': {
                'description': '未校验URL导致内网资源泄露',
                'threat_type': 'NETWORK_REQUEST',
                'resource_type': 'NETWORK_RESOURCE'
            },
            'urllib.parse.urljoin': {
                'description': '拼接恶意URL触发路径遍历攻击',
                'threat_type': 'NETWORK_REQUEST',
                'resource_type': 'NETWORK_RESOURCE'
            },
            
            # 反序列化 - 高风险
            'pickle.loads': {
                'description': '反序列化Python对象，可能导致任意代码执行',
                'threat_type': 'DESERIALIZATION',
                'resource_type': 'MEMORY_RESOURCE'
            },
            'pickle.load': {
                'description': '从文件反序列化Python对象，可能导致任意代码执行',
                'threat_type': 'DESERIALIZATION',
                'resource_type': 'MEMORY_RESOURCE'
            },
            'marshal.loads': {
                'description': '反序列化Python代码对象，可能导致任意代码执行',
                'threat_type': 'DESERIALIZATION',
                'resource_type': 'MEMORY_RESOURCE'
            },
            'marshal.load': {
                'description': '从文件反序列化Python代码对象，可能导致任意代码执行',
                'threat_type': 'DESERIALIZATION',
                'resource_type': 'MEMORY_RESOURCE'
            },
            'yaml.load': {
                'description': '不安全的YAML解析，可能导致任意代码执行',
                'threat_type': 'DESERIALIZATION',
                'resource_type': 'MEMORY_RESOURCE'
            },
            'yaml.unsafe_load': {
                'description': '不安全的YAML解析，可能导致任意代码执行',
                'threat_type': 'DESERIALIZATION',
                'resource_type': 'MEMORY_RESOURCE'
            },
            
            # 内存操作 - 高风险
            'ctypes.memmove': {
                'description': '内存越界操作导致进程崩溃或代码执行',
                'threat_type': 'MEMORY_SAFETY',
                'resource_type': 'MEMORY_RESOURCE'
            },
            'ctypes.cast': {
                'description': '类型转换错误引发内存泄漏或崩溃',
                'threat_type': 'MEMORY_SAFETY',
                'resource_type': 'MEMORY_RESOURCE'
            },
            'ctypes.POINTER': {
                'description': '指针操作不当导致内存破坏',
                'threat_type': 'MEMORY_SAFETY',
                'resource_type': 'MEMORY_RESOURCE'
            },
            'ctypes.CDLL': {
                'description': '动态加载恶意共享库',
                'threat_type': 'DYNAMIC_LOADING',
                'resource_type': 'MEMORY_RESOURCE'
            },
            'ctypes.create_string_buffer': {
                'description': '固定缓冲区大小未校验输入导致溢出',
                'threat_type': 'MEMORY_SAFETY',
                'resource_type': 'MEMORY_RESOURCE'
            },
            
            # 进程操作 - 高风险
            'os.execl': {
                'description': '替换当前进程执行恶意命令',
                'threat_type': 'COMMAND_EXECUTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'os.spawnlp': {
                'description': '执行外部命令继承过高权限',
                'threat_type': 'COMMAND_EXECUTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'multiprocessing.Process': {
                'description': '创建大量进程导致资源耗尽',
                'threat_type': 'RESOURCE_EXHAUSTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'os.fork': {
                'description': '创建子进程过多导致资源耗尽或系统崩溃',
                'threat_type': 'RESOURCE_EXHAUSTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'os.kill': {
                'description': '发送信号干扰其他进程',
                'threat_type': 'PROCESS_MANIPULATION',
                'resource_type': 'SYSTEM_RESOURCE'
            }
        }
        
    @property
    def dangerous_apis(self) -> Set[str]:
        return set(self._dangerous_apis.keys())
        
    def is_dangerous_api(self, api_name: str) -> bool:
        return api_name in self._dangerous_apis
        
    def get_api_description(self, api_name: str) -> str:
        return self._dangerous_apis.get(api_name, {}).get('description', '未知的危险API')
        
    def get_api_threat_type(self, api_name: str) -> str:
        return self._dangerous_apis.get(api_name, {}).get('threat_type', 'UNKNOWN')
        
    def get_api_resource_type(self, api_name: str) -> str:
        return self._dangerous_apis.get(api_name, {}).get('resource_type', 'UNKNOWN')

class TypeScriptAPIChecker(APIChecker):
    """JavaScript/TypeScript语言的API检查器"""
    def __init__(self):
        self._dangerous_apis = {
            # 命令执行 - 高风险
            'child_process.exec': {
                'description': '执行系统命令，可能导致任意代码执行',
                'threat_type': 'COMMAND_EXECUTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'child_process.spawn': {
                'description': '创建新进程，可能导致任意代码执行',
                'threat_type': 'COMMAND_EXECUTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'child_process.execSync': {
                'description': '同步执行系统命令，可能导致任意代码执行',
                'threat_type': 'COMMAND_EXECUTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'child_process.spawnSync': {
                'description': '同步创建新进程，可能导致任意代码执行',
                'threat_type': 'COMMAND_EXECUTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'exec': {
                'description': '执行系统命令，可能导致任意代码执行',
                'threat_type': 'COMMAND_EXECUTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'spawn': {
                'description': '创建新进程，可能导致任意代码执行',
                'threat_type': 'COMMAND_EXECUTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            
            # 危险文件操作 - 高风险
            'fs.unlink': {
                'description': '删除文件，可能导致数据丢失',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            'fs.unlinkSync': {
                'description': '同步删除文件，可能导致数据丢失',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            'fs.rmdir': {
                'description': '删除目录，可能导致数据丢失',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            'fs.rmdirSync': {
                'description': '同步删除目录，可能导致数据丢失',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            'fs.rm': {
                'description': '删除文件或目录，可能导致数据丢失',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            'fs.rmSync': {
                'description': '同步删除文件或目录，可能导致数据丢失',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            
            # 代码执行 - 高风险
            'eval': {
                'description': '执行JavaScript代码字符串，可能导致任意代码执行',
                'threat_type': 'CODE_INJECTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'new Function': {
                'description': '动态创建函数，可能导致任意代码执行',
                'threat_type': 'CODE_INJECTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'setTimeout': {
                'description': '延时执行代码，当第一个参数为字符串时可能导致代码注入',
                'threat_type': 'CODE_INJECTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'setInterval': {
                'description': '定时执行代码，当第一个参数为字符串时可能导致代码注入',
                'threat_type': 'CODE_INJECTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'vm.runInContext': {
                'description': '在指定上下文中运行代码，可能导致任意代码执行',
                'threat_type': 'CODE_INJECTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'vm.runInNewContext': {
                'description': '在新上下文中运行代码，可能导致任意代码执行',
                'threat_type': 'CODE_INJECTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            
            # 网络请求 - 高风险
            'http.request': {
                'description': '发送HTTP请求，可能导致数据泄露',
                'threat_type': 'NETWORK_REQUEST',
                'resource_type': 'NETWORK_RESOURCE'
            },
            'https.request': {
                'description': '发送HTTPS请求，可能导致数据泄露',
                'threat_type': 'NETWORK_REQUEST',
                'resource_type': 'NETWORK_RESOURCE'
            },
            'fetch': {
                'description': '发送网络请求，可能导致数据泄露',
                'threat_type': 'NETWORK_REQUEST',
                'resource_type': 'NETWORK_RESOURCE'
            },
            'axios.get': {
                'description': '发送HTTP GET请求，可能导致数据泄露',
                'threat_type': 'NETWORK_REQUEST',
                'resource_type': 'NETWORK_RESOURCE'
            },
            'axios.post': {
                'description': '发送HTTP POST请求，可能导致数据泄露',
                'threat_type': 'NETWORK_REQUEST',
                'resource_type': 'NETWORK_RESOURCE'
            },
            'XMLHttpRequest': {
                'description': '发送网络请求，可能导致数据泄露',
                'threat_type': 'NETWORK_REQUEST',
                'resource_type': 'NETWORK_RESOURCE'
            },
            'WebSocket': {
                'description': '建立WebSocket连接，可能导致数据泄露',
                'threat_type': 'NETWORK_REQUEST',
                'resource_type': 'NETWORK_RESOURCE'
            },
            
            # XSS相关 - 在客户端JavaScript中特别重要
            'document.write': {
                'description': '直接写入DOM，可能导致XSS攻击',
                'threat_type': 'XSS',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'innerHTML': {
                'description': '设置HTML内容，可能导致XSS攻击',
                'threat_type': 'XSS',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'dangerouslySetInnerHTML': {
                'description': 'React中设置HTML内容，可能导致XSS攻击',
                'threat_type': 'XSS',
                'resource_type': 'SYSTEM_RESOURCE'
            }
        }
        
    @property
    def dangerous_apis(self) -> Set[str]:
        return set(self._dangerous_apis.keys())
        
    def is_dangerous_api(self, api_name: str) -> bool:
        return api_name in self._dangerous_apis
        
    def get_api_description(self, api_name: str) -> str:
        return self._dangerous_apis.get(api_name, {}).get('description', '未知的危险API')
        
    def get_api_threat_type(self, api_name: str) -> str:
        return self._dangerous_apis.get(api_name, {}).get('threat_type', 'UNKNOWN')
        
    def get_api_resource_type(self, api_name: str) -> str:
        return self._dangerous_apis.get(api_name, {}).get('resource_type', 'UNKNOWN')

class RustAPIChecker(APIChecker):
    """Rust语言的API检查器"""
    def __init__(self):
        self._dangerous_apis = {
            # 命令执行 - 高风险
            'std::process::Command::new': {
                'description': '执行系统命令，可能导致任意代码执行',
                'threat_type': 'COMMAND_EXECUTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'std::process::Command::output': {
                'description': '执行系统命令并获取输出，可能导致任意代码执行',
                'threat_type': 'COMMAND_EXECUTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'std::process::Command::status': {
                'description': '执行系统命令并获取状态，可能导致任意代码执行',
                'threat_type': 'COMMAND_EXECUTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'std::process::Command::spawn': {
                'description': '执行系统命令作为新进程，可能导致任意代码执行',
                'threat_type': 'COMMAND_EXECUTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            
            # 危险文件操作 - 高风险
            'std::fs::remove_file': {
                'description': '删除文件，可能导致数据丢失',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            'std::fs::remove_dir': {
                'description': '删除目录，可能导致数据丢失',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            'std::fs::remove_dir_all': {
                'description': '递归删除目录，可能导致数据丢失',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            
            # 网络请求 - 高风险，可能泄露用户数据
            'reqwest::get': {
                'description': '发送HTTP GET请求，可能导致数据泄露',
                'threat_type': 'NETWORK_REQUEST',
                'resource_type': 'NETWORK_RESOURCE'
            },
            'reqwest::Client::get': {
                'description': '使用客户端发送HTTP GET请求，可能导致数据泄露',
                'threat_type': 'NETWORK_REQUEST',
                'resource_type': 'NETWORK_RESOURCE'
            },
            'reqwest::Client::post': {
                'description': '使用客户端发送HTTP POST请求，可能导致数据泄露',
                'threat_type': 'NETWORK_REQUEST',
                'resource_type': 'NETWORK_RESOURCE'
            },
            'hyper::Client': {
                'description': '创建HTTP客户端，可能导致数据泄露',
                'threat_type': 'NETWORK_REQUEST',
                'resource_type': 'NETWORK_RESOURCE'
            },
            'std::net::TcpStream::connect': {
                'description': '创建TCP连接，可能导致数据泄露',
                'threat_type': 'NETWORK_REQUEST',
                'resource_type': 'NETWORK_RESOURCE'
            },
            
            # 代码执行 - 高风险
            'std::mem::transmute': {
                'description': '不安全的类型转换，可能导致代码执行',
                'threat_type': 'CODE_INJECTION',
                'resource_type': 'MEMORY_RESOURCE'
            },
            'dlopen': {
                'description': '动态加载库，可能导致代码执行',
                'threat_type': 'DYNAMIC_LOADING',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'libloading::Library::new': {
                'description': '动态加载库，可能导致代码执行',
                'threat_type': 'DYNAMIC_LOADING',
                'resource_type': 'SYSTEM_RESOURCE'
            }
        }
        
    @property
    def dangerous_apis(self) -> Set[str]:
        return set(self._dangerous_apis.keys())
        
    def is_dangerous_api(self, api_name: str) -> bool:
        return api_name in self._dangerous_apis
        
    def get_api_description(self, api_name: str) -> str:
        return self._dangerous_apis.get(api_name, {}).get('description', '未知的危险API')
        
    def get_api_threat_type(self, api_name: str) -> str:
        return self._dangerous_apis.get(api_name, {}).get('threat_type', 'UNKNOWN')
        
    def get_api_resource_type(self, api_name: str) -> str:
        return self._dangerous_apis.get(api_name, {}).get('resource_type', 'UNKNOWN')

class GoAPIChecker(APIChecker):
    """Go语言的API检查器"""
    def __init__(self):
        self._dangerous_apis = {
            # 命令执行 - 高风险
            'os/exec.Command': {
                'description': '执行系统命令，可能导致任意代码执行',
                'threat_type': 'COMMAND_EXECUTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'exec.Command': {
                'description': '执行系统命令，可能导致任意代码执行',
                'threat_type': 'COMMAND_EXECUTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'exec.CommandContext': {
                'description': '执行系统命令，可能导致任意代码执行',
                'threat_type': 'COMMAND_EXECUTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'os.StartProcess': {
                'description': '启动新进程，可能导致任意代码执行',
                'threat_type': 'COMMAND_EXECUTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            
            # 危险文件操作 - 高风险
            'os.Remove': {
                'description': '删除文件，可能导致数据丢失',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            'os.RemoveAll': {
                'description': '递归删除目录，可能导致数据丢失',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            
            # 网络请求 - 高风险
            'http.Get': {
                'description': '发送HTTP GET请求，可能导致数据泄露',
                'threat_type': 'NETWORK_REQUEST',
                'resource_type': 'NETWORK_RESOURCE'
            },
            'http.Post': {
                'description': '发送HTTP POST请求，可能导致数据泄露',
                'threat_type': 'NETWORK_REQUEST',
                'resource_type': 'NETWORK_RESOURCE'
            },
            'http.Client.Do': {
                'description': '执行HTTP请求，可能导致数据泄露',
                'threat_type': 'NETWORK_REQUEST',
                'resource_type': 'NETWORK_RESOURCE'
            },
            'net.Dial': {
                'description': '建立网络连接，可能导致数据泄露',
                'threat_type': 'NETWORK_REQUEST',
                'resource_type': 'NETWORK_RESOURCE'
            },
            'net.DialTimeout': {
                'description': '建立带超时的网络连接，可能导致数据泄露',
                'threat_type': 'NETWORK_REQUEST',
                'resource_type': 'NETWORK_RESOURCE'
            },
            
            # 不安全的反射 - 高风险
            'plugin.Open': {
                'description': '动态加载Go插件，可能导致任意代码执行',
                'threat_type': 'DYNAMIC_LOADING',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'reflect.Value.Call': {
                'description': '通过反射调用函数，可能导致任意代码执行',
                'threat_type': 'CODE_INJECTION',
                'resource_type': 'SYSTEM_RESOURCE'
            }
        }
        
    @property
    def dangerous_apis(self) -> Set[str]:
        return set(self._dangerous_apis.keys())
        
    def is_dangerous_api(self, api_name: str) -> bool:
        return api_name in self._dangerous_apis
        
    def get_api_description(self, api_name: str) -> str:
        return self._dangerous_apis.get(api_name, {}).get('description', '未知的危险API')
        
    def get_api_threat_type(self, api_name: str) -> str:
        return self._dangerous_apis.get(api_name, {}).get('threat_type', 'UNKNOWN')
        
    def get_api_resource_type(self, api_name: str) -> str:
        return self._dangerous_apis.get(api_name, {}).get('resource_type', 'UNKNOWN')

class JavaAPIChecker(APIChecker):
    """Java语言的API检查器"""
    def __init__(self):
        self._dangerous_apis = {
            'Runtime.exec': {
                'description': '执行系统命令，可能导致任意代码执行',
                'threat_type': 'COMMAND_EXECUTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'Runtime.getRuntime': {
                'description': '获取运行时对象，常用于执行系统命令',
                'threat_type': 'COMMAND_EXECUTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'ProcessBuilder': {
                'description': '执行系统命令，可能导致任意代码执行',
                'threat_type': 'COMMAND_EXECUTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'ProcessBuilder.start': {
                'description': '启动进程，可能导致任意代码执行',
                'threat_type': 'COMMAND_EXECUTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'System.load': {
                'description': '加载本地库，可能导致代码执行',
                'threat_type': 'DYNAMIC_LOADING',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'System.loadLibrary': {
                'description': '加载本地库，可能导致代码执行',
                'threat_type': 'DYNAMIC_LOADING',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'Class.forName': {
                'description': '动态加载类，可能导致代码执行',
                'threat_type': 'DYNAMIC_LOADING',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'ClassLoader.loadClass': {
                'description': '加载类，可能导致代码执行',
                'threat_type': 'DYNAMIC_LOADING',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'URLClassLoader.newInstance': {
                'description': '创建类加载器，可能导致代码执行',
                'threat_type': 'DYNAMIC_LOADING',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'Statement.execute': {
                'description': '执行SQL语句，需要注意SQL注入',
                'threat_type': 'DATABASE_OPERATION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'Statement.executeQuery': {
                'description': '执行SQL查询，需要注意SQL注入',
                'threat_type': 'DATABASE_OPERATION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'Statement.executeUpdate': {
                'description': '执行SQL更新，需要注意SQL注入',
                'threat_type': 'DATABASE_OPERATION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'PreparedStatement.execute': {
                'description': '执行SQL语句，需要确保正确参数化',
                'threat_type': 'DATABASE_OPERATION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'Connection.prepareStatement': {
                'description': '准备SQL语句，需要确保正确参数化',
                'threat_type': 'DATABASE_OPERATION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'File.delete': {
                'description': '删除文件，需要注意意外删除',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            'File.deleteOnExit': {
                'description': '程序退出时删除文件，需要注意意外删除',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            'FileInputStream': {
                'description': '文件输入流，需要注意路径穿越',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            'FileOutputStream': {
                'description': '文件输出流，需要注意路径穿越',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            'FileReader': {
                'description': '文件读取器，需要注意路径穿越',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            'FileWriter': {
                'description': '文件写入器，需要注意路径穿越',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            'Files.delete': {
                'description': '删除文件，需要注意意外删除',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            'Files.write': {
                'description': '写入文件，需要注意路径穿越',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            'Files.readAllBytes': {
                'description': '读取文件，需要注意路径穿越',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            'URL.openConnection': {
                'description': '打开URL连接，需要注意SSRF',
                'threat_type': 'NETWORK_REQUEST',
                'resource_type': 'NETWORK_RESOURCE'
            },
            'URL.openStream': {
                'description': '打开URL流，需要注意SSRF',
                'threat_type': 'NETWORK_REQUEST',
                'resource_type': 'NETWORK_RESOURCE'
            },
            'URLConnection.connect': {
                'description': '建立URL连接，需要注意SSRF',
                'threat_type': 'NETWORK_REQUEST',
                'resource_type': 'NETWORK_RESOURCE'
            },
            'HttpURLConnection': {
                'description': 'HTTP连接，需要注意SSRF',
                'threat_type': 'NETWORK_REQUEST',
                'resource_type': 'NETWORK_RESOURCE'
            },
            'HttpClient.send': {
                'description': '发送HTTP请求，需要注意SSRF',
                'threat_type': 'NETWORK_REQUEST',
                'resource_type': 'NETWORK_RESOURCE'
            },
            'ObjectInputStream.readObject': {
                'description': '对象反序列化，可能导致代码执行',
                'threat_type': 'DESERIALIZATION',
                'resource_type': 'MEMORY_RESOURCE'
            },
            'XMLDecoder': {
                'description': 'XML反序列化，可能导致代码执行',
                'threat_type': 'DESERIALIZATION',
                'resource_type': 'MEMORY_RESOURCE'
            },
            'Cipher.getInstance': {
                'description': '获取加密实例，需要注意使用安全的算法和模式',
                'threat_type': 'CRYPTO_WEAKNESS',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'MessageDigest.getInstance': {
                'description': '获取哈希算法实例，需要注意使用安全的算法',
                'threat_type': 'CRYPTO_WEAKNESS',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'KeyPairGenerator.getInstance': {
                'description': '获取密钥对生成器，需要注意使用安全的算法和参数',
                'threat_type': 'CRYPTO_WEAKNESS',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'SecureRandom.setSeed': {
                'description': '设置随机数种子，可能减弱随机性',
                'threat_type': 'INSECURE_RANDOM',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'System.setSecurityManager': {
                'description': '设置安全管理器，可能影响安全策略',
                'threat_type': 'PRIVILEGE_ESCALATION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'Policy.setPolicy': {
                'description': '设置安全策略，可能影响权限控制',
                'threat_type': 'PRIVILEGE_ESCALATION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'AccessController.doPrivileged': {
                'description': '执行特权操作，需要注意权限提升',
                'threat_type': 'PRIVILEGE_ESCALATION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'System.setProperty': {
                'description': '设置系统属性，可能影响程序行为',
                'threat_type': 'ENVIRONMENT_MANIPULATION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'System.getenv': {
                'description': '获取环境变量，可能包含敏感信息',
                'threat_type': 'ENVIRONMENT_MANIPULATION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'XPath.evaluate': {
                'description': '执行XPath查询，需要注意XPath注入',
                'threat_type': 'CODE_INJECTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'SAXParserFactory.newSAXParser': {
                'description': '创建XML解析器，需要注意XXE',
                'threat_type': 'XXE',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'DocumentBuilderFactory.newDocumentBuilder': {
                'description': '创建XML文档构建器，需要注意XXE',
                'threat_type': 'XXE',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'javax.script.ScriptEngine.eval': {
                'description': '执行脚本代码，可能导致代码注入',
                'threat_type': 'CODE_INJECTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'Thread.sleep': {
                'description': '线程休眠，可能用于时序攻击，需要谨慎使用',
                'threat_type': 'RESOURCE_EXHAUSTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'ThreadPoolExecutor': {
                'description': '线程池执行器，需要注意资源管理',
                'threat_type': 'RESOURCE_EXHAUSTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'File.createTempFile': {
                'description': '创建临时文件，需要注意权限和清理',
                'threat_type': 'INSECURE_TEMP_FILE',
                'resource_type': 'FILE_RESOURCE'
            }
        }
        
    @property
    def dangerous_apis(self) -> Set[str]:
        return set(self._dangerous_apis.keys())
        
    def is_dangerous_api(self, api_name: str) -> bool:
        return api_name in self._dangerous_apis
        
    def get_api_description(self, api_name: str) -> str:
        return self._dangerous_apis.get(api_name, {}).get('description', '未知的危险API')
        
    def get_api_threat_type(self, api_name: str) -> str:
        return self._dangerous_apis.get(api_name, {}).get('threat_type', 'UNKNOWN')
        
    def get_api_resource_type(self, api_name: str) -> str:
        return self._dangerous_apis.get(api_name, {}).get('resource_type', 'UNKNOWN')

class CppAPIChecker(APIChecker):
    """C/C++语言的API检查器"""
    def __init__(self):
        self._dangerous_apis = {
            # 命令执行 - 高风险
            'system': {
                'description': '执行系统命令，可能导致任意代码执行',
                'threat_type': 'COMMAND_EXECUTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'popen': {
                'description': '执行系统命令并获取输出，可能导致任意代码执行',
                'threat_type': 'COMMAND_EXECUTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'exec': {
                'description': '执行系统命令，可能导致任意代码执行',
                'threat_type': 'COMMAND_EXECUTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'execl': {
                'description': '执行系统命令，可能导致任意代码执行',
                'threat_type': 'COMMAND_EXECUTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'execlp': {
                'description': '执行系统命令，可能导致任意代码执行',
                'threat_type': 'COMMAND_EXECUTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'execle': {
                'description': '执行系统命令，可能导致任意代码执行',
                'threat_type': 'COMMAND_EXECUTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'execv': {
                'description': '执行系统命令，可能导致任意代码执行',
                'threat_type': 'COMMAND_EXECUTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'execvp': {
                'description': '执行系统命令，可能导致任意代码执行',
                'threat_type': 'COMMAND_EXECUTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'fork': {
                'description': '创建子进程，可能导致任意代码执行',
                'threat_type': 'COMMAND_EXECUTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'std::system': {
                'description': '执行系统命令，可能导致任意代码执行',
                'threat_type': 'COMMAND_EXECUTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            
            # 危险文件操作 - 高风险
            'remove': {
                'description': '文件删除，可能导致数据丢失',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            'unlink': {
                'description': '文件删除，可能导致数据丢失',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            'std::remove': {
                'description': '文件删除，可能导致数据丢失',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            'rmdir': {
                'description': '删除目录，可能导致数据丢失',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            
            # 网络操作 - 高风险
            'socket': {
                'description': '创建网络套接字，可能导致数据泄露',
                'threat_type': 'NETWORK_REQUEST',
                'resource_type': 'NETWORK_RESOURCE'
            },
            'connect': {
                'description': '建立网络连接，可能导致数据泄露',
                'threat_type': 'NETWORK_REQUEST',
                'resource_type': 'NETWORK_RESOURCE'
            },
            'recv': {
                'description': '接收网络数据，可能导致数据泄露',
                'threat_type': 'NETWORK_REQUEST',
                'resource_type': 'NETWORK_RESOURCE'
            },
            'send': {
                'description': '发送网络数据，可能导致数据泄露',
                'threat_type': 'NETWORK_REQUEST',
                'resource_type': 'NETWORK_RESOURCE'
            },
            'curl_easy_perform': {
                'description': '执行HTTP请求，可能导致数据泄露',
                'threat_type': 'NETWORK_REQUEST',
                'resource_type': 'NETWORK_RESOURCE'
            },
            
            # 代码执行 - 高风险
            'dlopen': {
                'description': '动态加载库，可能导致代码执行',
                'threat_type': 'DYNAMIC_LOADING',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'dlsym': {
                'description': '获取动态库中的符号，可能导致代码执行',
                'threat_type': 'DYNAMIC_LOADING',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'LoadLibrary': {
                'description': '加载动态链接库，可能导致代码执行',
                'threat_type': 'DYNAMIC_LOADING',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'CreateProcess': {
                'description': '创建进程，可能导致任意代码执行',
                'threat_type': 'COMMAND_EXECUTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'ShellExecute': {
                'description': '执行shell命令，可能导致任意代码执行',
                'threat_type': 'COMMAND_EXECUTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'WinExec': {
                'description': '执行程序，可能导致任意代码执行',
                'threat_type': 'COMMAND_EXECUTION',
                'resource_type': 'SYSTEM_RESOURCE'
            }
        }
        
    @property
    def dangerous_apis(self) -> Set[str]:
        return set(self._dangerous_apis.keys())
        
    def is_dangerous_api(self, api_name: str) -> bool:
        return api_name in self._dangerous_apis
        
    def get_api_description(self, api_name: str) -> str:
        return self._dangerous_apis.get(api_name, {}).get('description', '未知的危险API')
        
    def get_api_threat_type(self, api_name: str) -> str:
        return self._dangerous_apis.get(api_name, {}).get('threat_type', 'UNKNOWN')
        
    def get_api_resource_type(self, api_name: str) -> str:
        return self._dangerous_apis.get(api_name, {}).get('resource_type', 'UNKNOWN')

class CSharpAPIChecker(APIChecker):
    """C#语言的API检查器"""
    def __init__(self):
        self._dangerous_apis = {
            # 命令执行 - 高风险
            'Process.Start': {
                'description': '启动进程，可能导致任意代码执行',
                'threat_type': 'COMMAND_EXECUTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'ProcessStartInfo': {
                'description': '配置进程启动，可能导致任意代码执行',
                'threat_type': 'COMMAND_EXECUTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'System.Diagnostics.Process.Start': {
                'description': '启动进程，可能导致任意代码执行',
                'threat_type': 'COMMAND_EXECUTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            
            # 危险文件操作 - 高风险
            'File.Delete': {
                'description': '删除文件，可能导致数据丢失',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            'Directory.Delete': {
                'description': '删除目录，可能导致数据丢失',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            
            # 网络操作 - 高风险
            'WebClient.DownloadFile': {
                'description': '下载文件，可能导致数据泄露',
                'threat_type': 'NETWORK_REQUEST',
                'resource_type': 'NETWORK_RESOURCE'
            },
            'WebClient.DownloadString': {
                'description': '下载字符串，可能导致数据泄露',
                'threat_type': 'NETWORK_REQUEST',
                'resource_type': 'NETWORK_RESOURCE'
            },
            'HttpClient.GetAsync': {
                'description': '发送HTTP GET请求，可能导致数据泄露',
                'threat_type': 'NETWORK_REQUEST',
                'resource_type': 'NETWORK_RESOURCE'
            },
            'HttpClient.PostAsync': {
                'description': '发送HTTP POST请求，可能导致数据泄露',
                'threat_type': 'NETWORK_REQUEST',
                'resource_type': 'NETWORK_RESOURCE'
            },
            'Socket.Connect': {
                'description': '建立网络连接，可能导致数据泄露',
                'threat_type': 'NETWORK_REQUEST',
                'resource_type': 'NETWORK_RESOURCE'
            },

            # 代码执行 - 高风险
            'Assembly.Load': {
                'description': '加载程序集，可能导致任意代码执行',
                'threat_type': 'DYNAMIC_LOADING',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'Assembly.LoadFrom': {
                'description': '从路径加载程序集，可能导致任意代码执行',
                'threat_type': 'DYNAMIC_LOADING',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'Activator.CreateInstance': {
                'description': '动态创建对象，可能导致任意代码执行',
                'threat_type': 'DYNAMIC_LOADING',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'Type.GetType': {
                'description': '获取类型，常用于动态实例化',
                'threat_type': 'DYNAMIC_LOADING',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'Reflection': {
                'description': '反射操作，可能导致代码注入',
                'threat_type': 'CODE_INJECTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'CSharpCodeProvider': {
                'description': '动态编译C#代码，可能导致任意代码执行',
                'threat_type': 'CODE_INJECTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'Eval': {
                'description': '执行脚本代码，可能导致任意代码执行',
                'threat_type': 'CODE_INJECTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'XmlSerializer': {
                'description': 'XML序列化/反序列化，可能导致代码执行',
                'threat_type': 'DESERIALIZATION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'BinaryFormatter.Deserialize': {
                'description': '二进制反序列化，可能导致代码执行',
                'threat_type': 'DESERIALIZATION',
                'resource_type': 'SYSTEM_RESOURCE'
            }
        }
        
    @property
    def dangerous_apis(self) -> Set[str]:
        return set(self._dangerous_apis.keys())
        
    def is_dangerous_api(self, api_name: str) -> bool:
        return api_name in self._dangerous_apis
        
    def get_api_description(self, api_name: str) -> str:
        return self._dangerous_apis.get(api_name, {}).get('description', '未知的危险API')
        
    def get_api_threat_type(self, api_name: str) -> str:
        return self._dangerous_apis.get(api_name, {}).get('threat_type', 'UNKNOWN')

class PHPAPIChecker(APIChecker):
    """PHP语言的API检查器"""
    def __init__(self):
        self._dangerous_apis = {
            # 命令执行 - 高风险
            'exec': {
                'description': '执行系统命令，可能导致任意代码执行',
                'threat_type': 'COMMAND_EXECUTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'shell_exec': {
                'description': '执行系统命令并返回输出，可能导致任意代码执行',
                'threat_type': 'COMMAND_EXECUTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'system': {
                'description': '执行系统命令并输出结果，可能导致任意代码执行',
                'threat_type': 'COMMAND_EXECUTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'passthru': {
                'description': '执行系统命令并直接输出结果，可能导致任意代码执行',
                'threat_type': 'COMMAND_EXECUTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'popen': {
                'description': '打开进程文件指针，可能导致任意代码执行',
                'threat_type': 'COMMAND_EXECUTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'proc_open': {
                'description': '执行命令并打开进程资源，可能导致任意代码执行',
                'threat_type': 'COMMAND_EXECUTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'pcntl_exec': {
                'description': '执行程序，可能导致任意代码执行',
                'threat_type': 'COMMAND_EXECUTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            
            # 代码注入 - 高风险
            'eval': {
                'description': '执行PHP代码字符串，可能导致代码注入',
                'threat_type': 'CODE_INJECTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'assert': {
                'description': '检查断言，可用于执行PHP代码',
                'threat_type': 'CODE_INJECTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'create_function': {
                'description': '动态创建函数，可能导致代码注入',
                'threat_type': 'CODE_INJECTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'preg_replace': {
                'description': '使用/e修饰符时可执行代码，可能导致代码注入',
                'threat_type': 'CODE_INJECTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            
            # 文件操作 - 高风险，仅保留可能造成数据丢失的操作
            'unlink': {
                'description': '删除文件，可能导致数据丢失',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            'rmdir': {
                'description': '删除目录，可能导致数据丢失',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            
            # 网络请求 - 高风险
            'curl_exec': {
                'description': '执行cURL会话，可能导致数据泄露或SSRF攻击',
                'threat_type': 'NETWORK_REQUEST',
                'resource_type': 'NETWORK_RESOURCE'
            },
            'curl_multi_exec': {
                'description': '执行多个cURL会话，可能导致数据泄露或SSRF攻击',
                'threat_type': 'NETWORK_REQUEST',
                'resource_type': 'NETWORK_RESOURCE'
            },
            'fsockopen': {
                'description': '打开Socket连接，可能导致数据泄露或SSRF攻击',
                'threat_type': 'NETWORK_REQUEST',
                'resource_type': 'NETWORK_RESOURCE'
            },
            'pfsockopen': {
                'description': '打开持久Socket连接，可能导致数据泄露或SSRF攻击',
                'threat_type': 'NETWORK_REQUEST',
                'resource_type': 'NETWORK_RESOURCE'
            },
            'stream_socket_client': {
                'description': '创建客户端Socket，可能导致数据泄露或SSRF攻击',
                'threat_type': 'NETWORK_REQUEST',
                'resource_type': 'NETWORK_RESOURCE'
            },
            
            # XML外部实体 - 高风险
            'simplexml_load_file': {
                'description': '从文件加载XML，可能导致XXE攻击和数据泄露',
                'threat_type': 'XXE',
                'resource_type': 'FILE_RESOURCE'
            },
            'simplexml_load_string': {
                'description': '从字符串加载XML，可能导致XXE攻击和数据泄露',
                'threat_type': 'XXE',
                'resource_type': 'MEMORY_RESOURCE'
            },
            'DOMDocument::load': {
                'description': '加载XML文件，可能导致XXE攻击和数据泄露',
                'threat_type': 'XXE',
                'resource_type': 'FILE_RESOURCE'
            },
            'DOMDocument::loadXML': {
                'description': '加载XML字符串，可能导致XXE攻击和数据泄露',
                'threat_type': 'XXE',
                'resource_type': 'MEMORY_RESOURCE'
            },
            'xml_parse': {
                'description': '解析XML文档，可能导致XXE攻击和数据泄露',
                'threat_type': 'XXE',
                'resource_type': 'MEMORY_RESOURCE'
            },
            
            # 反序列化 - 高风险
            'unserialize': {
                'description': 'PHP对象反序列化，可能导致代码执行',
                'threat_type': 'DESERIALIZATION',
                'resource_type': 'MEMORY_RESOURCE'
            }
        }
        
    @property
    def dangerous_apis(self) -> Set[str]:
        return set(self._dangerous_apis.keys())
        
    def is_dangerous_api(self, api_name: str) -> bool:
        return api_name in self._dangerous_apis
        
    def get_api_description(self, api_name: str) -> str:
        return self._dangerous_apis.get(api_name, {}).get('description', '未知的危险API')
        
    def get_api_threat_type(self, api_name: str) -> str:
        return self._dangerous_apis.get(api_name, {}).get('threat_type', 'UNKNOWN')
        
    def get_api_resource_type(self, api_name: str) -> str:
        return self._dangerous_apis.get(api_name, {}).get('resource_type', 'UNKNOWN')

class RubyAPIChecker(APIChecker):
    """Ruby语言的API检查器"""
    def __init__(self):
        self._dangerous_apis = {
            # 命令执行 - 高风险
            'system': {
                'description': '执行系统命令，可能导致任意代码执行',
                'threat_type': 'COMMAND_EXECUTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'exec': {
                'description': '执行系统命令，可能导致任意代码执行',
                'threat_type': 'COMMAND_EXECUTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'spawn': {
                'description': '创建新进程，可能导致任意代码执行',
                'threat_type': 'COMMAND_EXECUTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'backtick': {
                'description': '执行命令并返回输出，可能导致任意代码执行',
                'threat_type': 'COMMAND_EXECUTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'popen': {
                'description': '打开进程管道，可能导致任意代码执行',
                'threat_type': 'COMMAND_EXECUTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            
            # 代码执行 - 高风险
            'eval': {
                'description': '执行Ruby代码字符串，可能导致代码注入',
                'threat_type': 'CODE_INJECTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'instance_eval': {
                'description': '在对象上下文中执行代码，可能导致代码注入',
                'threat_type': 'CODE_INJECTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'class_eval': {
                'description': '在类上下文中执行代码，可能导致代码注入',
                'threat_type': 'CODE_INJECTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'module_eval': {
                'description': '在模块上下文中执行代码，可能导致代码注入',
                'threat_type': 'CODE_INJECTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'send': {
                'description': '动态调用方法，可能导致代码注入',
                'threat_type': 'CODE_INJECTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            
            # 文件操作 - 高风险
            'File.delete': {
                'description': '删除文件，可能导致数据丢失',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            'File.unlink': {
                'description': '删除文件，可能导致数据丢失',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            'FileUtils.rm': {
                'description': '删除文件，可能导致数据丢失',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            'FileUtils.rm_r': {
                'description': '递归删除文件和目录，可能导致数据丢失',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            'FileUtils.rm_rf': {
                'description': '强制递归删除文件和目录，可能导致数据丢失',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            
            # 网络请求 - 高风险
            'Net::HTTP.get': {
                'description': '发送HTTP GET请求，可能导致SSRF攻击',
                'threat_type': 'NETWORK_REQUEST',
                'resource_type': 'NETWORK_RESOURCE'
            },
            'Net::HTTP.post': {
                'description': '发送HTTP POST请求，可能导致SSRF攻击',
                'threat_type': 'NETWORK_REQUEST',
                'resource_type': 'NETWORK_RESOURCE'
            },
            'open-uri': {
                'description': '打开远程URI，可能导致SSRF攻击',
                'threat_type': 'NETWORK_REQUEST',
                'resource_type': 'NETWORK_RESOURCE'
            },
            
            # 反序列化 - 高风险
            'Marshal.load': {
                'description': '反序列化Ruby对象，可能导致代码执行',
                'threat_type': 'DESERIALIZATION',
                'resource_type': 'MEMORY_RESOURCE'
            },
            'YAML.load': {
                'description': '加载YAML数据，可能导致代码执行',
                'threat_type': 'DESERIALIZATION',
                'resource_type': 'MEMORY_RESOURCE'
            },
            'JSON.load': {
                'description': '加载JSON数据，可能导致代码执行',
                'threat_type': 'DESERIALIZATION',
                'resource_type': 'MEMORY_RESOURCE'
            }
        }
        
    @property
    def dangerous_apis(self) -> Set[str]:
        return set(self._dangerous_apis.keys())
        
    def is_dangerous_api(self, api_name: str) -> bool:
        return api_name in self._dangerous_apis
        
    def get_api_description(self, api_name: str) -> str:
        return self._dangerous_apis.get(api_name, {}).get('description', '未知的危险API')
        
    def get_api_threat_type(self, api_name: str) -> str:
        return self._dangerous_apis.get(api_name, {}).get('threat_type', 'UNKNOWN')
        
    def get_api_resource_type(self, api_name: str) -> str:
        return self._dangerous_apis.get(api_name, {}).get('resource_type', 'UNKNOWN')

class SwiftAPIChecker(APIChecker):
    """Swift语言的API检查器"""
    def __init__(self):
        self._dangerous_apis = {
            # 命令执行 - 高风险
            'Process': {
                'description': '执行系统命令，可能导致任意代码执行',
                'threat_type': 'COMMAND_EXECUTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'NSTask': {
                'description': '执行系统命令，可能导致任意代码执行',
                'threat_type': 'COMMAND_EXECUTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'system': {
                'description': '执行系统命令，可能导致任意代码执行',
                'threat_type': 'COMMAND_EXECUTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            
            # 文件操作 - 高风险
            'FileManager.removeItem': {
                'description': '删除文件或目录，可能导致数据丢失',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            'FileManager.trashItem': {
                'description': '将文件或目录移动到废纸篓，可能导致数据丢失',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            'unlink': {
                'description': '删除文件，可能导致数据丢失',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            'remove': {
                'description': '删除文件，可能导致数据丢失',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            
            # 网络请求 - 高风险
            'URLSession.dataTask': {
                'description': '发起网络请求，可能导致数据泄露或SSRF攻击',
                'threat_type': 'NETWORK_REQUEST',
                'resource_type': 'NETWORK_RESOURCE'
            },
            'URLSession.downloadTask': {
                'description': '下载文件，可能导致数据泄露或SSRF攻击',
                'threat_type': 'NETWORK_REQUEST',
                'resource_type': 'NETWORK_RESOURCE'
            },
            'URLSession.uploadTask': {
                'description': '上传文件，可能导致数据泄露',
                'threat_type': 'NETWORK_REQUEST',
                'resource_type': 'NETWORK_RESOURCE'
            },
            'CFNetwork': {
                'description': '底层网络操作，可能导致数据泄露或SSRF攻击',
                'threat_type': 'NETWORK_REQUEST',
                'resource_type': 'NETWORK_RESOURCE'
            },
            
            # 动态代码执行 - 高风险
            'NSClassFromString': {
                'description': '动态加载类，可能导致代码注入',
                'threat_type': 'CODE_INJECTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'performSelector': {
                'description': '动态执行方法，可能导致代码注入',
                'threat_type': 'CODE_INJECTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'dlopen': {
                'description': '动态加载库，可能导致代码注入',
                'threat_type': 'CODE_INJECTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            
            # 不安全的数据处理 - 高风险
            'UnsafePointer': {
                'description': '不安全的指针操作，可能导致内存破坏',
                'threat_type': 'MEMORY_CORRUPTION',
                'resource_type': 'MEMORY_RESOURCE'
            },
            'UnsafeMutablePointer': {
                'description': '不安全的可变指针操作，可能导致内存破坏',
                'threat_type': 'MEMORY_CORRUPTION',
                'resource_type': 'MEMORY_RESOURCE'
            },
            'withUnsafePointer': {
                'description': '不安全的指针操作，可能导致内存破坏',
                'threat_type': 'MEMORY_CORRUPTION',
                'resource_type': 'MEMORY_RESOURCE'
            },
            'withUnsafeMutablePointer': {
                'description': '不安全的可变指针操作，可能导致内存破坏',
                'threat_type': 'MEMORY_CORRUPTION',
                'resource_type': 'MEMORY_RESOURCE'
            }
        }
        
    @property
    def dangerous_apis(self) -> Set[str]:
        return set(self._dangerous_apis.keys())
        
    def is_dangerous_api(self, api_name: str) -> bool:
        return api_name in self._dangerous_apis
        
    def get_api_description(self, api_name: str) -> str:
        return self._dangerous_apis.get(api_name, {}).get('description', '未知的危险API')
        
    def get_api_threat_type(self, api_name: str) -> str:
        return self._dangerous_apis.get(api_name, {}).get('threat_type', 'UNKNOWN')
        
    def get_api_resource_type(self, api_name: str) -> str:
        return self._dangerous_apis.get(api_name, {}).get('resource_type', 'UNKNOWN')

class KotlinAPIChecker(APIChecker):
    """Kotlin语言的API检查器"""
    def __init__(self):
        self._dangerous_apis = {
            # 命令执行 - 高风险
            'Runtime.exec': {
                'description': '执行系统命令，可能导致任意代码执行',
                'threat_type': 'COMMAND_EXECUTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'ProcessBuilder': {
                'description': '创建新进程，可能导致任意代码执行',
                'threat_type': 'COMMAND_EXECUTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'ProcessBuilder.start': {
                'description': '启动新进程，可能导致任意代码执行',
                'threat_type': 'COMMAND_EXECUTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            
            # 文件操作 - 高风险
            'File.delete': {
                'description': '删除文件，可能导致数据丢失',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            'File.deleteRecursively': {
                'description': '递归删除文件和目录，可能导致数据丢失',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            'Files.delete': {
                'description': '删除文件，可能导致数据丢失',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            'Files.deleteIfExists': {
                'description': '如果存在则删除文件，可能导致数据丢失',
                'threat_type': 'FILE_OPERATION',
                'resource_type': 'FILE_RESOURCE'
            },
            
            # 网络请求 - 高风险
            'URL.openConnection': {
                'description': '打开网络连接，可能导致SSRF攻击',
                'threat_type': 'NETWORK_REQUEST',
                'resource_type': 'NETWORK_RESOURCE'
            },
            'HttpURLConnection': {
                'description': '创建HTTP连接，可能导致SSRF攻击',
                'threat_type': 'NETWORK_REQUEST',
                'resource_type': 'NETWORK_RESOURCE'
            },
            'Socket': {
                'description': '创建Socket连接，可能导致SSRF攻击',
                'threat_type': 'NETWORK_REQUEST',
                'resource_type': 'NETWORK_RESOURCE'
            },
            
            # 反射和动态加载 - 高风险
            'Class.forName': {
                'description': '动态加载类，可能导致代码注入',
                'threat_type': 'CODE_INJECTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'ClassLoader.loadClass': {
                'description': '动态加载类，可能导致代码注入',
                'threat_type': 'CODE_INJECTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'Method.invoke': {
                'description': '动态调用方法，可能导致代码注入',
                'threat_type': 'CODE_INJECTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            
            # 序列化和反序列化 - 高风险
            'ObjectInputStream.readObject': {
                'description': '反序列化对象，可能导致代码执行',
                'threat_type': 'DESERIALIZATION',
                'resource_type': 'MEMORY_RESOURCE'
            },
            'XMLDecoder': {
                'description': '解码XML数据，可能导致代码执行',
                'threat_type': 'DESERIALIZATION',
                'resource_type': 'MEMORY_RESOURCE'
            },
            'Gson.fromJson': {
                'description': '解析JSON数据，可能导致代码执行',
                'threat_type': 'DESERIALIZATION',
                'resource_type': 'MEMORY_RESOURCE'
            },
            
            # 不安全的加密 - 高风险
            'MessageDigest.getInstance("MD5")': {
                'description': '使用不安全的MD5哈希算法',
                'threat_type': 'WEAK_ENCRYPTION',
                'resource_type': 'SYSTEM_RESOURCE'
            },
            'Cipher.getInstance("DES")': {
                'description': '使用不安全的DES加密算法',
                'threat_type': 'WEAK_ENCRYPTION',
                'resource_type': 'SYSTEM_RESOURCE'
            }
        }
        
    @property
    def dangerous_apis(self) -> Set[str]:
        return set(self._dangerous_apis.keys())
        
    def is_dangerous_api(self, api_name: str) -> bool:
        return api_name in self._dangerous_apis
        
    def get_api_description(self, api_name: str) -> str:
        return self._dangerous_apis.get(api_name, {}).get('description', '未知的危险API')
        
    def get_api_threat_type(self, api_name: str) -> str:
        return self._dangerous_apis.get(api_name, {}).get('threat_type', 'UNKNOWN')
        
    def get_api_resource_type(self, api_name: str) -> str:
        return self._dangerous_apis.get(api_name, {}).get('resource_type', 'UNKNOWN')

def get_checker(language: str) -> APIChecker:
    """根据语言获取对应的API检查器"""
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
        raise ValueError(f"不支持的语言: {language}")