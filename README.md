# cn-en-glossary2anki
Converts a Chinese-English glossary (with page number structure) into a rich-format Anki import file. Supports HTML (images), deck and tag hierarchy, note type, and tab-separated .txt format.

将中英文词汇表（中文 英文 页码格式）转换为Anki导入文件。支持HTML图片、牌组层次、标签分类，输出制表符分隔的.txt格式。

## 主要功能

- 中英文词汇表转换为Anki格式
- 图片嵌入（HTML格式）
- 牌组和标签层次结构
- 页码信息保留
- 自定义笔记类型
- 输出制表符分隔的.txt文件，可直接导入Anki

## 项目结构

```text
cn-en-glossary2anki/                # 根目录
├── README.md                       
├── books/                          # 单词表及图片资源
│   └── cell_biology/               # "细胞生物学"词表示例
│       ├── config.py               # 配置脚本
│       ├── images/                 # 图像序列
│       ├── output_anki.txt         # 生成结果（成功）
│       ├── output_anki_failed.txt  # 生成结果（失败日志）
│       ├── 细胞生物学_单词表.txt    # 原始词表
│       └── 细胞生物学_目录.txt      # 章节目录
├── core.py                         # 核心逻辑模块
├── main.py                         # 脚本入口
├── example.apkg                    # 示例输出卡包
└── tools/                          # 辅助工具脚本
    ├── create_book.py              # 快速配置书籍文件夹
    ├── pdf_setup.py                # 快速转换pdf
    └── page_ranges_prompt.md       # 页码标签prompt
```

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/imRozen/cn-en-glossary2anki.git
cd cn-en-glossary2anki
```

### 2. 安装依赖

```bash
pip install PyMuPDF
```

### 3. 配置文件夹

```bash
python tools/create_book.py
```

在 `books/[书名]/config.py` 中配置：

- 牌组相关内容
- pdf处理范围
- 目录文件：用tools/page_ranges_prompt丢给AIGC，按照选定精度生成页码标签放入config.py/page_ranges
- 词汇表文件：要求格式是[中文 英文 页码]，如为[中文(英文) 页码]则括号手动替换为空格
- 图片文件：anki支持png和jpg格式，命名不能带中文或空格，会转写

### 4. pdf处理

填写好config.py中的pdf参数后：

```bash
python tools/pdf_setup.py
```

### 5. 运行转换脚本

```bash
python main.py
```

### 6. 校正

建立一个excel表，复制粘贴output.txt和检查fail.txt。检查目的是处理本脚本不能正确处理的数字，英文结尾用空格分隔的数字会被当成页码，一般加上`-`短横线就可以正确分隔了。

## 配置说明

- 卡片模板设置：在`core.py/write_anki_output`中修改
- 卡组和pdf信息：在`books/[书名]/config.py`中配置

## Output

输出在对应的`books/[书名]`文件夹下：

- `output_anki.txt`：成功转换的Anki导入文件
- `output_anki_failed.txt`：转换失败的条目

## Anki导入步骤

1. 打开Anki
2. 选择"文件" > "导入"
3. 选择生成的 `output_anki.txt` 文件
4. 确认字段映射和设置
5. 点击"导入"
6. 图片文件放入对应的collection.media文件夹中即可正确查看
7. 如需要添加音频，推荐[hyper-tts插件](https://ankiweb.net/shared/info/111623432)

## 示例

1. 项目包含完整的细胞生物学词汇表示例，位于 `books/cell_biology/` 目录，可以直接运行查看效果
2. 根目录下有制作好的神经病学卡组`example.apkg`，带有音频和图片页索引，可导入anki查看效果

## 工具说明

- `tools/create_book.py`：快速创建新书籍项目结构
- `tools/pdf_setup.py`：根据config.py处理pdf
- `tools/page_ranges_prompt.md`：生成页码标签映射`page_ranges`

## 已知问题

1. 不能正确处理英文结尾空格分隔的数字，会误认为页码，如果有这种情况需要手动添加`-`短横线分隔
2. 不能忽视开头的"单词表"和行内的字母分隔，需要手动在原始`glossary.txt`文件中清理

## 相关资源

- 百度网盘 [34本人卫五年制专业课教材anki术语卡组]( https://pan.baidu.com/s/1-yd7pDvlp00QeNjUVuwFNA?pwd=usu6)
- 该脚本是我整理这些单词的过程中搞出来的
