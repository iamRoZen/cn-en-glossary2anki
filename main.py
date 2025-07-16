"""
中英文词汇Anki卡片生成器 - 批量处理器

功能：
- 批量处理多个中英文词汇书籍
- 生成详细的处理报告
- 支持选择性处理和命令行参数

适用范围：任何包含"中文 英文 页码"格式的纯文本文件

作者：RoZen
版本：1.0.0
"""

import os
import sys
import importlib.util
import json
from datetime import datetime
from typing import Dict, List, Tuple
import argparse

# 导入核心模块
try:
    from core import extract_and_tag_terms, write_anki_output
except ImportError:
    # 如果在项目根目录运行，尝试从子目录导入
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from core import extract_and_tag_terms, write_anki_output

# 应用版本
VERSION = "1.0.0"

class ProcessingReport:
    """处理报告类"""
    
    def __init__(self):
        self.books_processed = []
        self.books_failed = []
        self.total_successful_entries = 0
        self.total_failed_entries = 0
        self.processing_start_time = datetime.now()
        self.detailed_stats = {}
    
    def add_book_result(self, book_name: str, success: bool, successful_count: int = 0, 
                       failed_count: int = 0, failure_reasons: Dict = None):
        """添加书籍处理结果"""
        if success:
            self.books_processed.append(book_name)
            self.total_successful_entries += successful_count
            self.total_failed_entries += failed_count
            
            self.detailed_stats[book_name] = {
                'successful': successful_count,
                'failed': failed_count,
                'success_rate': successful_count / (successful_count + failed_count) * 100 if (successful_count + failed_count) > 0 else 0,
                'failure_reasons': failure_reasons or {}
            }
        else:
            self.books_failed.append(book_name)
    
    def generate_summary_report(self) -> str:
        """生成汇总报告"""
        processing_time = datetime.now() - self.processing_start_time
        
        report = []
        report.append("=" * 80)
        report.append(f"        中英文词汇批量处理工具 {VERSION} - 最终报告")
        report.append("=" * 80)
        report.append(f"📅 处理时间: {self.processing_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"⏱️  总耗时: {processing_time}")
        report.append("")
        
        # 总体统计
        total_books = len(self.books_processed) + len(self.books_failed)
        report.append("📊 总体统计:")
        report.append(f"  📚 处理书籍总数: {total_books}")
        report.append(f"  ✅ 成功处理: {len(self.books_processed)} 本 ({len(self.books_processed)/total_books*100:.1f}%)")
        report.append(f"  ❌ 处理失败: {len(self.books_failed)} 本 ({len(self.books_failed)/total_books*100:.1f}%)")
        report.append(f"  📝 成功提取条目: {self.total_successful_entries:,}")
        report.append(f"  ⚠️  失败条目: {self.total_failed_entries:,}")
        
        if self.total_successful_entries + self.total_failed_entries > 0:
            overall_success_rate = self.total_successful_entries / (self.total_successful_entries + self.total_failed_entries) * 100
            report.append(f"  🎯 总体成功率: {overall_success_rate:.1f}%")
        
        report.append("")
        
        # 成功处理的书籍详情
        if self.books_processed:
            report.append("✅ 成功处理的书籍:")
            
            # 按成功率排序
            sorted_books = sorted(self.detailed_stats.items(), 
                                key=lambda x: x[1]['success_rate'], reverse=True)
            
            for book_name, stats in sorted_books:
                success_rate = stats['success_rate']
                total_entries = stats['successful'] + stats['failed']
                
                status_icon = "🏆" if success_rate >= 95 else "✅" if success_rate >= 90 else "⚠️"
                report.append(f"  {status_icon} {book_name}: {stats['successful']:,}/{total_entries:,} ({success_rate:.1f}%)")
        
        # 失败的书籍
        if self.books_failed:
            report.append("")
            report.append("❌ 处理失败的书籍:")
            for book_name in self.books_failed:
                report.append(f"  • {book_name}")
        
        # 改进建议
        report.append("")
        report.append("💡 改进建议:")
        
        if self.books_failed:
            report.append("  📁 对于失败的书籍:")
            report.append("    - 检查配置文件是否存在且格式正确")
            report.append("    - 确认词汇表文件是否存在")
            report.append("    - 检查文件编码是否为UTF-8")
        
        low_success_books = [name for name, stats in self.detailed_stats.items() 
                           if stats['success_rate'] < 85]
        if low_success_books:
            report.append("  📈 对于成功率较低的书籍:")
            report.append("    - 检查词汇表文件的格式和质量")
            report.append("    - 考虑手动清理明显的错误条目")
            report.append("    - 优化页码范围配置")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def save_detailed_report(self, output_path: str):
        """保存详细报告到文件"""
        detailed_report = {
            'processing_time': self.processing_start_time.isoformat(),
            'version': VERSION,
            'summary': {
                'total_books': len(self.books_processed) + len(self.books_failed),
                'successful_books': len(self.books_processed),
                'failed_books': len(self.books_failed),
                'total_successful_entries': self.total_successful_entries,
                'total_failed_entries': self.total_failed_entries
            },
            'book_details': self.detailed_stats,
            'failed_books': self.books_failed
        }
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(detailed_report, f, ensure_ascii=False, indent=2)
            print(f"📄 详细报告已保存: {output_path}")
        except Exception as e:
            print(f"⚠️  保存详细报告失败: {e}")

def load_config_from_file(config_path: str):
    """动态加载配置文件"""
    try:
        spec = importlib.util.spec_from_file_location("config", config_path)
        config_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config_module)
        return config_module
    except Exception as e:
        print(f"❌ 配置文件加载失败: {e}")
        return None

