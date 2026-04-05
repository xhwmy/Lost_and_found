#!/usr/bin/env python3
"""
检查所有管理员路由和模板的潜在问题
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_admin_routes_and_templates():
    print("🔍 扫描管理员界面所有潜在问题...")
    
    # 读取admin_views.py文件
    admin_views_path = project_root / "admin_views.py"
    if not admin_views_path.exists():
        print(f"❌ 文件不存在: {admin_views_path}")
        return
    
    with open(admin_views_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("\n📋 发现的管理员路由:")
    
    # 查找所有管理员路由
    import re
    
    # 匹配 @admin_bp.route 装饰器
    route_pattern = r'@admin_bp\.route\s*\(\s*[\'"](.*?)[\'"]\s*\)'
    routes = re.findall(route_pattern, content)
    
    for route in routes:
        print(f"  - {route}")
    
    print("\n🔧 检查路由函数定义:")
    
    # 查找所有路由函数定义
    function_pattern = r'def\s+(\w+)\s*\(\s*\)\s*:'
    functions = re.findall(function_pattern, content)
    
    for func in functions:
        # 检查函数是否包含render_template调用
        func_def_pos = content.find(f'def {func}(')
        if func_def_pos != -1:
            # 找到下一个函数定义或文件末尾
            next_func_pos = len(content)
            for next_func in functions:
                if next_func != func:
                    temp_pos = content.find(f'def {next_func}(', func_def_pos)
                    if temp_pos != -1 and temp_pos < next_func_pos:
                        next_func_pos = temp_pos
            
            func_content = content[func_def_pos:next_func_pos]
            
            # 检查render_template调用
            template_match = re.search(r'render_template\s*\(\s*[\'"]([^\'"]+)[\'"]', func_content)
            if template_match:
                template = template_match.group(1)
                template_path = project_root / "templates" / template
                
                print(f"  {func}() -> {template}")
                
                # 检查模板文件是否存在
                if not template_path.exists():
                    print(f"    ❌ 模板文件不存在: {template_path}")
                else:
                    print(f"    ✅ 模板文件存在: {template_path}")
                    
                    # 检查模板内容中的变量
                    with open(template_path, 'r', encoding='utf-8') as tf:
                        template_content = tf.read()
                        
                        # 查找模板中使用的变量
                        var_pattern = r'\{\{\s*(\w+(?:\.\w+)*)\s*\}\}'
                        template_vars = re.findall(var_pattern, template_content)
                        
                        # 查找模板中使用的循环变量
                        for_pattern = r'\{\%\s*for\s+(\w+)\s+in\s+\w+(?:\.\w+)*\s*\%\}'
                        loop_vars = re.findall(for_pattern, template_content)
                        
                        # 查找条件变量
                        if_pattern = r'\{\%\s*if\s+(\w+(?:\.\w+)*)\s*\%\}'
                        condition_vars = re.findall(if_pattern, template_content)
                        
                        all_vars = set(template_vars + loop_vars + condition_vars)
                        
                        # 过滤掉内置属性和方法
                        filtered_vars = []
                        for var in all_vars:
                            parts = var.split('.')
                            if len(parts) > 1:
                                base_var = parts[0]
                                if base_var not in ['item', 'user', 'log', 'comment', 'ban', 'claim', 'post', 'reply']:
                                    filtered_vars.append(base_var)
                            else:
                                if var not in ['loop', 'true', 'false', 'none', 'request', 'session', 'g', 'config']:
                                    filtered_vars.append(var)
                        
                        if filtered_vars:
                            print(f"    📝 模板中使用的变量: {filtered_vars}")
                            
                            # 检查这些变量是否在函数中传递
                            passed_vars = []
                            render_matches = re.findall(r'render_template\s*\([^)]*\)', func_content)
                            for render_match in render_matches:
                                # 提取传递给render_template的变量
                                var_matches = re.findall(r'(\w+)\s*=\s*\w+', render_match)
                                passed_vars.extend(var_matches)
                            
                            missing_vars = [var for var in filtered_vars if var not in passed_vars]
                            if missing_vars:
                                print(f"    ⚠️  模板中使用但未传递的变量: {missing_vars}")
                            else:
                                print(f"    ✅ 所有变量都已正确传递")
    
    print("\n📁 检查所有管理员模板文件...")
    
    # 检查admin目录下的所有模板文件
    admin_template_dir = project_root / "templates" / "admin"
    if admin_template_dir.exists():
        for template_file in admin_template_dir.glob("*.html"):
            print(f"\n📄 检查模板: {template_file.name}")
            
            with open(template_file, 'r', encoding='utf-8') as tf:
                template_content = tf.read()
                
                # 检查是否有未定义的变量使用
                # 查找所有{{ variable }}模式
                var_pattern = r'\{\{\s*(\w+(?:\.\w+)*)\s*\}\}'
                template_vars = re.findall(var_pattern, template_content)
                
                # 查找所有{% for variable in ... %}模式
                for_pattern = r'\{\%\s*for\s+(\w+)\s+in\s+\w+(?:\.\w+)*\s*\%\}'
                loop_vars = re.findall(for_pattern, template_content)
                
                # 查找所有{% if variable %}模式
                if_pattern = r'\{\%\s*if\s+(\w+(?:\.\w+)*)\s*\%\}'
                condition_vars = re.findall(if_pattern, template_content)
                
                all_vars = set(template_vars + loop_vars + condition_vars)
                
                # 过滤掉内置变量
                filtered_vars = []
                for var in all_vars:
                    parts = var.split('.')
                    if len(parts) > 1:
                        base_var = parts[0]
                        if base_var not in ['item', 'user', 'log', 'comment', 'ban', 'claim', 'post', 'reply', 'loop']:
                            filtered_vars.append(base_var)
                    else:
                        if var not in ['loop', 'true', 'false', 'none', 'request', 'session', 'g', 'config', 'url_for', 'csrf_token']:
                            filtered_vars.append(var)
                
                if filtered_vars:
                    print(f"   使用的变量: {filtered_vars}")

if __name__ == "__main__":
    check_admin_routes_and_templates()