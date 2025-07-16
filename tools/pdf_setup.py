"""
PDF快速处理脚本 - 根据config.py参数提取内容

功能：
- 读取books/项目名/config.py中的PDF参数
- 提取目录内容到txt文件
- 提取单词表内容到txt文件  
- 提取图片页面到png文件
- 最简实现，专注核心功能
- 支持批处理多个项目

依赖：
- PyMuPDF (pip install PyMuPDF)

作者：RoZen
版本：1.0.0
"""

import os
import sys
import fitz  # PyMuPDF
from pathlib import Path
import importlib.util
from datetime import datetime

VERSION = "1.0.0"

def load_config(project_path: Path):
    """动态加载指定项目的config.py文件"""
    config_file = project_path / "config.py"
    
    if not config_file.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_file}")
    
    # 动态加载配置模块
    spec = importlib.util.spec_from_file_location("config", config_file)
    config = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config)
    
    return config

def extract_text_from_pages(pdf_path: str, start_page: int, end_page: int) -> str:
    """从PDF指定页码范围提取文本"""
    doc = fitz.open(pdf_path)
    text_content = []
    
    # 页码转换为0-based索引
    start_idx = start_page - 1
    end_idx = end_page - 1
    
    print(f"    提取页码 {start_page}-{end_page} 的文本...")
    
    for page_num in range(start_idx, min(end_idx + 1, len(doc))):
        page = doc[page_num]
        text = page.get_text()
        text_content.append(f"{text}\n")
    
    doc.close()
    return "\n".join(text_content)

def extract_images_from_pages(pdf_path: str, start_page: int, end_page: int, 
                             output_dir: Path, image_prefix: str) -> int:
    """从PDF指定页码范围提取图片"""
    doc = fitz.open(pdf_path)
    
    # 页码转换为0-based索引
    start_idx = start_page - 1
    end_idx = end_page - 1
    
    print(f"    提取页码 {start_page}-{end_page} 的图片...")
    
    image_count = 0
    # 从0001开始编号，不管实际页码
    image_index = 1
    
    for page_num in range(start_idx, min(end_idx + 1, len(doc))):
        page = doc[page_num]
        
        # 将页面渲染为图片
        mat = fitz.Matrix(2.0, 2.0)  # 2x缩放以获得更好的质量
        pix = page.get_pixmap(matrix=mat)
        
        # 生成文件名 - 使用独立的索引计数器
        image_filename = f"{image_prefix}_{image_index:04d}.png"
        image_path = output_dir / image_filename
        
        # 保存图片
        pix.save(str(image_path))
        pix = None  # 释放内存
        image_count += 1
        image_index += 1  # 递增索引
        
        if image_count % 10 == 0:
            print(f"      已处理 {image_count} 张图片...")
    
    doc.close()
    return image_count

