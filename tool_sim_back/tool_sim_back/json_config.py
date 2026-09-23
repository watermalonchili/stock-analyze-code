import json
import os
import shutil

# 动态获取当前脚本所在目录的绝对路径（项目根目录）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# JSON文件路径 - 放在项目根目录下
JSON_FILE_PATH = os.path.join(BASE_DIR, 'modeListSelf.json')


def init_json_file():
    """初始化JSON文件"""
    if not os.path.exists(JSON_FILE_PATH):
        with open(JSON_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=2)


def read_json_data():
    """读取JSON文件数据"""
    init_json_file()
    with open(JSON_FILE_PATH, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def write_json_data(data):
    """写入数据到JSON文件"""
    with open(JSON_FILE_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def move_images_to_new_folder(new_folder_name):
    # 【核心修改】：使用相对路径，自动适配 E:\gitClone... 或 D:\self...
    base_path = os.path.join(BASE_DIR, "public")  # public 目录
    source_path = os.path.join(BASE_DIR, "public", "savepng")  # 源图片目录

    print(f"📂 正在准备移动图片:")
    print(f"   源路径: {source_path}")

    # 确保基础路径存在
    if not os.path.exists(base_path):
        os.makedirs(base_path)

    # 新建文件夹的完整路径 (例如 public/CUSTOM_1772347...)
    new_folder_path = os.path.join(base_path, new_folder_name)

    if os.path.exists(new_folder_path):
        print(f"   ⚠️ 文件夹已存在: {new_folder_name}")
    else:
        os.makedirs(new_folder_path)
        print(f"   🆕 已创建模式专属目录: {new_folder_path}")

    # 检查源目录是否存在
    if not os.path.exists(source_path):
        print(f"   ❌ 错误: 源目录 {source_path} 不存在，无法移动图片！")
        return

    image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')
    moved_count = 0

    # 遍历源文件夹
    files = os.listdir(source_path)
    print(f"   🔎 扫描到 {len(files)} 个文件...")

    for filename in files:
        if filename.lower().endswith(image_extensions):
            source_file = os.path.join(source_path, filename)
            target_file = os.path.join(new_folder_path, filename)

            try:
                # 移动文件
                shutil.move(source_file, target_file)
                # print(f"      -> 已移动: {filename}")
                moved_count += 1
            except Exception as e:
                print(f"      ❌ 移动 {filename} 失败: {str(e)}")

    print(f"✅ 图片整理完成: 共移动 {moved_count} 张图片至 {new_folder_name}")
