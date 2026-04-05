#!/usr/bin/env python3
"""
专门修复models.py文件BOM问题的脚本
"""

# 直接读取并修复models.py文件
with open('models.py', 'rb') as f:
    content = f.read()

# 移除BOM和所有前导空白字符
content = content.lstrip(b'\xef\xbb\xbf')
content = content.lstrip()

# 写入修复后的内容
with open('models.py', 'wb') as f:
    f.write(content)

print('已成功修复models.py文件的BOM问题！')

# 验证修复结果
with open('models.py', 'rb') as f:
    first_bytes = f.read(10)

print('文件开头10个字节:', first_bytes)
print('是否包含BOM:', first_bytes.startswith(b'\xef\xbb\xbf'))
