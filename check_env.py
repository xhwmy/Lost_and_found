import sys
import os

print("Python version:", sys.version)
print("Python path:", sys.path)
print("Current directory:", os.getcwd())

try:
    import flask
    print("Flask version:", flask.__version__)
except ImportError as e:
    print("Flask import error:", e)

try:
    import sqlalchemy
    print("SQLAlchemy version:", sqlalchemy.__version__)
except ImportError as e:
    print("SQLAlchemy import error:", e)

try:
    import pymysql
    print("PyMySQL version:", pymysql.__version__)
except ImportError as e:
    print("PyMySQL import error:", e)

print("Environment variables:")
for key, value in os.environ.items():
    if 'SECRET' in key or 'DATABASE' in key:
        print(f"{key}: {value}")
