"""
中英文词汇Anki卡片生成器 - 核心模块

功能：
- 解析中英文词汇文件
- 智能中英文分离（支持希腊字母）
- 生成Anki导入格式文件
- 支持图片标签和章节标签

适用范围：任何包含"中文 英文 页码"格式的纯文本文件

作者：RoZen
版本：1.0.0
"""

import re
import os
import urllib.parse
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# 模块版本
__version__ = "1.0.0"

script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

@dataclass
class ProcessingStats:
    """处理统计信息"""
    total_processed: int = 0
    successful: int = 0
    failed: int = 0
    filtered_out: int = 0
    failure_reasons: Dict[str, int] = None
    
    def __post_init__(self):
        if self.failure_reasons is None:
            self.failure_reasons = {}

class TermProcessor:
    """中英文术语处理器 - 支持希腊字母和复杂术语格式"""
    
    def __init__(self):
        self.stats = ProcessingStats()
        self._init_patterns()
    
    def _init_patterns(self):
        """初始化正则表达式模式"""
        # 过滤模式 - 需要跳过的内容
        self.filter_patterns = [
            r'^中英文名词对照索引',  # 索引页面
            r'^[A-Z]\s*$',  # 单个大写字母
            r'^\d{3,}\s*$',  # 纯数字（页码）
            r'^[，。；：,\.;:]\s*$',  # 纯符号
            r'^[（）\(\)]\s*$',  # 纯括号
            r'^\s*$',  # 空白
            r'^推荐阅读',  # 推荐阅读
            r'^参考文献',  # 参考文献
        ]
        
        # 中文字符模式
        self.chinese_pattern = r'[\u4e00-\u9fa5]'
        
        # 英文字符模式 - 包含拉丁字母和希腊字母
        self.english_pattern = r'[a-zA-Z\u0370-\u03FF]'
        
        # 拉丁字母和希腊字母字符集（用于构建正则）
        self.latin_greek_chars = r'a-zA-Z\u0370-\u03FF'
        
        # 页码提取模式
        self.page_pattern = r'(\d+(?:[,\uFF0C]\s*\d+)*)\s*$'

    _fw2hw = str.maketrans({           # full‑width → half‑width
        '，': ',', '．': '.', '；': ';', '：': ':',
    })
    
    def _normalize(self, text: str) -> str:
        """把全角标点替换成半角，并将制表符转换为空格，防止正则漏匹配"""
        # 先进行原有的全角到半角转换
        text = text.translate(self._fw2hw)
        # 将制表符替换为空格
        text = text.replace('\t', ' ')
        text = re.sub(r'[\u3000\u200A]+', ' ', text)
        text = text.translate(str.maketrans('，．：；', ',.:;'))
        return text

    def should_filter_content(self, content: str) -> bool:
        """判断内容是否应该被过滤掉"""
        content_clean = content.strip()
        
        # 检查是否匹配过滤模式
        for pattern in self.filter_patterns:
            if re.search(pattern, content_clean):
                return True
        
        # 过滤过短的内容
        if len(content_clean) < 2:
            return True
        
        # 过滤只包含数字和符号的内容
        if re.match(r'^[0-9\s，。；：,\.;:\(\)（）-]+$', content_clean):
            return True
            
        return False
    
    def extract_page_numbers(self, line: str) -> Tuple[str, str]:
        """改进的页码提取，能区分术语中的数字和真正的页码"""
        line_clean = self._normalize(line.strip())
        
        # 页码模式：必须是独立的数字，前面有至少一个空格，并且在行末
        # 避免匹配术语中的数字（如PD-1, GAD-7中的数字）
        page_patterns = [
            r'\s+(\d+(?:,\s*\d+)*)\s*$',  # 标准页码：前面有空格的数字
            r'\s+(\d+)\s*$',  # 单个页码
        ]
        
        for pattern in page_patterns:
            match = re.search(pattern, line_clean)
            if match:
                page_numbers = match.group(1)
                content = line_clean[:match.start()].strip()
                
                # 验证这确实是页码而不是术语的一部分
                if self._is_valid_page_number(content, page_numbers, match.start()):
                    return content, page_numbers
        
        # 如果没有找到明确的页码，返回原内容
        return line_clean, ""    
    
    def _is_valid_page_number(self, content: str, page_num: str, page_start_pos: int) -> bool:
        """验证提取的数字是否为真正的页码"""
        try:
            # 检查页码是否合理（在常见的页码范围内）
            page_int = int(page_num.split(',')[0])  # 取第一个页码
            if page_int < 1 or page_int > 2000:  # 页码应该在合理范围内
                return False
            
            # 检查页码前的内容
            if page_start_pos > 0:
                # 页码前应该有足够的空格分隔
                preceding_chars = content[-min(10, len(content)):]  # 检查最后几个字符
                
                # 如果页码前紧跟着连字符+数字，可能是术语的一部分
                if re.search(r'[-]\d+$', preceding_chars):
                    return False
                
                # 如果页码前紧跟着字母+数字，可能是术语的一部分  
                if re.search(rf'[{self.latin_greek_chars}]\d+$', preceding_chars):
                    return False
                    
                # 如果页码前紧跟着逗号+字母+数字，可能是缩写术语
                if re.search(rf'[,，]\s*[A-Z\u0391-\u03A9]+[-]?\d+$', preceding_chars):
                    return False
            
            return True
            
        except ValueError:
            return False
        
    def split_chinese_english_basic(self, content: str) -> Optional[Tuple[str, str]]:
        """基础方法: 基于最后一个中文字符分离"""
        try:
            chinese_matches = list(re.finditer(self.chinese_pattern, content))
            if not chinese_matches:
                return None
            
            last_chinese_pos = chinese_matches[-1].start()
            
            # 从最后一个中文字符之后查找第一个英文字符
            remaining = content[last_chinese_pos:]
            english_match = re.search(self.english_pattern, remaining)
            
            if not english_match:
                return None
            
            split_point = last_chinese_pos + english_match.start()
            chinese_part = content[:split_point].strip()
            english_part = content[split_point:].strip()
            
            return chinese_part, english_part
            
        except Exception:
            return None
    
    def split_chinese_english_blocks(self, content: str) -> Optional[Tuple[str, str]]:
        """基于连续中文字符块分离"""
        try:
            # 查找连续的中文字符块
            chinese_blocks = list(re.finditer(r'[\u4e00-\u9fa5]+', content))
            if not chinese_blocks:
                return None
            
            # 使用最后一个中文块作为分离点
            last_block = chinese_blocks[-1]
            split_point = last_block.end()
            
            # 在分离点之后查找英文
            remaining = content[split_point:].strip()
            if not re.search(self.english_pattern, remaining):
                return None
            
            chinese_part = content[:split_point].strip()
            english_part = remaining
            
            return chinese_part, english_part
            
        except Exception:
            return None
    
    def split_chinese_english_patterns(self, content: str) -> Optional[Tuple[str, str]]:
        """基于模式匹配分离"""
        try:
            # 尝试多种分离模式
            patterns = [
                rf'^(.*[\u4e00-\u9fa5].*?)\s+([{self.latin_greek_chars}].*?)$',  # 空格分离
                rf'^(.*[\u4e00-\u9fa5].*?)\s*,\s*([{self.latin_greek_chars}].*?)$',  # 逗号分离
                rf'^(.*[\u4e00-\u9fa5].*?)\s*([A-Z\u0391-\u03A9][{self.latin_greek_chars}].*?)$',  # 大写字母开始
                rf'^(.*[\u4e00-\u9fa5].*?)\s*\(\s*([{self.latin_greek_chars}].*?)\s*\).*$',  # 括号中的英文
            ]
            
            for pattern in patterns:
                match = re.match(pattern, content)
                if match:
                    chinese_part = match.group(1).strip()
                    english_part = match.group(2).strip()
                    
                    # 验证结果
                    if (chinese_part and english_part and 
                        re.search(self.chinese_pattern, chinese_part) and
                        re.search(self.english_pattern, english_part)):
                        return chinese_part, english_part
            
            return None
            
        except Exception:
            return None
    
    def split_chinese_english_special_chars(self, content: str) -> Optional[Tuple[str, str]]:
        """特殊字符处理"""
        try:
            # 处理特殊开头的情况（如数字、希腊字母等）
            content_clean = content.strip()
            
            # 查找模式：中文 + 特殊字符/数字 + 英文
            pattern = rf'^(.*[\u4e00-\u9fa5].*?)\s*[-\s]*\s*([0-9]*[{self.latin_greek_chars}].*?)$'
            match = re.match(pattern, content_clean)
            
            if match:
                chinese_part = match.group(1).strip()
                english_part = match.group(2).strip()
                
                # 清理中文部分的尾部特殊字符
                chinese_part = re.sub(r'[-\s]*$', '', chinese_part)
                
                if (chinese_part and english_part and 
                    re.search(self.chinese_pattern, chinese_part) and
                    re.search(self.english_pattern, english_part)):
                    return chinese_part, english_part
            
            return None
            
        except Exception:
            return None
        
    def split_chinese_english_uppercase_ending(self, content: str) -> Optional[Tuple[str, str]]:
        """处理中文部分以英文大写字母结尾的情况"""
        try:
            content_clean = content.strip()
            
            # 先移除页码部分，以便更准确地分离中英文
            page_match = re.search(self.page_pattern, content_clean)
            if page_match:
                content_without_page = content_clean[:page_match.start()].strip()
            else:
                content_without_page = content_clean
            
            # 查找所有中文字符的位置
            chinese_matches = list(re.finditer(self.chinese_pattern, content_without_page))
            if not chinese_matches:
                return None
            
            # 从最后一个中文字符开始，向后查找分离点
            last_chinese_pos = chinese_matches[-1].end()
            
            # 在最后一个中文字符之后的部分
            remaining_part = content_without_page[last_chinese_pos:]
            
            # 模式1: 中文后直接跟英文大写字母(可能是缩写)+空格+英文单词
            pattern1 = rf'^([A-Z\u0391-\u03A9]+)\s+([{self.latin_greek_chars}].*)$'
            match1 = re.match(pattern1, remaining_part)
            if match1:
                abbreviation = match1.group(1)  # 缩写部分
                english_start = match1.group(2)  # 英文部分
                
                chinese_part = content_without_page[:last_chinese_pos + len(abbreviation)].strip()
                english_part = english_start.strip()
                
                if self.validate_split_result(chinese_part, english_part):
                    return chinese_part, english_part
            
            # 模式2: 处理更复杂的情况
            pattern2 = rf'^([{self.latin_greek_chars}]+)\s+([a-z\u03B1-\u03C9][{self.latin_greek_chars}].*)$'
            match2 = re.match(pattern2, remaining_part)
            if match2:
                abbreviation = match2.group(1)  # 缩写或英文序列
                english_start = match2.group(2)  # 英文部分（小写开头）
                
                chinese_part = content_without_page[:last_chinese_pos + len(abbreviation)].strip()
                english_part = english_start.strip()
                
                if self.validate_split_result(chinese_part, english_part):
                    return chinese_part, english_part
            
            return None
            
        except Exception:
            return None

    def split_chinese_english_with_numbers(self, content: str) -> Optional[Tuple[str, str]]:
        """专门处理包含数字的术语"""
        try:
            content_clean = content.strip()
            
            # 查找所有中文字符的位置
            chinese_matches = list(re.finditer(self.chinese_pattern, content_clean))
            if not chinese_matches:
                return None
            
            # 从最后一个中文字符开始分析
            last_chinese_pos = chinese_matches[-1].end()
            remaining_part = content_clean[last_chinese_pos:]
            
            # 模式1: 中文后跟连字符和数字，然后是英文
            pattern1 = rf'^([-]\d+)\s+([{self.latin_greek_chars}].*)$'
            match1 = re.match(pattern1, remaining_part)
            if match1:
                chinese_suffix = match1.group(1)  # -1, -7 等
                english_part = match1.group(2)   # 英文部分
                
                chinese_part = content_clean[:last_chinese_pos + len(chinese_suffix)].strip()
                
                if self.validate_split_result_enhanced(chinese_part, english_part):
                    return chinese_part, english_part
            
            # 模式2: 中文后跟数字，然后是英文（无连字符）
            pattern2 = rf'^(\d+)\s+([{self.latin_greek_chars}].*)$'
            match2 = re.match(pattern2, remaining_part)
            if match2:
                chinese_suffix = match2.group(1)  # 数字
                english_part = match2.group(2)    # 英文部分
                
                chinese_part = content_clean[:last_chinese_pos + len(chinese_suffix)].strip()
                
                if self.validate_split_result_enhanced(chinese_part, english_part):
                    return chinese_part, english_part
            
            return None
            
        except Exception as e:
            logger.debug(f"数字术语处理失败: {e}")
            return None

    def validate_split_result(self, chinese: str, english: str) -> bool:
        """验证分离结果的质量"""
        # 基本验证
        if not chinese or not english:
            return False
        
        # 检查中文部分是否包含中文
        if not re.search(self.chinese_pattern, chinese):
            return False
        
        # 检查英文部分是否包含英文
        if not re.search(self.english_pattern, english):
            return False
        
        # 检查长度合理性
        if len(chinese.strip()) < 1 or len(english.strip()) < 1:
            return False
        
        # 检查英文部分不应该主要是符号
        english_clean = re.sub(rf'[^{self.latin_greek_chars}]', '', english)
        if len(english_clean) < len(english) * 0.3:  # 英文字符应该占30%以上
            return False
        
        return True

    def validate_split_result_enhanced(self, chinese: str, english: str) -> bool:
        """增强的验证方法，考虑数字在术语中的情况"""
        # 调用原有的基本验证
        if not self.validate_split_result(chinese, english):
            return False
        
        # 额外验证：确保数字在合理的位置
        chinese_clean = chinese.strip()
        english_clean = english.strip()
        
        # 检查英文部分的合理性
        english_alpha_count = len(re.findall(rf'[{self.latin_greek_chars}]', english_clean))
        if english_alpha_count < 2:  # 英文部分应该至少有2个英文字母
            return False
        
        # 检查是否意外包含了中文
        if re.search(self.chinese_pattern, english_clean):
            return False
        
        return True

    def split_chinese_english(self, content: str) -> Optional[Tuple[str, str]]:
        """智能中英文分离 - 尝试多种方法"""
        methods = [
            ("数字术语处理", self.split_chinese_english_with_numbers),    
            ("英文大写结尾分离", self.split_chinese_english_uppercase_ending), 
            ("基础分离", self.split_chinese_english_basic),
            ("块分离", self.split_chinese_english_blocks), 
            ("模式分离", self.split_chinese_english_patterns),
            ("特殊字符分离", self.split_chinese_english_special_chars),
        ]
        
        for method_name, method_func in methods:
            result = method_func(content)
            if result and self.validate_split_result_enhanced(result[0], result[1]):
                logger.debug(f"使用{method_name}成功分离: {content}")
                return result
        
        return None
    
    def clean_text(self, text: str) -> str:
        """清理文本"""
        if not text:
            return ""
        
        # 移除多余的空白
        text = re.sub(r'\s+', ' ', text.strip())
        
        # 移除尾部的标点符号（但保留必要的）
        text = re.sub(r'[，。；：]+$', '', text)
        
        # 清理特殊字符组合
        text = re.sub(r'\s*[-\s]+$', '', text)
        
        return text.strip()
    
    def get_tag_for_page(self, page_number_str: str, ranges: List[Tuple[int, int, str]]) -> str:
        """根据页码查找并返回对应的标签"""
        if not page_number_str:
            return "未知章节"
        
        first_page_match = re.search(r'\d+', page_number_str)
        if not first_page_match:
            return "未知章节"
        
        page_num = int(first_page_match.group(0))
        
        for start, end, tag in ranges:
            if start <= page_num <= end:
                return tag
        
        return "未知章节"
    
    def record_failure(self, reason: str, content: str = ""):
        """记录失败原因"""
        self.stats.failed += 1
        if reason not in self.stats.failure_reasons:
            self.stats.failure_reasons[reason] = 0
        self.stats.failure_reasons[reason] += 1
        
        logger.debug(f"处理失败 - {reason}: {content[:50]}...")
    
    def process_single_entry(self, content: str, page_number: str, tag_ranges: List[Tuple[int, int, str]], 
                        image_folder: str, image_prefix: str) -> Optional[Dict]:
        """处理单个条目"""
        self.stats.total_processed += 1
        
        # 过滤检查
        if self.should_filter_content(content):
            self.stats.filtered_out += 1
            logger.debug(f"过滤条目: {content}")
            return None
        
        # 中英文分离
        split_result = self.split_chinese_english(content)
        if not split_result:
            self.record_failure("中英文分离失败", content)
            return None
        
        chinese_term, english_term = split_result
        
        # 文本清理
        chinese_term = self.clean_text(chinese_term)
        english_term = self.clean_text(english_term)
        
        # 最终验证
        if not self.validate_split_result(chinese_term, english_term):
            self.record_failure("结果验证失败", content)
            return None
        
        # 生成标签和图片
        tag = self.get_tag_for_page(page_number, tag_ranges)
        
        # 改进的图片标签生成逻辑
        image_tag = ""
        first_page_match = re.search(r'\d+', page_number)
        if first_page_match and image_folder and os.path.exists(image_folder):
            page_num = int(first_page_match.group(0))
            
            # 尝试多种图片文件名格式，按优先级排序
            image_filename_candidates = [
                f"{image_prefix}-{page_num:04d}.png",  # 格式1: prefix-0077.png (带连字符，4位填充)
                f"{image_prefix}{page_num:04d}.png",   # 格式2: prefix0077.png (无连字符，4位填充)
                f"{image_prefix}-{page_num}.png",      # 格式3: prefix-77.png (带连字符，无填充)
                f"{image_prefix}{page_num}.png",       # 格式4: prefix77.png (无连字符，无填充)
                f"{image_prefix}_{page_num:04d}.png",  # 格式5: prefix_0077.png (下划线，4位填充)
                f"{image_prefix}_{page_num}.png",      # 格式6: prefix_77.png (下划线，无填充)
            ]
            
            # 如果有额外的常见格式，也可以添加
            if page_num < 1000:  # 对于3位数以下的页码，也尝试3位填充
                image_filename_candidates.extend([
                    f"{image_prefix}-{page_num:03d}.png",  # prefix-077.png
                    f"{image_prefix}{page_num:03d}.png",   # prefix077.png
                    f"{image_prefix}_{page_num:03d}.png",  # prefix_077.png
                ])
            
            # 按顺序尝试每种格式
            for image_filename in image_filename_candidates:
                image_path = os.path.join(image_folder, image_filename)
                if os.path.exists(image_path):
                    image_tag = f'<img src="{image_filename}">'
                    logger.debug(f"找到图片文件: {image_filename}")
                    break
            else:
                # 如果所有格式都没找到，记录调试信息
                logger.debug(f"页码 {page_num} 未找到对应图片文件。尝试过的格式:")
                for candidate in image_filename_candidates[:4]:  # 只显示主要的4种格式
                    candidate_path = os.path.join(image_folder, candidate)
                    logger.debug(f"  - {candidate} -> {'存在' if os.path.exists(candidate_path) else '不存在'}")
        
        self.stats.successful += 1
        
        return {
            '中文': chinese_term,
            '英文': english_term,
            '图片': image_tag,
            '页码': page_number,
            'tag': tag
        }
    
    def merge_broken_lines(self, lines: List[str]) -> List[str]:
        """合并被换行分割的条目"""
        merged_lines = []
        buffer = ""

        # 仅数字（可带逗号）的页码行
        page_only_pat = re.compile(r'^\d+(?:[,\uFF0C]\s*\d+)*\s*$')
        # 其他需要无视的行
        ignore_pat = re.compile(r'^\s*([A-Z]|中英文名词对照索引)\s*$')

        for raw in lines:
            line = self._normalize(raw.strip())
            if not line:
                continue

            # 先处理纯页码行
            if page_only_pat.match(line):
                # a. 正常情况：补到缓冲区并立即成条目
                if buffer:
                    merged_lines.append(f"{buffer} {line}".strip())
                    buffer = ""
                # b. 极端情况：上一条已写完但页码落单
                elif merged_lines:
                    merged_lines[-1] = f"{merged_lines[-1]} {line}"
                continue

            # 过滤其余无意义行
            if ignore_pat.match(line):
                continue

            # 原有逻辑
            if re.search(r'\s+\d+\s*$', line):
                page_match = re.search(r'\s+(\d+)\s*$', line)
                if page_match and self._is_real_page_number(line, page_match.start(), page_match.group(1)):
                    full_entry = f"{buffer} {line}".strip() if buffer else line
                    merged_lines.append(full_entry)
                    buffer = ""
                    continue

            # 尚未结束，继续累积
            buffer = f"{buffer} {line}".strip() if buffer else line

        # 处理文件末尾残留
        if buffer:
            merged_lines.append(buffer)

        return merged_lines
    
    def split_entries_by_page(self, lines: List[str]) -> List[Dict[str, str]]:
        """使用页码作为分隔符，精准拆分词条"""
        entries = []
        
        for line in lines:
            line_clean = line.strip()
            if not line_clean:
                continue
                
            # 找到所有可能的页码位置
            potential_pages = []
            
            # 使用更严格的页码模式：独立的数字，前后不与字母或连字符相连
            page_pattern = r'(?<!\S)(\d+(?:,\s*\d+)*)(?=\s|$)'
            
            for match in re.finditer(page_pattern, line_clean):
                start_pos = match.start()
                page_number = match.group(1)
                
                # 验证这是否为真正的页码
                if self._is_real_page_number(line_clean, start_pos, page_number):
                    potential_pages.append((start_pos, match.end(), page_number))
            
            if not potential_pages:
                # 没有找到页码，跳过这行
                continue
            
            # 按照页码位置拆分条目
            last_pos = 0
            for start_pos, end_pos, page_number in potential_pages:
                content = line_clean[last_pos:start_pos].strip()
                
                if content:  # 确保内容不为空
                    entries.append({
                        'content': content,
                        'page_number': page_number
                    })
                
                last_pos = end_pos
        
        return entries

    def _is_real_page_number(self, line: str, pos: int, page_num: str) -> bool:
        """判断数字是否为真正的页码而非术语中的数字"""
        try:
            # 页码应该在合理范围内
            page_int = int(page_num.replace('，', ',').split(',')[0])
            if page_int < 1 or page_int > 2000:
                return False
            
            # 检查数字前面的上下文
            before_context = line[:pos] if pos > 0 else ""
            after_context = line[pos + len(page_num):] if pos + len(page_num) < len(line) else ""
            
            # 排除：数字前面紧跟连字符的情况 (如 "量表-7")
            if before_context.endswith('-'):
                return False
            
            # 排除：数字前面紧跟字母的情况 (如 "GAD7")  
            if before_context and re.search(rf'[{self.latin_greek_chars}]$', before_context):
                return False
                
            # 排除：数字后面紧跟连字符+字母的情况 (如 "7-item")
            if after_context.startswith('-') and len(after_context) > 1 and re.search(rf'^-[{self.latin_greek_chars}]', after_context):
                return False
            
            # 页码前应该有足够的内容（不应该是行首的数字）
            content_before = before_context.strip()
            if len(content_before) < 3:  # 页码前应该有实际的术语内容
                return False
            
            # 页码前应该有空格分隔（真正的页码通常前面有空格）
            if not before_context.endswith(' '):
                return False
                
            return True
            
        except (ValueError, IndexError):
            return False

