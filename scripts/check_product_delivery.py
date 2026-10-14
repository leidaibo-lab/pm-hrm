"""正式交付自动预检；只判断可检出的缺陷，不替代产品语义复审。"""
from pathlib import Path
import re
import sys
from urllib.parse import unquote

BODY_FORBIDDEN = (
    ('内部决策编号', r'(?<![\w-])D-\d{3}(?![\w-])'),
    ('内部过程引用', r'产品探索/|docs/product/|产品决策记录\.md'),
    ('抽象规则兜底', r'相关业务规则|规则规则|公共字段规范公共|规则一年'),
    ('内部确认过程', r'本节以\[产品决策|按用户(?:选择|确认)|本轮(?:修正|整理|检查)|字段定义完成不代表'),
    ('拼接或断句', r'按按(?!钮)|中的\s*和\s*[。；]|(?:验收见|正式场景)\s*[。；]|(?m:^\s*关联\s*[。；])'),
)


PAGE_TABLE_HEADERS = {
    '按钮': ('按钮名称', '所在位置', '操作权限', '前置条件', '点击行为', '确认要求', '成功结果', '异常反馈'),
    '输入字段': ('字段名称', '业务含义', '数据类型', '控件类型', '取值来源', '默认值', '必填条件', '校验规则', '修改与历史'),
    '筛选项': ('字段名称', '数据类型', '控件类型', '取值来源', '默认值', '筛选规则'),
    '展示字段': ('字段名称', '数据类型', '取值来源', '展示规则', '空值展示', '交互说明'),
}


def page_table_kind(cells):
    # 对象事实及区域概览不属于这四类页面规格。
    if '按钮名称' in cells:
        return '按钮'
    if '业务含义' in cells and any(x in cells for x in ('控件', '控件类型')):
        return '输入字段'
    if any(x in cells for x in ('筛选说明', '筛选规则')):
        return '筛选项'
    if '展示规则' in cells and '空值展示' in cells:
        return '展示字段'
    return None


def visible_text(text):
    # 显式定位标识不属于可见正文。
    text = re.sub(r'<a\s+id="[^"]+"\s*></a>', '', text)
    return re.sub(r'<!--.*?-->', '', text, flags=re.S)


def heading_anchors(text):
    anchors = set(re.findall(r'<a\s+id="([^"]+)"\s*></a>', text))
    counts = {}
    fenced = False
    for line in text.splitlines():
        if line.startswith('```'):
            fenced = not fenced
        if fenced:
            continue
        heading = re.match(r'^#{1,6}\s+(.+)$', line)
        if heading:
            label = re.sub(r'[^\w\-\s]', '', heading[1].lower()).replace(' ', '-')
            count = counts.get(label, 0)
            counts[label] = count + 1
            anchors.add(label if not count else f'{label}-{count}')
    return anchors


