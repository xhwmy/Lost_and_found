#!/usr/bin/env python3
"""
修复 UTF-8 BOM 问题的脚本
"""

import os

def remove_bom(file_path):
    """移除文件开头的 UTF-8 BOM"""
    try:
        with open(file_path, 'rb') as f:
            content = f.read()
        
        # 检查是否有 BOM
        if content.startswith(b'\xef\xbb\xbf'):
            # 移除 BOM
            content = content[3:]
            with open(file_path, 'wb') as f:
                f.write(content)
            print(f"已修复文件: {file_path}")
        else:
            print(f"文件无 BOM: {file_path}")
            
    except Exception as e:
        print(f"修复文件 {file_path} 时出错: {e}")

# 修复 models.py 文件
remove_bom('models.py')

# 检查并修复其他可能有 BOM 的 Python 文件
python_files = [
    'app.py',
    'admin_views.py', 
    'user_views.py',
    'utils.py',
    'config.py'
]

for file in python_files:
    if os.path.exists(file):
        remove_bom(file)

print("\n修复完成！")