def process_pdf(project_name: str):
    """处理指定项目的PDF"""
    
    # 获取项目路径
    script_dir = Path(__file__).parent.absolute()
    project_root = script_dir.parent
    books_dir = project_root / "books"
    project_path = books_dir / project_name
    
    if not project_path.exists():
        print(f"❌ 项目不存在: {project_path}")
        return False
    
    try:
        # 加载配置
        print(f"📖 加载项目配置: {project_name}")
        config = load_config(project_path)
        
        # 检查PDF路径
        pdf_path = getattr(config, 'PDF_PATH', '')
        if not pdf_path:
            print("❌ PDF_PATH 未配置")
            return False
        
        if not os.path.exists(pdf_path):
            print(f"❌ PDF文件不存在: {pdf_path}")
            return False
        
        print(f"📄 PDF文件: {pdf_path}")
        
        # 获取配置参数
        toc_pages = getattr(config, 'TOC_PAGES', None)
        glossary_pages = getattr(config, 'GLOSSARY_PAGES', None)
        index_pages = getattr(config, 'INDEX_PAGES', None)
        auto_extract_images = getattr(config, 'AUTO_EXTRACT_IMAGES', True)
        
        # 文件名配置
        toc_file = getattr(config, 'TOC_FILE', f'{project_name}_toc.txt')
        terms_file = getattr(config, 'TERMS_FILE', f'{project_name}_glossary.txt')
        image_prefix = getattr(config, 'IMAGE_PREFIX', project_name)
        
        success_count = 0
        
        # 1. 提取目录
        if toc_pages:
            print(f"📑 提取目录 (页码 {toc_pages[0]}-{toc_pages[1]}):")
            try:
                toc_text = extract_text_from_pages(pdf_path, toc_pages[0], toc_pages[1])
                toc_path = project_path / toc_file
                
                with open(toc_path, 'w', encoding='utf-8') as f:
                    f.write(f"# 目录文件 - {project_name}\n")
                    f.write(f"# 提取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"# 源文件: {pdf_path}\n")
                    f.write(f"# 页码范围: {toc_pages[0]}-{toc_pages[1]}\n\n")
                    f.write(toc_text)
                
                print(f"    ✅ 目录已保存: {toc_path}")
                success_count += 1
            except Exception as e:
                print(f"    ❌ 目录提取失败: {e}")
        else:
            print("⏭️  跳过目录提取 (TOC_PAGES 未配置)")
        
        # 2. 提取单词表
        if glossary_pages:
            print(f"📚 提取单词表 (页码 {glossary_pages[0]}-{glossary_pages[1]}):")
            try:
                glossary_text = extract_text_from_pages(pdf_path, glossary_pages[0], glossary_pages[1])
                glossary_path = project_path / terms_file
                
                with open(glossary_path, 'w', encoding='utf-8') as f:
                    f.write(glossary_text)
                
                print(f"    ✅ 单词表已保存: {glossary_path}")
                success_count += 1
            except Exception as e:
                print(f"    ❌ 单词表提取失败: {e}")
        else:
            print("⏭️  跳过单词表提取 (GLOSSARY_PAGES 未配置)")
        
        # 3. 提取图片
        if index_pages and auto_extract_images:
            print(f"🖼️  提取图片 (页码 {index_pages[0]}-{index_pages[1]}):")
            try:
                images_dir = project_path / "images"
                images_dir.mkdir(exist_ok=True)
                
                image_count = extract_images_from_pages(
                    pdf_path, index_pages[0], index_pages[1], 
                    images_dir, image_prefix
                )
                
                print(f"    ✅ 图片已保存: {image_count} 张，目录: {images_dir}")
                success_count += 1
            except Exception as e:
                print(f"    ❌ 图片提取失败: {e}")
        else:
            reason = "INDEX_PAGES 未配置" if not index_pages else "AUTO_EXTRACT_IMAGES 已禁用"
            print(f"⏭️  跳过图片提取 ({reason})")
        
        # 总结
        print(f"\n📊 处理完成: {success_count} 个任务成功")
        
        if success_count > 0:
            print("\n💡 下一步建议:")
            print("1. 检查并编辑提取的txt文件，确保格式正确")
            print("2. 运行主脚本生成Anki卡片: python main.py " + project_name)
        
        return success_count > 0
        
    except Exception as e:
        print(f"❌ 处理失败: {e}")
        return False

def list_available_projects():
    """列出可用的项目"""
    script_dir = Path(__file__).parent.absolute()
    project_root = script_dir.parent
    books_dir = project_root / "books"
    
    if not books_dir.exists():
        print("📁 books目录不存在")
        return []
    
    projects = []
    for item in books_dir.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            config_file = item / "config.py"
            if config_file.exists():
                projects.append(item.name)
    
    return projects

def batch_process_all():
    """批处理所有项目"""
    print("\n🔄 批处理模式 - 处理所有项目")
    print("-" * 40)
    
    projects = list_available_projects()
    
    if not projects:
        print("❌ 没有找到可用的项目")
        return False
    
    print(f"📚 找到 {len(projects)} 个项目:")
    for project in projects:
        print(f"  - {project}")
    
    confirm = input(f"\n确认处理所有 {len(projects)} 个项目? (y/N): ").strip().lower()
    if confirm != 'y':
        print("⏹️  已取消批处理")
        return False
    
    print("\n开始批处理...")
    print("=" * 60)
    
    success_projects = []
    failed_projects = []
    
    for i, project in enumerate(projects, 1):
        print(f"\n[{i}/{len(projects)}] 处理项目: {project}")
        print("-" * 40)
        
        try:
            success = process_pdf(project)
            if success:
                success_projects.append(project)
            else:
                failed_projects.append(project)
        except Exception as e:
            print(f"❌ 项目处理异常: {e}")
            failed_projects.append(project)
        
        print("-" * 40)
    
    # 批处理总结
    print("\n" + "=" * 60)
    print("📊 批处理完成总结:")
    print(f"  ✅ 成功: {len(success_projects)} 个项目")
    if success_projects:
        for project in success_projects:
            print(f"     - {project}")
    
    print(f"  ❌ 失败: {len(failed_projects)} 个项目")
    if failed_projects:
        for project in failed_projects:
            print(f"     - {project}")
    
    print("=" * 60)
    
    return len(success_projects) > 0

def interactive_mode():
    """交互式模式"""
    print("\n🎯 交互式PDF处理模式")
    print("-" * 40)
    
    projects = list_available_projects()
    
    if not projects:
        print("❌ 没有找到可用的项目")
        print("请先运行 python tools/create_book.py 创建项目")
        return False
    
    print("📚 可用项目:")
    for i, project in enumerate(projects, 1):
        print(f"  {i}. {project}")
    print(f"  {len(projects) + 1}. 批处理所有项目")
    
    while True:
        try:
            choice = input(f"\n选择项目 (1-{len(projects) + 1}) 或输入项目名: ").strip()
            
            if choice.isdigit():
                idx = int(choice) - 1
                if idx == len(projects):  # 选择批处理
                    return batch_process_all()
                elif 0 <= idx < len(projects):
                    project_name = projects[idx]
                    break
                else:
                    print("❌ 无效的选择")
                    continue
            else:
                if choice in projects:
                    project_name = choice
                    break
                else:
                    print("❌ 项目不存在")
                    continue
        except ValueError:
            print("❌ 请输入有效的数字或项目名")
            continue
    
    print(f"\n🚀 开始处理项目: {project_name}")
    return process_pdf(project_name)

def main():
    """主函数"""
    print("=" * 60)
    print(f"    PDF快速处理工具 v{VERSION}")
    print("=" * 60)
    
    # 检查依赖
    try:
        import fitz
    except ImportError:
        print("❌ 缺少依赖库 PyMuPDF")
        print("请安装: pip install PyMuPDF")
        return
    
    # 命令行参数处理
    if len(sys.argv) > 1:
        if sys.argv[1] in ['--batch', '-b', 'batch', 'all']:
            # 批处理模式
            success = batch_process_all()
            if not success:
                sys.exit(1)
        else:
            # 处理指定项目
            project_name = sys.argv[1]
            print(f"🚀 处理项目: {project_name}")
            success = process_pdf(project_name)
            if not success:
                sys.exit(1)
    else:
        # 交互式模式
        success = interactive_mode()
        if not success:
            sys.exit(1)

if __name__ == '__main__':
    main()