def review(documents, output_root, expected=None):
    """返回确定性错误和阅读提示；documents可用于写入前或内存检查。"""
    documents = {Path(p).resolve(): t for p, t in documents.items()}
    output_root = Path(output_root).resolve()
    errors, notes = [], []
    links = 0
    for path, text in documents.items():
        body = visible_text(text)
        for label, pattern in BODY_FORBIDDEN:
            for match in re.finditer(pattern, body):
                line = body[:match.start()].count('\n') + 1
                errors.append(f'{path.name}:{line} {label}：{match[0]}')
        version_section = re.search(r'^## (?:版本与变更记录|版本记录)\n', text, re.M)
        if version_section:
            preceding = re.findall(r'^## (.+)$', text[:version_section.start()], re.M)
            if preceding and preceding != ['1 文档信息'] and preceding != ['文档信息']:
                errors.append(f'{path.name} 版本变更记录须位于顶部或文档信息之后')
        explicit = re.findall(r'<a\s+id="([^"]+)"\s*></a>', text)
        duplicates = {a for a in explicit if explicit.count(a) > 1}
        if duplicates:
            errors.append(f'{path.name} 显式锚点重复：{sorted(duplicates)}')
        fenced, table_width = False, None
        headings = {}
        document_lines = text.splitlines()
        for number, line in enumerate(document_lines, 1):
            if line.startswith('```'):
                fenced = not fenced
                continue
            if fenced:
                continue
            if line.startswith('|'):
                width = len(re.split(r'(?<!\\)\|', line)) - 2
                if table_width is not None and width != table_width:
                    errors.append(f'{path.name}:{number} 表格列数不一致')
                table_width = width
                if path.name.endswith('PRD.md') and table_width is not None:
                    if number < len(document_lines) and re.match(r'^\|[\s:|\-]+\|$', document_lines[number]):
                        cells = tuple(c.strip() for c in line.strip('|').split('|'))
                        kind = page_table_kind(cells)
                        if kind and cells != PAGE_TABLE_HEADERS[kind]:
                            errors.append(f'{path.name}:{number} {kind}表头不符合统一规范')
            else:
                table_width = None
            heading = re.match(r'^#{2,6} (.+)$', line)
            if heading:
                name = re.sub(r'^\d+(?:\.\d+)*\s+', '', heading[1])
                headings.setdefault(name, []).append(number)
            if not line.startswith(('|', '<a')) and len(line) > 240:
                notes.append(f'{path.name}:{number} 长段落，需复核阅读负担')
        if fenced:
            errors.append(f'{path.name} 代码块未闭合')
        if path.name.endswith('PRD.md'):
            for name, locations in headings.items():
                if len(locations) > 1 and name not in {'编辑模式差异', '异常处理与验收摘要', '页面内容与操作授权', '页面与验收'}:
                    notes.append(f'{path.name} 同名章节需核对是否重复定义：{name} {locations}')
            if re.search(r'(?<![\w-])(?:US-\d+|TS-[A-Z]+-\d+|RB-\d+|TR-[A-Z]+-\d+)', body):
                errors.append(f'{path.name} PRD正文仍含工程追踪编号')
        for match in re.finditer(r'\[([^\]\n]*)\]\(([^)\n]+)\)', text):
            label, link = match.groups()
            if not label.strip():
                errors.append(f'{path.name} 空链接名称')
            if re.match(r'^[a-zA-Z][\w+.-]*:', link):
                continue
            links += 1
            local, sep, fragment = link.partition('#')
            target = (path.parent / unquote(local)).resolve() if local else path
            if not target.is_relative_to(output_root):
                errors.append(f'{path.name} 引用越出output：{link}')
                continue
            if target not in documents and not target.exists():
                errors.append(f'{path.name} 引用目标不存在：{link}')
                continue
            target_text = documents.get(target)
            if target_text is None and target.suffix == '.md':
                target_text = target.read_text()
            if sep and target.suffix == '.md' and unquote(fragment) not in heading_anchors(target_text):
                errors.append(f'{path.name} 锚点不存在：{link}')
        if expected is not None and path in expected and text != expected[path]:
            errors.append(f'{path.name} 输出与权威源生成结果不一致')
    # 入口声明版本应与实际文档元信息一致。
    readme = documents.get(output_root / 'README.md', '')
    for label, name in [('项目总览', '产品项目总览.md'), ('基础资料PRD', '基础资料管理PRD.md'),
                        ('招聘PRD', '招聘管理PRD.md'), ('验收附件', '招聘管理验收附件.md')]:
        declared = re.search(re.escape(label) + r'(\d+\.\d+)', readme)
        text = documents.get(output_root / name, '')
        actual = re.search(r'(?:版本／(?:日期|更新时间).*?)(\d+\.\d+)／', text)
        if declared and actual and declared[1] != actual[1]:
            errors.append(f'README {label}版本{declared[1]}与正文{actual[1]}不一致')
    return {'errors': errors, 'review_notes': notes, 'local_links': links, 'documents': len(documents)}


def main():
    from export_product_delivery import OUTPUT, generate_delivery
    documents = {p.resolve(): p.read_text() for p in OUTPUT.rglob('*.md')}
    expected = generate_delivery()
    result = review(documents, OUTPUT, expected)
    for error in result['errors']:
        print('错误：' + error)
    for note in result['review_notes']:
        print('阅读提示：' + note)
    print(f"自动预检：{result['documents']}份文档，{result['local_links']}处本地引用，"
          f"{len(result['errors'])}项错误，{len(result['review_notes'])}项阅读提示。")
    print('本结果仅为自动预检；正文语义、案例推演及联合交接分别复核。')
    return 1 if result['errors'] else 0


if __name__ == '__main__':
    sys.exit(main())
