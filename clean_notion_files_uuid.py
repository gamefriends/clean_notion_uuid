# -*- coding: utf-8 -*-

import os
import re
import urllib.parse

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
    seen_headings = {}
    last_heading_level = 0
    
    for line in lines:
        # 处理尾随空格：保留两个或删除所有
        if line.rstrip() != line:
            if line.endswith('  '):  # 保留两个空格
                line = line.rstrip() + '  '
            else:  # 删除所有尾随空格
                line = line.rstrip()
        
        # 处理无序列表缩进，将4空格缩进改为2空格
        if re.match(r'^(\s{4})+[*+-]', line):
            spaces = len(re.match(r'^(\s*)', line).group())
            line = ' ' * (spaces // 2) + line.lstrip()
        
        # 处理标题层级问题
        if line.startswith('#'):
            level = len(re.match(r'^#+', line).group())
            if level - last_heading_level > 1:  # 如果层级跳跃超过1
                line = '#' * (last_heading_level + 1) + line[level:]
            last_heading_level = len(re.match(r'^#+', line).group())
        
        # 处理MD024: 处理重复标题
        if line.startswith('#'):
            heading_text = line.lstrip('#').strip()
            if heading_text in seen_headings:
                count = seen_headings[heading_text]
                line = line.rstrip() + f' {count}'
                seen_headings[heading_text] += 1
            else:
                seen_headings[heading_text] = 2
        
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
            
        # 处理标题尾部标点
        if line.startswith('#'):
            line = re.sub(r'[：:;,!?。，！？]+\s*$', '', line)
        
        cleaned_lines.append(line)
    
    # 处理文件末尾空行
    # 1. 先移除所有尾部空行
    while cleaned_lines and not cleaned_lines[-1].strip():
        cleaned_lines.pop()
    
    # 2. 添加一个空行
    cleaned_lines.append('')
    
    return cleaned_lines

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

def decode_url_filename(filename):
    """将URL编码的文件名解码为正常的中文文件名"""
    try:
        # 解码URL编码的文件名
        decoded = urllib.parse.unquote(filename)
        return decoded
    except Exception as e:
        print(f'解码文件名失败 {filename}: {str(e)}')
        return filename

def update_markdown_links(content, rename_map):
    """更新Markdown文件中的链接引用"""
    # 更新Markdown链接语法 [text](url)
    for old_name, new_name in rename_map.items():
        # 处理URL编码的情况
        encoded_old = urllib.parse.quote(old_name)
        encoded_new = urllib.parse.quote(new_name)
        
        # 替换普通链接
        content = content.replace(f']({old_name})', f']({new_name})')
        content = content.replace(f']({encoded_old})', f']({new_name})')
        
        # 替换图片链接
        content = content.replace(f'![]({old_name})', f'![]({new_name})')
        content = content.replace(f'![]({encoded_old})', f'![]({new_name})')
    
    return content

def process_file(file_path, rename_map=None):
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
            # 如果有重命名映射，更新文件中的链接
            if rename_map:
                cleaned_content = update_markdown_links(cleaned_content, rename_map)
        
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
            # 先清理UUID
            new_name = clean_notion_filename(name)
            # 然后解码URL编码
            new_name = decode_url_filename(new_name)
            new_path = os.path.join(root, new_name)
            
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
            # 先清理UUID
            new_name = clean_notion_filename(name)
            # 然后解码URL编码
            new_name = decode_url_filename(new_name)
            new_path = os.path.join(root, new_name)
            
            if old_path != new_path:
                try:
                    os.rename(old_path, new_path)
                    rename_map[name] = new_name
                    print(f'重命名目录: {name} -> {new_name}')
                except Exception as e:
                    print(f'重命名目录失败 {name}: {str(e)}')
    
    # 重命名完成后，更新所有markdown文件中的引用
    for root, _, files in os.walk(path):
        for name in files:
            if name.endswith('.md'):
                file_path = os.path.join(root, name)
                process_file(file_path, rename_map)
    
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
