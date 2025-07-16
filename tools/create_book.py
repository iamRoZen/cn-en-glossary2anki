"""
快速创建书籍项目脚本 - tools目录版本

功能：
- 放置在tools文件夹下，在根目录/books/下创建书籍项目
- 生成空白配置和数据文件
- 支持批量创建
- 自动验证项目结构
- 支持PDF处理相关参数

项目结构:
project_root/
├── tools/
│   └── create_book.py    (本脚本)
└── books/                (创建的书籍项目位置)
    ├── cell_biology/
    ├── molecular_biology/
    └── ...

作者：RoZen
版本：2.1.0
"""

import os
from datetime import datetime
from pathlib import Path

VERSION = "2.1.0"

def create_config_file(book_name: str, book_title: str = "") -> str:
    """生成基础配置文件"""
    if not book_title:
        # 将下划线转换为空格，首字母大写
        book_title = book_name.replace('_', ' ').title()
    
    return f'''# {book_title} 配置文件
# 自动生成于 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

# 页码范围和标签配置, 相关prompt在tools/page_ranges_prompt.md
page_ranges = [
    # 示例配置 - 请根据实际章节调整
    (1, 50, "{book_title}::01第一章名"),
    (51, 100, "{book_title}::02第二章名"), 
    (101, 150, "{book_title}::03第三章名"),
    (151, 200, "{book_title}::04第四章名"),
    (201, 250, "{book_title}::05第五章名"),
    
    # 可以添加更多章节...
    # (251, 300, "{book_title}::06第六章名"),
    # (301, 350, "{book_title}::07附录名"),
]

# 图片文件夹名称 (相对于书籍目录)
IMAGE_FOLDER_NAME = 'images'

# 图片文件前缀 (用于Anki兼容的文件名)
IMAGE_PREFIX = '{book_name}'

# 单词表文件名
TERMS_FILE = '{book_name}_glossary.txt'

# 目录文件名
TOC_FILE = '{book_name}_toc.txt'

# 输出文件名
OUTPUT_FILE = 'output_anki.txt'

# Anki卡组名称
DECK_NAME = "glossary::{book_title}"

# 书籍名称（用于报告显示）
BOOK_NAME = "{book_title}"

# ========== PDF 处理相关配置 (可选) ==========
# 如果设置了以下参数，PDF处理器可以直接使用这些配置

# PDF源文件路径 (留空则需要手动指定)
PDF_PATH = ""

# 目录页码范围 (提取为txt) - 格式: (起始页, 结束页)
TOC_PAGES = None  # 例如: (1, 10)

# 单词表页码范围 (提取为txt) - 格式: (起始页, 结束页)  
GLOSSARY_PAGES = None  # 例如: (280, 300)

# 索引页码范围 (提取为png图片) - 格式: (起始页, 结束页)
INDEX_PAGES = None  # 例如: (1, 250)

# 是否自动提取图片
AUTO_EXTRACT_IMAGES = True
'''


def create_book_project(book_name: str, book_title: str = "") -> bool:
    """创建书籍项目"""
    try:
        # 获取项目根目录（从tools目录回退一级）
        script_dir = Path(__file__).parent.absolute()
        project_root = script_dir.parent
        books_dir = project_root / "books"
        
        # 创建books目录（如果不存在）
        books_dir.mkdir(exist_ok=True)
        
        # 创建项目文件夹
        project_dir = books_dir / book_name
        
        if project_dir.exists():
            print("已存在")
            return False
        
        # 创建主文件夹
        project_dir.mkdir()
        
        # 创建images子文件夹
        images_dir = project_dir / "images"
        images_dir.mkdir()
        
        # 生成配置文件
        config_path = project_dir / "config.py"
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(create_config_file(book_name, book_title))
        
        # 生成空白词汇表文件
        glossary_path = project_dir / f"{book_name}_glossary.txt"
        with open(glossary_path, 'w', encoding='utf-8') as f:
            f.write("# 词汇表文件\n")
            f.write("# 格式：中文术语 英文术语 页码\n")
            f.write("# 示例：细胞膜 cell membrane 77\n\n")
        
        # 生成空白目录文件
        toc_path = project_dir / f"{book_name}_toc.txt"
        with open(toc_path, 'w', encoding='utf-8') as f:
            f.write("# 目录文件\n")
            f.write("# 从PDF提取的目录信息\n\n")
        
        print("✅")
        return True
        
    except Exception as e:
        print(f"❌ ({e})")
        return False

