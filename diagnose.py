import sys
import os

# 写入诊断信息到文件
with open('diagnosis.txt', 'w') as f:
    f.write('=== 系统诊断信息 ===\n')
    f.write(f'Python版本: {sys.version}\n')
    f.write(f'Python路径: {sys.path}\n')
    f.write(f'当前目录: {os.getcwd()}\n')
    f.write(f'目录文件: {os.listdir(".")}\n')
    
    # 检查依赖项
    f.write('\n=== 依赖项检查 ===\n')
    try:
        import flask
        f.write(f'Flask: {flask.__version__}\n')
    except Exception as e:
        f.write(f'Flask: {e}\n')
    
    try:
        import sqlalchemy
        f.write(f'SQLAlchemy: {sqlalchemy.__version__}\n')
    except Exception as e:
        f.write(f'SQLAlchemy: {e}\n')
    
    try:
        import pymysql
        f.write(f'PyMySQL: {pymysql.__version__}\n')
    except Exception as e:
        f.write(f'PyMySQL: {e}\n')
    
    try:
        import cryptography
        f.write(f'Cryptography: {cryptography.__version__}\n')
    except Exception as e:
        f.write(f'Cryptography: {e}\n')
    
    # 检查文件权限
    f.write('\n=== 文件权限检查 ===\n')
    for file in ['app.py', 'config.py', 'models.py', 'user_views.py', 'admin_views.py', 'utils.py']:
        if os.path.exists(file):
            f.write(f'{file}: 存在\n')
        else:
            f.write(f'{file}: 不存在\n')

print('诊断完成，请查看diagnosis.txt文件获取详细信息。')
