#!/usr/bin/env python3
"""
下载校园失物招领系统的ER图和用例图
"""

import requests
import os

def download_image(url, filename):
    """下载图片"""
    print(f"正在下载 {filename}...")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()  # 检查是否有错误
        with open(filename, 'wb') as f:
            f.write(response.content)
        print(f"✅ 下载成功：{filename}")
        return True
    except Exception as e:
        print(f"❌ 下载失败：{e}")
        return False

def main():
    """主函数"""
    # ER图下载链接
    er_url = "https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=Campus%20Lost%20and%20Found%20System%20ER%20Diagram%2C%20entities%20User%2C%20LostItem%2C%20FoundItem%2C%20Claim%2C%20Comments%2C%20Favorites%2C%20Forum%2C%20Admin&image_size=landscape_16_9"
    
    # 用例图下载链接
    use_case_url = "https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=Campus%20Lost%20and%20Found%20System%20Use%20Case%20Diagram%2C%20actors%20User%2C%20Admin%2C%20System%2C%20use%20cases%20Register%2C%20Login%2C%20Post%2C%20Search%2C%20Claim%2C%20Manage&image_size=landscape_16_9"
    
    # 下载图片
    er_success = download_image(er_url, "er_diagram.png")
    use_case_success = download_image(use_case_url, "use_case_diagram.png")
    
    # 检查下载结果
    if er_success and use_case_success:
        print("\n🎉 所有图表下载完成！")
        print("\n生成的文件：")
        print(f"- ER图：{os.path.abspath('er_diagram.png')}")
        print(f"- 用例图：{os.path.abspath('use_case_diagram.png')}")
        print("\n请在文件资源管理器中找到这些图片并查看。")
    else:
        print("\n❌ 部分图表下载失败，请检查网络连接后重试。")

if __name__ == "__main__":
    main()
