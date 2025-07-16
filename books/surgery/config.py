# Surgery 配置文件
# 自动生成于 2025-07-16 19:06:27

# 页码范围和标签配置
page_ranges = [
    # 示例配置 - 请根据实际章节调整
    (1, 50, "Surgery::01第一章名"),
    (51, 100, "Surgery::02第二章名"), 
    (101, 150, "Surgery::03第三章名"),
    (151, 200, "Surgery::04第四章名"),
    (201, 250, "Surgery::05第五章名"),
    
    # 可以添加更多章节...
    # (251, 300, "Surgery::06第六章名"),
    # (301, 350, "Surgery::07附录名"),
]

# 图片文件夹名称 (相对于书籍目录)
IMAGE_FOLDER_NAME = 'images'

# 图片文件前缀 (用于Anki兼容的文件名)
IMAGE_PREFIX = 'surgery'

# 单词表文件名
TERMS_FILE = 'surgery_glossary.txt'

# 目录文件名
TOC_FILE = 'surgery_toc.txt'

# 输出文件名
OUTPUT_FILE = 'output_anki.txt'

# Anki卡组名称
DECK_NAME = "glossary::Surgery"

# 书籍名称（用于报告显示）
BOOK_NAME = "Surgery"

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
