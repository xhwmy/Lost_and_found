#!/usr/bin/env python3
"""
检测并修复所有模板文件中的CSRF令牌问题
确保每个POST表单只有一个CSRF令牌
"""

import os
import re

# 模板文件根目录
TEMPLATES_DIR = 'templates'

# 匹配POST表单的正则表达式
form_pattern = re.compile(r'<form\s+method="POST"[^>]*>', re.IGNORECASE)

# 匹配CSRF令牌的正则表达式
csrf_pattern = re.compile(r'<input\s+type="hidden"\s+name="csrf_token"\s+value="\{\{\s*csrf_token\(\)\s*\}\}"\s*/?>')

def fix_csrf_tokens_in_file(file_path):
    """修复单个文件中的CSRF令牌问题"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找所有POST表单
        forms = form_pattern.finditer(content)
        
        # 统计表单数量
        form_count = 0
        fixed_forms = 0
        
        for form_match in forms:
            form_count += 1
            form_start = form_match.start()
            
            # 查找表单结束位置
            # 简单实现：查找下一个</form>标签
            form_end = content.find('</form>', form_start)
            if form_end == -1:
                continue
            
            # 提取表单内容
            form_content = content[form_start:form_end]
            
            # 检查是否已有CSRF令牌
            csrf_matches = csrf_pattern.findall(form_content)
            
            if len(csrf_matches) == 0:
                # 缺少CSRF令牌，添加
                # 在<form>标签后添加CSRF令牌
                new_form_content = form_match.group(0) + '\n                    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">' + form_content[len(form_match.group(0)):]
                content = content.replace(form_content, new_form_content, 1)
                fixed_forms += 1
                print(f"✓ 添加CSRF令牌到 {file_path} 的表单 #{form_count}")
            elif len(csrf_matches) > 1:
                # 多个CSRF令牌，保留第一个，删除其他
                # 查找所有令牌位置
                token_positions = []
                for token_match in csrf_pattern.finditer(form_content):
                    token_positions.append((token_match.start(), token_match.end()))
                
                # 保留第一个，删除其他
                if token_positions:
                    # 从后往前删除，避免位置偏移
                    for start, end in reversed(token_positions[1:]):
                        form_content = form_content[:start] + form_content[end:]
                    
                    # 更新内容
                    content = content.replace(content[form_start:form_end], form_content, 1)
                    fixed_forms += 1
                    print(f"✓ 清理重复CSRF令牌到 {file_path} 的表单 #{form_count}")
        
        if fixed_forms > 0:
            # 写入修复后的内容
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        else:
            return False
            
    except Exception as e:
        print(f"✗ 处理文件 {file_path} 时出错: {e}")
        return False

def main():
    """主函数"""
    print('开始检测并修复CSRF令牌问题...')
    
    total_files = 0
    fixed_files = 0
    
    # 遍历所有模板文件
    for root, dirs, files in os.walk(TEMPLATES_DIR):
        for file in files:
            if file.endswith('.html'):
                total_files += 1
                file_path = os.path.join(root, file)
                if fix_csrf_tokens_in_file(file_path):
                    fixed_files += 1
    
    print(f'\n检测完成！')
    print(f'总文件数: {total_files}')
    print(f'修复文件数: {fixed_files}')
    
    # 验证修复结果
    print('\n验证修复结果...')
    
    # 再次检查所有文件
    for root, dirs, files in os.walk(TEMPLATES_DIR):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 查找所有POST表单
                    forms = form_pattern.finditer(content)
                    
                    for i, form_match in enumerate(forms, 1):
                        form_start = form_match.start()
                        form_end = content.find('</form>', form_start)
                        if form_end == -1:
                            continue
                        
                        form_content = content[form_start:form_end]
                        csrf_matches = csrf_pattern.findall(form_content)
                        
                        if len(csrf_matches) == 0:
                            print(f'✗ {file_path} 表单 #{i} 缺少CSRF令牌')
                        elif len(csrf_matches) > 1:
                            print(f'✗ {file_path} 表单 #{i} 存在多个CSRF令牌')
                        else:
                            pass  # 正常
                            
                except Exception as e:
                    print(f'✗ 验证 {file_path} 时出错: {e}')
    
    print('\n验证完成！')

if __name__ == '__main__':
    main()