def validate_book_name(name: str) -> bool:
    """验证书籍名称是否为合法格式（纯英文+下划线+数字）"""
    import re
    # 允许字母开头，包含字母、数字、下划线
    return bool(re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', name))

def check_project_structure():
    """检查项目结构是否正确"""
    script_dir = Path(__file__).parent.absolute()
    project_root = script_dir.parent
    
    print("🔍 项目结构检查:")
    print(f"  脚本位置: {script_dir}")
    print(f"  项目根目录: {project_root}")
    print(f"  目标books目录: {project_root / 'books'}")
    
    # 检查是否在正确的位置
    if script_dir.name != "tools":
        print("⚠️ 警告: 脚本不在tools目录下")
        return False
    
    return True

def list_existing_books():
    """列出已存在的书籍项目"""
    script_dir = Path(__file__).parent.absolute()
    project_root = script_dir.parent
    books_dir = project_root / "books"
    
    if not books_dir.exists():
        print("📁 books目录不存在，将在创建项目时自动创建")
        return []
    
    existing_books = []
    for item in books_dir.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            config_file = item / "config.py"
            status = "✅" if config_file.exists() else "⚠️"
            existing_books.append((item.name, status))
    
    if existing_books:
        print("📚 已存在的书籍项目:")
        for book_name, status in existing_books:
            print(f"  {status} {book_name}")
    else:
        print("📁 books目录为空")
    
    return [book[0] for book in existing_books]

def interactive_create():
    """交互式创建模式"""
    print("\n🎯 交互式创建模式")
    print("-" * 30)
    
    while True:
        book_name = input("书籍标识 (纯英文+下划线): ").strip()
        
        if not book_name:
            print("❌ 请输入书籍标识")
            continue
        
        if not validate_book_name(book_name):
            print("❌ 格式错误，请使用纯英文+下划线，例如: cell_biology")
            continue
        
        break
    
    book_title = input(f"书籍显示名称 [默认: {book_name.replace('_', ' ').title()}]: ").strip()
    if not book_title:
        book_title = book_name.replace('_', ' ').title()
    
    print(f"\n📋 确认创建:")
    print(f"  标识: {book_name}")
    print(f"  名称: {book_title}")
    
    confirm = input("确认创建? (y/N): ").strip().lower()
    if confirm in ['y', 'yes']:
        print(f"📖 创建 {book_name}: ", end="")
        return create_book_project(book_name, book_title)
    else:
        print("❌ 取消创建")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print(f"    快速创建书籍项目工具 v{VERSION}")
    print("=" * 60)
    
    # 检查项目结构
    if not check_project_structure():
        print("\n❌ 项目结构检查失败")
        print("请确保脚本位于 project_root/tools/ 目录下")
        return
    
    # 列出已存在的项目
    print()
    existing_books = list_existing_books()
    
    print("\n" + "=" * 60)
    print("创建模式选择:")
    print("1. 批量创建 (空格分隔多个书籍标识)")
    print("2. 交互式创建 (逐步输入信息)")
    print("0. 退出")
    
    choice = input("\n选择模式 (1/2/0): ").strip()
    
    if choice == "0":
        print("退出程序")
        return
    
    elif choice == "2":
        success = interactive_create()
        if success:
            print("✅ 项目创建成功")
            print("\n💡 下一步建议:")
            print("1. 编辑 config.py 文件，配置牌组和PDF相关参数")
            print("2. 运行 python tools/pdf_setup.py 进行PDF处理")
        return
    
    elif choice == "1":
        print("\n📝 批量创建模式")
        print("输入书籍标识 (纯英文+下划线, 空格分隔):")
        print("示例: cell_biology molecular_biology biochemistry")
        
        input_line = input("\n书籍标识: ").strip()
        
        if not input_line:
            print("❌ 未输入任何书籍标识")
            return
    else:
        print("❌ 无效选择")
        return
    
    # 处理批量创建
    book_names = input_line.split()
    
    # 验证书籍名称格式
    valid_names = []
    invalid_names = []
    existing_names = []
    
    for name in book_names:
        if not validate_book_name(name):
            invalid_names.append(name)
        elif name in existing_books:
            existing_names.append(name)
        else:
            valid_names.append(name)
    
    # 显示验证结果
    if invalid_names:
        print(f"❌ 无效格式: {', '.join(invalid_names)}")
        print("   格式要求: 纯英文+下划线，例如 cell_biology")
    
    if existing_names:
        print(f"⚠️ 已存在: {', '.join(existing_names)}")
    
    if not valid_names:
        print("❌ 没有可创建的有效书籍标识")
        return
    
    if invalid_names or existing_names:
        print(f"继续创建 {len(valid_names)} 个新项目...")
    
    print(f"\n🚀 开始批量创建 {len(valid_names)} 个项目...")
    
    success_count = 0
    for book_name in valid_names:
        print(f"📖 {book_name}: ", end="")
        if create_book_project(book_name):
            success_count += 1
    
    print(f"\n📊 创建完成: {success_count}/{len(valid_names)} 个项目创建成功")
    
    if success_count > 0:
        print("\n💡 下一步建议:")
        print("1. 编辑各项目的 config.py 文件，设置牌组和PDF相关参数")
        print("2. 运行 python tools/pdf_setup.py 进行PDF处理")

if __name__ == '__main__':
    main()