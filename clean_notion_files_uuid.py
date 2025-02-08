# -*- coding: utf-8 -*-

import os
import re

# 添加在文件开头的配置部分
IGNORE_DIRS = {
    # 版本控制
    '.git',
    '.svn',
    '.hg',  # Mercurial
    '.bzr',  # Bazaar
    
    # 开发工具
    'node_modules',
    '__pycache__',
    '.idea',
    '.vscode',
    '.vs',  # Visual Studio
    'vendor',  # PHP/Composer
    'bin',
    'obj',  # .NET
    
    # 构建和缓存
    'build',
    'dist',
    '.cache',
    '.npm',
    '.yarn',
    
    # macOS
    '.DS_Store',
    '.Spotlight-V100',
    '.Trashes',
    '.AppleDouble',
    '.LSOverride',
    
    # Windows
    '$RECYCLE.BIN',
    'System Volume Information',
    'Thumbs.db',
    'ehthumbs.db',
    'Desktop.ini',
    
    # Linux
    '.Trash-*',
    
    # 临时文件
    'tmp',
    'temp',
    '.tmp',
    '.temp'
}

# 添加要处理的文本文件扩展名
TEXT_FILE_EXTENSIONS = {
    # 常见文本文件
    '.txt', '.md', '.markdown',
    # 网页文件
    '.html', '.htm', '.css', '.js',
    # 配置文件
    '.json', '.yaml', '.yml', '.xml', '.ini', '.conf',
    # 源代码文件
    '.py', '.java', '.c', '.cpp', '.h', '.cs', '.php',
    '.rb', '.pl', '.sh', '.bat', '.ps1',
    # 其他文本文件
    '.csv', '.tsv', '.sql'
}

def clean_notion_filename(filename):
    # 匹配 Notion 的 UUID 模式 (32位十六进制数字，可能带有空格和破折号)
    uuid_pattern = r'\s+[a-fA-F0-9]{8}[-\s]?[a-fA-F0-9]{4}[-\s]?[a-fA-F0-9]{4}[-\s]?[a-fA-F0-9]{4}[-\s]?[a-fA-F0-9]{12}'
    
    # 移除 UUID
    clean_name = re.sub(uuid_pattern, '', filename)
    
    # 清理可能残留的多余空格
    clean_name = clean_name.strip()
    
    return clean_name

def clean_file_content(content):
    # 匹配文件内容中的 UUID 引用
    uuid_pattern = r'\s+[a-fA-F0-9]{8}[-\s]?[a-fA-F0-9]{4}[-\s]?[a-fA-F0-9]{4}[-\s]?[a-fA-F0-9]{4}[-\s]?[a-fA-F0-9]{12}'
    
    # 清理内容中的 UUID
    clean_content = re.sub(uuid_pattern, '', content)
    return clean_content

def clean_markdown_content(content):
    """清理markdown内容中的lint问题，只处理有问题的行"""
    lines = content.splitlines()
    cleaned_lines = []
    
    for line in lines:
        # 处理MD026: 只处理以冒号结尾的标题
        if line.startswith('#') and line.rstrip().endswith(':'):
            line = line.rstrip().rstrip(':')
            
        # 处理MD009: 只处理有单个尾随空格的行
        if line.endswith(' ') and not line.endswith('  '):
            line = line.rstrip()
            
        # 处理MD034: 处理裸URL和邮箱
        # 匹配邮箱地址
        if re.search(r'[\w\.-]+@[\w\.-]+\.\w+', line):
            line = re.sub(r'([\w\.-]+@[\w\.-]+\.\w+)', r'<\1>', line)
            
        # 匹配http(s)链接
        if re.search(r'(?<![\[\(<])(https?://\S+)(?![\]>\)])', line):
            line = re.sub(r'(?<![\[\(<])(https?://\S+)(?![\]>\)])', r'<\1>', line)
            
        cleaned_lines.append(line)
    
    # 处理MD047: 只在末尾没有换行符时添加
    result = '\n'.join(cleaned_lines)
    if not result.endswith('\n'):
        result += '\n'
        
    return result

def is_text_file(file_path):
    """检查是否为文本文件"""
    # 检查文件扩展名
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in TEXT_FILE_EXTENSIONS:
        return False
        
    # 可选：进一步检查文件内容是否为文本
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            f.read(1024)  # 尝试读取开头的一些字节
        return True
    except UnicodeDecodeError:
        return False

def process_file(file_path):
    """处理单个文件"""
    # 只处理文本文件
    if not is_text_file(file_path):
        return
        
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 清理UUID
        cleaned_content = clean_file_content(content)
        
        # 处理markdown lint问题
        if file_path.endswith('.md'):
            cleaned_content = clean_markdown_content(cleaned_content)
        
        # 只在内容发生变化时写入
        if content != cleaned_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(cleaned_content)
            print(f'已清理文件: {file_path}')
            
    except Exception as e:
        print(f'处理文件失败 {file_path}: {str(e)}')

def rename_files_and_dirs(path):
    rename_map = {}
    
    for root, dirs, files in os.walk(path, topdown=True):
        # 修改dirs列表来跳过不需要遍历的目录
        # 1. 跳过配置的忽略目录
        # 2. 跳过所有以点开头的隐藏目录
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith('.')]
        
        # 处理文件，跳过隐藏文件和系统文件
        for name in files:
            if name.startswith('.') or name in {
                'Thumbs.db', 
                '.DS_Store', 
                'desktop.ini'
            }:
                continue
            old_path = os.path.join(root, name)
            new_name = clean_notion_filename(name)
            new_path = os.path.join(root, new_name)
            
            # 先处理文件内容
            process_file(old_path)
            
            if old_path != new_path:
                try:
                    os.rename(old_path, new_path)
                    rename_map[name] = new_name
                    print(f'重命名文件: {name} -> {new_name}')
                except Exception as e:
                    print(f'重命名文件失败 {name}: {str(e)}')
        
        # 处理目录
        for name in dirs:
            if name.startswith('.'):  # 跳过隐藏目录
                continue
            old_path = os.path.join(root, name)
            new_name = clean_notion_filename(name)
            new_path = os.path.join(root, new_name)
            
            if old_path != new_path:
                try:
                    os.rename(old_path, new_path)
                    rename_map[name] = new_name
                    print(f'重命名目录: {name} -> {new_name}')
                except Exception as e:
                    print(f'重命名目录失败 {name}: {str(e)}')
    
    return rename_map

if __name__ == '__main__':
    # 获取当前目录
    current_dir = os.getcwd()
    
    # 确认是否继续
    print(f'即将处理目录: {current_dir}')
    confirm = input('确认要继续吗？(y/n): ')
    
    if confirm.lower() == 'y':
        rename_map = rename_files_and_dirs(current_dir)
        print('处理完成！')
        
        # 显示重命名统计
        if rename_map:
            print('\n重命名统计:')
            for old_name, new_name in rename_map.items():
                print(f'{old_name} -> {new_name}')
    else:
        print('操作已取消') 