def write_failed_entries(failed_entries: List[str], output_path: str, book_name: str):
    """将失败条目写入文件"""
    if not failed_entries:
        return
    
    # 分析失败原因
    failure_analysis = {}
    for entry in failed_entries:
        if '] >' in entry:
            reason = entry.split('] >')[0].replace('[', '').strip()
            if reason not in failure_analysis:
                failure_analysis[reason] = 0
            failure_analysis[reason] += 1
        else:
            if '未知原因' not in failure_analysis:
                failure_analysis['未知原因'] = 0
            failure_analysis['未知原因'] += 1
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# {book_name} - 处理失败条目分析报告\n")
            f.write(f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# 应用版本: {VERSION}\n")
            f.write(f"# 失败条目总数: {len(failed_entries)}\n")
            f.write("#" + "="*70 + "\n\n")
            
            # 失败原因统计
            f.write("## 失败原因统计\n")
            f.write("-" * 30 + "\n")
            for reason, count in sorted(failure_analysis.items(), key=lambda x: x[1], reverse=True):
                percentage = count / len(failed_entries) * 100
                f.write(f"{reason}: {count} 条 ({percentage:.1f}%)\n")
            f.write("\n")
            
            # 详细失败条目
            f.write("## 详细失败条目\n")
            f.write("-" * 30 + "\n")
            for i, entry in enumerate(failed_entries, 1):
                f.write(f"{i:04d}. {entry}\n")
            
            f.write(f"\n# 总计: {len(failed_entries)} 条失败条目\n")
            
            # 改进建议
            f.write("\n## 改进建议\n")
            f.write("-" * 30 + "\n")
            if "内容被过滤" in failure_analysis:
                f.write("• 内容被过滤: 这些通常是索引页面或无意义内容，过滤是正常的\n")
            if "内容中不含中文字符" in failure_analysis:
                f.write("• 纯英文内容: 考虑在词汇表中添加对应的中文翻译\n")
            if "中英文分离失败" in failure_analysis:
                f.write("• 分离失败: 检查条目格式，可能需要手动调整\n")
        
        print(f"📄 失败条目分析报告已保存: {output_path}")
        
    except Exception as e:
        print(f"⚠️  保存失败条目文件时出错: {e}")

def process_single_book(book_folder: str, report: ProcessingReport) -> bool:
    """处理单个书籍文件夹"""
    print(f"\n{'='*60}")
    print(f"开始处理: {os.path.basename(book_folder)}")
    print(f"{'='*60}")
    
    book_name = os.path.basename(book_folder)
    
    # 检查配置文件
    config_file = os.path.join(book_folder, 'config.py')
    if not os.path.exists(config_file):
        print(f"❌ 错误：未找到配置文件 '{config_file}'")
        report.add_book_result(book_name, False)
        return False
    
    # 加载配置
    config = load_config_from_file(config_file)
    if not config:
        report.add_book_result(book_name, False)
        return False
    
    try:
        # 提取配置信息
        page_ranges = config.page_ranges
        image_folder_name = os.path.join(book_folder, config.IMAGE_FOLDER_NAME)
        image_prefix = config.IMAGE_PREFIX
        terms_file = os.path.join(book_folder, config.TERMS_FILE)
        output_file = os.path.join(book_folder, config.OUTPUT_FILE)
        deck_name = config.DECK_NAME
        book_display_name = config.BOOK_NAME
        
    except AttributeError as e:
        print(f"❌ 错误：配置文件缺少必要字段 - {e}")
        report.add_book_result(book_name, False)
        return False
    
    # 检查词汇表文件
    if not os.path.exists(terms_file):
        print(f"❌ 错误：未找到词汇表文件 '{terms_file}'")
        report.add_book_result(book_name, False)
        return False
    
    # 检查图片文件夹
    if not os.path.exists(image_folder_name):
        print(f"⚠️  警告：未找到图片文件夹 '{image_folder_name}'，将跳过图片处理")
    
    # 切换到书籍文件夹
    original_cwd = os.getcwd()
    os.chdir(book_folder)
    
    try:
        print(f"📖 开始处理: {book_display_name}")
        print(f"📁 词汇表文件: {config.TERMS_FILE}")
        print(f"📊 页码范围: {len(page_ranges)} 个")
        
        # 处理词汇
        successful, failed = extract_and_tag_terms(
            config.TERMS_FILE, 
            page_ranges, 
            config.IMAGE_FOLDER_NAME, 
            image_prefix
        )
        
        # 写入输出文件
        write_anki_output(successful, config.OUTPUT_FILE, deck_name)
        
        # 写入失败条目文件
        failed_output_file = os.path.join(book_folder, f"{os.path.splitext(config.OUTPUT_FILE)[0]}_failed.txt")
        write_failed_entries(failed, failed_output_file, book_display_name)
        
        # 计算成功率
        total_entries = len(successful) + len(failed)
        success_rate = len(successful) / total_entries * 100 if total_entries > 0 else 0
        
        # 报告结果
        print(f"✅ 成功处理: {len(successful):,} 条")
        print(f"❌ 失败: {len(failed):,} 条")
        print(f"🎯 成功率: {success_rate:.1f}%")
        print(f"📁 输出文件: {output_file}")
        
        # 初始化失败原因分析字典
        failure_reasons = {}
        
        if failed:
            print(f"📁 失败分析文件: {failed_output_file}")
            
            # 显示主要失败原因
            for entry in failed[:10]:  # 只分析前10个
                if '] >' in entry:
                    reason = entry.split('] >')[0].replace('[', '').strip()
                    failure_reasons[reason] = failure_reasons.get(reason, 0) + 1
            
            if failure_reasons:
                print("--- ⚠️ 主要失败原因 ---")
                for reason, count in sorted(failure_reasons.items(), key=lambda x: x[1], reverse=True)[:3]:
                    print(f"  {reason}: {count} 条")
        
        # 添加到报告
        report.add_book_result(book_name, True, len(successful), len(failed), failure_reasons)
        
        return True
        
    except Exception as e:
        print(f"❌ 处理过程中发生错误: {e}")
        import traceback
        print(f"详细错误信息:\n{traceback.format_exc()}")
        report.add_book_result(book_name, False)
        return False
        
    finally:
        os.chdir(original_cwd)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description=f'中英文词汇批量处理工具 {VERSION}')
    parser.add_argument('--books-dir', default=None, help='指定books文件夹路径')
    parser.add_argument('--output-report', default=None, help='指定详细报告输出路径')
    parser.add_argument('--quiet', action='store_true', help='静默模式，减少输出')
    parser.add_argument('--version', action='version', version=f'中英文词汇Anki卡片生成器 {VERSION}')
    
    args = parser.parse_args()
    
    print(f"        中英文词汇批量处理工具 {VERSION}")
    print("="*60)
    print(f"🔧 应用版本: {VERSION}")
    print(f"📅 处理时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # 获取books文件夹路径
    if args.books_dir:
        books_dir = args.books_dir
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        books_dir = os.path.join(script_dir, 'books')
    
    if not os.path.exists(books_dir):
        print(f"❌ 错误：未找到books文件夹 '{books_dir}'")
        print("请确保项目结构正确，并在books文件夹中放置各个书籍的文件夹")
        return
    
    # 获取所有书籍文件夹
    book_folders = [
        os.path.join(books_dir, item) 
        for item in os.listdir(books_dir) 
        if os.path.isdir(os.path.join(books_dir, item))
    ]
    
    if not book_folders:
        print(f"❌ 错误：books文件夹中没有找到任何书籍文件夹")
        return
    
    print(f"📚 发现 {len(book_folders)} 个书籍文件夹:")
    for i, folder in enumerate(book_folders, 1):
        print(f"  {i:2d}. {os.path.basename(folder)}")
    
    # 处理方式选择
    if not args.quiet:
        print("\n请选择处理方式:")
        print("1. 处理所有书籍")
        print("2. 选择特定书籍")
        print("3. 退出")
        
        choice = input("\n请输入选择 (1-3): ").strip()
    else:
        choice = '1'  # 静默模式下默认处理所有书籍
    
    # 创建处理报告
    report = ProcessingReport()
    
    if choice == '1':
        # 处理所有书籍
        print(f"\n🚀 开始处理所有 {len(book_folders)} 个书籍...")
        
        for i, book_folder in enumerate(book_folders, 1):
            print(f"\n📈 进度: {i}/{len(book_folders)}")
            process_single_book(book_folder, report)
        
    elif choice == '2':
        # 选择特定书籍
        print("\n请输入要处理的书籍编号 (用逗号分隔多个编号，如: 1,3,5):")
        selection = input("编号: ").strip()
        
        try:
            selected_indices = [int(x.strip()) - 1 for x in selection.split(',')]
            selected_books = [book_folders[i] for i in selected_indices if 0 <= i < len(book_folders)]
            
            if not selected_books:
                print("❌ 错误：没有选择有效的书籍")
                return
            
            print(f"\n🚀 开始处理选中的 {len(selected_books)} 个书籍...")
            
            for i, book_folder in enumerate(selected_books, 1):
                print(f"\n📈 进度: {i}/{len(selected_books)}")
                process_single_book(book_folder, report)
                
        except (ValueError, IndexError):
            print("❌ 错误：输入的编号无效")
            return
    
    elif choice == '3':
        print("👋 退出程序")
        return
    
    else:
        print("❌ 错误：无效的选择")
        return
    
    # 生成并显示最终报告
    summary_report = report.generate_summary_report()
    print(summary_report)
    
    # 保存详细报告
    if args.output_report:
        report_path = args.output_report
    else:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = f"processing_report_{timestamp}.json"
    
    report.save_detailed_report(report_path)

if __name__ == '__main__':
    main()