def extract_and_tag_terms(terms_file: str, tag_ranges: List[Tuple[int, int, str]], 
                         image_folder_name: str = "", image_prefix: str = "") -> Tuple[List[Dict], List[str]]:
    """
    提取、标注词汇，并生成包含图片字段的Anki导入文件
    
    Args:
        terms_file: 词汇表文件路径
        tag_ranges: 页码范围和标签的映射列表
        image_folder_name: 图片文件夹名称
        image_prefix: 图片文件前缀
    
    Returns:
        (成功提取的条目列表, 失败条目列表)
    """
    
    processor = TermProcessor()
    successful_extractions = []
    failed_extractions = []
    
    # 检查文件是否存在
    if not os.path.exists(terms_file):
        logger.error(f"错误：词汇索引文件 '{terms_file}' 不存在。")
        return [], [f"文件不存在: {terms_file}"]
    
    # 读取文件
    try:
        with open(terms_file, 'r', encoding='utf-8') as f:
            raw_lines = f.readlines()
    except Exception as e:
        logger.error(f"读取文件失败: {e}")
        return [], [f"读取文件失败: {e}"]
    
    logger.info(f"开始处理文件: {terms_file}")
    logger.info(f"原始行数: {len(raw_lines)}")
    
    # 1. 合并换行的条目
    merged_lines = processor.merge_broken_lines(raw_lines)
    logger.info(f"合并后行数: {len(merged_lines)}")
    
    # 2. 按页码拆分条目
    entries = processor.split_entries_by_page(merged_lines)
    logger.info(f"拆分后条目数: {len(entries)}")
    
    # 3. 处理每个条目
    for entry in entries:
        result = processor.process_single_entry(
            entry['content'], 
            entry['page_number'], 
            tag_ranges, 
            image_folder_name, 
            image_prefix
        )
        
        if result:
            successful_extractions.append(result)
        else:
            # 构造失败条目信息
            content = entry.get('content', '')
            page = entry.get('page_number', '')
            
            # 判断失败原因
            if processor.should_filter_content(content):
                reason = "内容被过滤"
            elif not re.search(processor.chinese_pattern, content):
                reason = "内容中不含中文字符"
            elif processor.split_chinese_english(content) is None:
                reason = "中英文分离失败"
            else:
                reason = "其他原因"
            
            failed_extractions.append(f"[{reason}] > {content} {page}")
    
    # 4. 排序结果
    def get_sort_key(item):
        first_page_match = re.search(r'\d+', item['页码'])
        return int(first_page_match.group()) if first_page_match else 0
    
    successful_extractions.sort(key=get_sort_key)
    
    # 5. 输出统计信息
    stats = processor.stats
    logger.info("="*50)
    logger.info("处理统计:")
    logger.info(f"  总计处理: {stats.total_processed}")
    logger.info(f"  成功提取: {stats.successful}")
    logger.info(f"  处理失败: {stats.failed}")
    logger.info(f"  过滤条目: {stats.filtered_out}")
    logger.info(f"  成功率: {stats.successful/stats.total_processed*100:.1f}%")
    
    if stats.failure_reasons:
        logger.info("失败原因分布:")
        for reason, count in sorted(stats.failure_reasons.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"  {reason}: {count}")
    
    return successful_extractions, failed_extractions

def write_anki_output(successful_extractions: List[Dict], output_file: str, deck_name: str = "词汇卡组"):
    """写入Anki导入文件"""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            # 写入配置信息
            f.write("#separator:tab\n")
            f.write("#html:true\n")
            f.write("#notetype column:1\n")
            f.write("#deck column:2\n")
            f.write("#tags column:8\n")
            
            # 写入数据
            for entry in successful_extractions:
                f.write(f"医学英语V2\t{deck_name}\t{entry['英文']}\t{entry['中文']}\t\t\t{entry['图片']}\t{entry['tag']}\n")
        
        logger.info(f"成功写入Anki文件: {output_file}")
        
    except Exception as e:
        logger.error(f"写入Anki文件失败: {e}")