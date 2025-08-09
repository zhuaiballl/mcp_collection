import json
import os
import sys
import json
from pathlib import Path
from collections import defaultdict


def load_json_file(file_path):
    """加载 JSON 文件并返回数据"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValueError(f"文件 {file_path} 内容必须是数组格式")
        return data
    except Exception as e:
        print(f"加载文件 {file_path} 时出错: {str(e)}", file=sys.stderr)
        return []


def merge_projects(input_files, handle_missing_github_url='keep_separate', list_fields=['tags', 'categories'], multi_value_fields=['detail_url']):
    """
    合并多个 JSON 文件中的项目

    参数:
        input_files: 输入 JSON 文件路径列表
        handle_missing_github_url: 处理缺少 github_url 的项目的策略
            'keep_separate': 保留为单独的项目
            'ignore': 忽略这些项目
            'merge_by_name': 尝试通过 name 字段合并
        list_fields: 需要合并而非覆盖的列表类型字段
        multi_value_fields: 即使是非列表类型，也需要收集多个不同值的字段
    """
    # 使用字典存储合并后的项目，key 为 github_url
    projects_by_github_url = defaultdict(dict)
    # 存储缺少 github_url 的项目
    missing_github_url_projects = []

    for file_path in input_files:
        data = load_json_file(file_path)
        if not data:
            continue

        for item in data:
            # 修复：使用 str() 确保值不是 None
            github_url = str(item.get('github_url', '')).strip()

            if github_url:
                # 有 github_url，合并到对应项目
                existing_project = projects_by_github_url[github_url]
                
                # 处理每个字段
                for key, value in item.items():
                    # 对于列表类型的字段，执行合并去重
                    if key in list_fields and isinstance(value, list) and key in existing_project and isinstance(existing_project[key], list):
                        # 合并两个列表并去重
                        merged_list = list(set(existing_project[key] + value))
                        existing_project[key] = merged_list
                    # 对于需要收集多个值的字段
                    elif key in multi_value_fields:
                        if key not in existing_project:
                            # 如果字段不存在，初始化为列表
                            existing_project[key] = []
                        elif not isinstance(existing_project[key], list):
                            # 如果字段存在但不是列表，转换为列表
                            existing_project[key] = [existing_project[key]]
                        
                        # 添加新值（如果不存在）
                        if value not in existing_project[key]:
                            existing_project[key].append(value)
                    else:
                        # 其他字段直接覆盖
                        existing_project[key] = value
            else:
                # 没有 github_url，根据策略处理
                if handle_missing_github_url == 'keep_separate':
                    missing_github_url_projects.append(item)
                elif handle_missing_github_url == 'merge_by_name':
                    name = item.get('name', '').strip()
                    if name:
                        # 使用 name 作为临时键
                        name_key = f"__name__{name}"
                        existing_project = projects_by_github_url[name_key]
                        
                        # 处理每个字段
                        for key, value in item.items():
                            # 对于列表类型的字段，执行合并去重
                            if key in list_fields and isinstance(value, list) and key in existing_project and isinstance(existing_project[key], list):
                                merged_list = list(set(existing_project[key] + value))
                                existing_project[key] = merged_list
                            # 对于需要收集多个值的字段
                            elif key in multi_value_fields:
                                if key not in existing_project:
                                    existing_project[key] = []
                                elif not isinstance(existing_project[key], list):
                                    existing_project[key] = [existing_project[key]]
                                
                                if value not in existing_project[key]:
                                    existing_project[key].append(value)
                            else:
                                # 其他字段直接覆盖
                                existing_project[key] = value
                    else:
                        # 既没有 github_url 也没有 name，无法合并，添加到缺失列表
                        missing_github_url_projects.append(item)
                # 'ignore' 策略下不做任何处理

    # 转换为列表
    merged_projects = list(projects_by_github_url.values())

    # 添加缺少 github_url 的项目（如果策略不是 ignore）
    if handle_missing_github_url != 'ignore':
        merged_projects.extend(missing_github_url_projects)

    return merged_projects


def main():
    if len(sys.argv) < 3:
        print("用法: python merge_json_by_github_url.py <输出文件> <输入文件1> [输入文件2] ...")
        print("选项:")
        print("  --handle-missing-url <strategy>  处理缺少 github_url 的项目的策略")
        print("                                  'keep_separate': 保留为单独的项目 (默认)")
        print("                                  'ignore': 忽略这些项目")
        print("                                  'merge_by_name': 尝试通过 name 字段合并")
        print("  --list-fields <fields>           指定需要合并而非覆盖的列表字段，用逗号分隔")
        print("                                  默认: 'tags,categories'")
        print("  --multi-value-fields <fields>    指定需要收集多个不同值的字段，用逗号分隔")
        print("                                  默认: 'detail_url'")
        sys.exit(1)

    # 解析命令行参数
    output_file = sys.argv[1]
    input_files = []
    handle_missing_github_url = 'keep_separate'
    list_fields = ['tags', 'categories']
    multi_value_fields = ['detail_url']

    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == '--handle-missing-url' and i + 1 < len(sys.argv):
            handle_missing_github_url = sys.argv[i + 1]
            if handle_missing_github_url not in ['keep_separate', 'ignore', 'merge_by_name']:
                print(f"错误: 无效的策略 '{handle_missing_github_url}'")
                sys.exit(1)
            i += 2
        elif sys.argv[i] == '--list-fields' and i + 1 < len(sys.argv):
            list_fields = [field.strip() for field in sys.argv[i + 1].split(',')]
            i += 2
        elif sys.argv[i] == '--multi-value-fields' and i + 1 < len(sys.argv):
            multi_value_fields = [field.strip() for field in sys.argv[i + 1].split(',')]
            i += 2
        else:
            input_files.append(sys.argv[i])
            i += 1

    if not input_files:
        print("错误: 至少需要一个输入文件")
        sys.exit(1)

    # 检查输入文件是否存在
    for file_path in input_files:
        if not os.path.exists(file_path):
            print(f"错误: 输入文件 '{file_path}' 不存在")
            sys.exit(1)

    # 合并项目
    merged_projects = merge_projects(input_files, handle_missing_github_url, list_fields, multi_value_fields)

    # 写入输出文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(merged_projects, f, ensure_ascii=False, indent=2)

    print(f"成功合并 {len(input_files)} 个文件中的项目")
    print(f"合并后共有 {len(merged_projects)} 个项目")
    print(f"输出文件: {output_file}")


if __name__ == '__main__':
    main()