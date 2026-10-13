"""从权威正文生成交付目录；输出不直接编辑，业务规则只维护一处。"""
from pathlib import Path
import os
import re

ROOT = Path(__file__).resolve().parents[1]
PRODUCT = ROOT / 'docs/product'
OUTPUT = ROOT / 'docs/output'
SOURCES = {
    PRODUCT / '公共规范/字段与表单校验规范.md': OUTPUT / '公共规范/字段与表单校验规范.md',
    PRODUCT / '公共规范/权限与数据治理规范.md': OUTPUT / '公共规范/权限与数据治理规范.md',
    PRODUCT / '指标与试点基线.md': OUTPUT / '指标与试点基线.md',
    PRODUCT / '产品总览.md': OUTPUT / '产品项目总览.md',
    PRODUCT / '模块/招聘管理/产品需求文档.md': OUTPUT / '招聘管理PRD.md',
    PRODUCT / '平台基础能力/基础资料管理产品需求文档.md': OUTPUT / '基础资料管理PRD.md',
    PRODUCT / '验收与追踪/招聘管理验收附件.md': OUTPUT / '招聘管理验收附件.md',
}



# 决策编号仅在产品协作资料中使用；交付引用以业务含义表达。
DECISION_NAMES = {
    '000': '本期范围', '001': '职位与外部系统边界', '002': '候选人阶段规则',
    '003': '首批试点范围', '004': '面试配置规则', '005': '邀约规则',
    '006': '招聘决策规则', '007': '评价授权规则', '008': '人员配置规则',
    '009': '数据生命周期规则', '010': '平台与招聘职责', '011': '应聘资料治理规则',
    '012': '取消与终止规则', '013': '职位责任指派规则', '014': '多轮评价规则',
    '015': '一面跳过规则', '016': '公共校验与授权规则', '017': '文字评价维度规则',
    '018': '场次责任与历史处理规则', '019': '评价流转与最终承接规则',
    '020': '同职位活动重复准入规则', '021': '前轮迟交待定规则',
    '022': '内部人员身份规则', '023': '按钮展示与授权规则', '024': '部门规则',
    '025': '人员账号操作规则', '026': '用人负责人接任规则', '027': '申请唯一关联规则',
    '028': '职位人数与发布时间规则', '029': '同一职位资料与来源更正规则',
    '030': '公共字典编辑规则', '031': '来源凭证规则', '032': '联系方式强匹配规则',
    '033': '简历自动当前规则', '034': '应聘职位固定规则', '035': '场次实际开始规则',
    '036': '筛选与邀约规则', '037': '计划与实际场次规则', '038': '评价与决策字段规则',
    '039': '任务消息与治理规则', '040': '阶段任务统计规则',
    '041': '内推渠道',
}
DECISION_REF = r'(?<![A-Za-z0-9_-])D-\d{3}(?:(?:至|到|[／/、])(?:D-)?\d{2,3})*'


def reader_text(text):
    # 删除纯溯源句，正文中的规则和适用条件继续保留。
    text = re.sub(r'以\[决策[^\]]*\]\([^)]*\)为当前业务基线。', '', text)
    text = re.sub(r'本节依据 D-016 及其细化的 [^。]*?，遵循', '本节遵循', text)
    text = re.sub(r'^D-026定义用人负责人接任[^\n]*$', '', text, flags=re.M)
    text = text.replace('本节按 D-016 允许', '本节允许')
    text = re.sub(r'本节结合\[产品决策 D-015\]\([^)]*\)的一面跳过例外，多轮评价以 D-014 为基础，当前通过／淘汰及CTO不参与规则以\[产品决策 D-019\]\([^)]*\)和 E.4 为准。',
                  '一面跳过、多轮评价、通过／淘汰及CTO不参与按下方对应规则执行。', text)
    text = re.sub(r'；F-0[1-8]本期产品定义[^。]*。', '。', text)
    text = re.sub(r'剩余实施与真实交接按TODO执行；不能因矩阵已存在把所有按钮判为可实施。', '', text)
    text = text.replace('后续保留期限、归档和物理清理须在公共规范及产品决策中确认后再实施。',
                        '正式发布前须明确保留期限、归档、物理清理及相应操作授权。')
    text = re.sub(r'本节以\[产品决策[^\]]*\]\([^)]*\)为准。\n?', '', text)
    text = re.sub(r'；已确认业务依据' + DECISION_REF + r'。', '。', text)
    text = re.sub(r'[（(]' + DECISION_REF + r'(?:已确认)?[）)]', '', text)

    def business_name(match):
        ids = re.findall(r'\d{2,3}', match[0])
        unknown = [i for i in ids if i.zfill(3) not in DECISION_NAMES]
        if unknown:
            raise ValueError(f'未知决策编号，须先改写面向读者的正文：{unknown}')
        names = list(dict.fromkeys(DECISION_NAMES[i.zfill(3)] for i in ids))
        if len(names) > 2:
            raise ValueError(f'多项决策不能拼接为交付正文，须按业务改写：{match[0]}')
        return '及'.join(names)

    # 内部决策链接不导出，含义在正文中直接表达。
    text = re.sub(r'\[([^\]]*)\]\([^)]*产品探索/产品决策记录\.md[^)]*\)',
                  lambda m: re.sub(DECISION_REF, business_name, m[1]).replace('产品决策 ', '').replace('决策', ''), text)
    text = re.sub(DECISION_REF, business_name, text)
    text = re.sub(r'(?:已确认|正式已确认)业务依据', '业务依据', text)
    text = text.replace('规则规则', '规则').replace('业务依据相关业务规则', '业务定义')
    text = text.replace('、TS-DUP-020', '，对应验收TS-DUP-020')
    text = re.sub(r'\(\s*\)', '', text)
    return text


def requirement_reader_text(text):
    """页面说明保留业务规则；工程追踪编号由验收附件承载。"""
    result = []
    removed = []
    in_fence = False
    for line in text.splitlines():
        if line.startswith('```'):
            in_fence = not in_fence
        if in_fence or line.startswith('<a '):
            result.append(line)
            continue
        if line.startswith('|'):
            cells = [cell.strip() for cell in line.split('|')[1:-1]]
            if any(cell == '按钮编号' for cell in cells):
                removed = [0, len(cells) - 1]
            elif not cells or not all(cell.startswith('---') for cell in cells) and not removed:
                removed = [i for i, cell in enumerate(cells) if cell in ('验收场景', '故事／主要场景')]
            if removed:
                cells = [cell for i, cell in enumerate(cells) if i not in removed]
            line = '| ' + ' | '.join(cells) + ' |'
        else:
            removed = []
        # Preserve linked business names and their destinations, not visible tracking IDs.
        parts = re.split(r'(\[[^\]]*\]\([^)]*\))', line)
        pattern = r'(?:US-\d+|TS-[A-Z]+-\d+|RB-\d+[A-Z]?|TR-[A-Z]+-\d+)(?:(?:[／/、,]|至)(?:(?:US-|TS-[A-Z]+-|RB-|TR-[A-Z]+-)?\d+[A-Z]?))*'
        for i in range(0, len(parts), 2):
            parts[i] = re.sub(pattern, '', parts[i])
        line = ''.join(parts)
        line = line.replace('最小配置方案', '面试流程配置').replace('最小配置矩阵', '默认流程配置表').replace('按最小配置支持组', '按默认流程支持的职级组').replace('按最小配置填写', '按场次字段要求填写').replace('最小配置', '面试流程配置')
        line = re.sub(r'(?:验收引用|正式场景|验收见)\s*[；，、。]', '', line)
        line = re.sub(r'(?:验收引用|验收见|正式场景|关联)\s*$', '', line)
        line = re.sub(r'验收入口见(\[[^\]]+\]\([^)]*\))中的\s*和\s*。', r'详细验收步骤见\1。', line)
        line = line.replace('HR负责人既有动作沿。', '').replace('正式场景待执行。', '').replace('，均待执行。', '。')
        line = re.sub(r'[；，、]{2,}', '；', line)
        line = re.sub(r'^\s*(?:关联|验收引用|正式场景|验收见|及|与|及对应追踪|与对应追踪)?[\s；，、。及与]*$', '', line)
        if line:
            result.append(line)
        elif not result or result[-1] != '':
            result.append('')
    result_text = '\n'.join(result) + '\n'
    if re.search(r'(?<![A-Za-z0-9_-])(?:RB-\d|US-\d|TS-[A-Z]+-\d|TR-[A-Z]+-\d)', re.sub(r'<a[^>]*>.*?</a>', '', result_text)):
        raise ValueError('招聘交付正文仍含工程追踪编号')
    return result_text


def expand_delivery_sections(source):
    """从既有权威章节组成页面交付正文，链接先归一到组合源位置。"""
    pattern = r'<!-- delivery:include source="([^"]+)" section="([^"]+)" title="([^"]+)" -->'

    def include(match):
        included = (source.parent / match[1]).resolve()
        if not included.is_relative_to(PRODUCT.resolve()):
            raise ValueError('交付章节必须来自产品权威目录')
        content = included.read_text()
        heading = match[2]
        if content.splitlines().count(heading) != 1:
            raise ValueError(f'{included.name}章节缺失或不唯一：{heading}')
        start = content.index(heading + '\n')
        old_level = len(heading) - len(heading.lstrip('#'))
        rest = content[start + len(heading) + 1:]
        stop = re.search(r'^#{1,' + str(old_level) + r'} ', rest, re.M)
        fragment = heading + '\n' + (rest[:stop.start()] if stop else rest)
        title = match[3]
        numbering = title.split(' ', 1)[0]
        level = len(numbering.split('.')) + 1
        child_counts = {}
        lines = []
        for line in fragment.splitlines():
            h = re.match(r'^(#{1,6}) (.*)$', line)
            if h:
                current_level = len(h[1]) + level - old_level
                if len(h[1]) == old_level:
                    line = '#' * level + ' ' + title
                else:
                    child_level = len(h[1]) - old_level
                    child_counts[child_level] = child_counts.get(child_level, 0) + 1
                    for key in list(child_counts):
                        if key > child_level:
                            del child_counts[key]
                    prefix = numbering + ''.join('.' + str(child_counts.get(i, 1)) for i in range(1, child_level + 1))
                    label = re.sub(r'^\d+(?:\.\d+)* ', '', h[2])
                    line = '#' * min(current_level, 6) + ' ' + prefix + ' ' + label
            lines.append(line)
        fragment = '\n'.join(lines)
        # A following section's anchor is outside the included section.
        fragment = re.sub(r'(?:\s*<a id="[^"]+"></a>)+\s*$', '', fragment)
        fragment = re.sub(r'<!-- 内部追踪：.*? -->', '', fragment)

        def rebase(link):
            path, separator, anchor = link[2].partition('#')
            if re.match(r'^[a-zA-Z]+:', path):
                return link[0]
            target = (included.parent / path).resolve() if path else included
            local_sections = {
                ('人员账号与角色字段定义.md', '三人员与组织字段'): 'person-fields',
                ('人员账号与角色字段定义.md', 'organization-account'): 'department-management',
                ('页面与交互基线.md', '六部门列表页及新增编辑功能'): 'department-management',
                ('待办消息字典与审计字段定义.md', '三字典字段与管理'): 'dictionary-fields',
            }
            local_anchor = local_sections.get((target.name, anchor))
            if source.name == '基础资料管理产品需求文档.md' and local_anchor:
                return '[' + link[1] + '](#' + local_anchor + ')'
            relative = os.path.relpath(target, source.parent)
            return '[' + link[1] + '](' + relative + ('#' + anchor if separator else '') + ')'

        fragment = re.sub(r'\[([^\]\n]*)\]\(([^)\n]+)\)', rebase, fragment)
        if included.name == '页面与交互基线.md':
            fragment = fragment.replace('第1.1节', '第6.1.1节')
        return fragment.strip()

    text = re.sub(pattern, include, source.read_text())
    if '<!-- delivery:include' in text:
        raise ValueError('交付引用指令未完整展开')
    return text


def delivery_scope_text(text, destination):
    """内部维护方法不进入正式需求；当前业务要求与验收保留。"""
    if destination.name == '字段与表单校验规范.md':
        text = re.sub(r'## 模块例外\n.*?(?=## 追加公共验收规则)',
                      '## 规则适用\n\n字段格式与错误反馈按本规范执行；模块PRD中更严格的业务条件与本规范共同校验。\n\n', text, flags=re.S)
    elif destination.name == '权限与数据治理规范.md':
        text = re.sub(r'### 3.3 PRD 表述与验收格式\n.*?(?=<a id="34-)',
                      '### 3.3 授权验收要求\n\n每项操作验证合法授权、缺少角色、记录越界、指派失效及状态不允许等适用路径。角色、部门及指派变化后重新判断当前授权；页面、列表、搜索、工作台和附件的拒绝反馈均不得泄露敏感信息。\n\n', text, flags=re.S)
        text = re.sub(r'### 4.1 产品文档与参考资料脱敏\n.*?(?=## 五、)', '', text, flags=re.S)
        text = re.sub(r'## 七、模块落地要求\n.*?(?=招聘管理模块的)', '## 七、招聘业务规则\n\n', text, flags=re.S)
        text = text.replace('- 模块 PRD 必须提供角色、数据范围和操作权限矩阵，不得只描述页面可见性。\n', '')
        text = text.replace('模块需要区分“允许”“禁止”和“待确认”，并将待确认项列入需求评审。', '未明确的授权范围须在开放对应操作前确认。')
        text = text.replace('模块按钮矩阵明确页面、动作、授权引用、业务条件、确认、成功／失败反馈及验收。', '')
    if destination.name in ('招聘管理PRD.md', '基础资料管理PRD.md') and '## 版本与变更记录' in text:
        body, history = text.split('## 版本与变更记录', 1)
        rows = re.findall(r'^\| (\d+\.\d+)[^\n]*$', history, re.M)
        current = max(rows, key=lambda v: tuple(map(int, v.split('.'))))
        latest = next(line for line in history.splitlines() if line.startswith('| ' + current + '／'))
        text = body.rstrip() + '\n\n## 版本与变更记录\n\n| 版本／日期 | 变更与交付影响 |\n| --- | --- |\n' + latest + '\n'
    return text


def export_text(source, destination):
    text = expand_delivery_sections(source)
    if source.name == '产品总览.md':
        text = text.split('<!-- delivery:overview:start -->', 1)[1].split('<!-- delivery:overview:end -->', 1)[0].strip()
        text = '# 产品项目总览\n\n' + text

    def replace_link(match):
        path, separator, fragment = match[2].partition('#')
        if not path or re.match(r'^[a-zA-Z]+:', path):
            return match[0]
        target = (source.parent / path).resolve()
        target = SOURCES.get(target, target)
        relative = os.path.relpath(target, destination.parent)
        return '[' + match[1] + '](' + relative + ('#' + fragment if separator else '') + ')'

    text = re.sub(r'\[([^\]\n]*)\]\(([^)\n]+)\)', replace_link, text)
    text = re.sub(r'<!-- 内部追踪：.*? -->', '', text)
    text = reader_text(text)
    text = delivery_scope_text(text, destination)
    if destination.name in ('招聘管理PRD.md', '基础资料管理PRD.md'):
        text = requirement_reader_text(text)
    if re.search(r'\bD-\d+', text) or '产品探索/产品决策记录.md' in text:
        raise ValueError(f'{destination.name}仍含内部决策溯源信息')
    return text.rstrip() + '\n'


def export_readme(generated):
    """入口版本读取已生成文档元信息，避免独立维护后漂移。"""
    versions = {}
    for label, name in [('项目总览', '产品项目总览.md'), ('基础资料PRD', '基础资料管理PRD.md'),
                        ('招聘PRD', '招聘管理PRD.md'), ('验收附件', '招聘管理验收附件.md')]:
        match = re.search(r'(?:版本／(?:日期|更新时间).*?)(\d+\.\d+)／', generated[(OUTPUT / name).resolve()])
        if not match:
            raise ValueError(f'{name}缺少版本元信息')
        versions[label] = match[1]
    prototype = (OUTPUT / 'prototype/index.html').read_text()
    prototype_version = re.search(r'原型 · v(\d+\.\d+)', prototype)
    if not prototype_version:
        raise ValueError('原型缺少版本信息')
    baseline = '、'.join(label + version for label, version in versions.items()) + '、原型' + prototype_version[1]
    return f"""# 产品交付与宣讲入口

本目录提供基础资料、平台支撑及招聘MVP需求，供研发、测试、设计和业务评审使用。

当前版本：{baseline}。宣讲从《产品项目总览》开始，按下表顺序展开，页面操作配合原型演示。

| 顺序 | 文档 | 内容 |
| --- | --- | --- |
| 1 | [产品项目总览](产品项目总览.md) | 产品目标、范围、角色、业务架构、数据流与实施依赖 |
| 2 | [基础资料管理PRD](基础资料管理PRD.md) | 人员、账号、部门、字典，以及登录、工作台、消息、审计和回收页面 |
| 3 | [招聘管理PRD](招聘管理PRD.md) | 职位与应聘资料、筛选邀约、场次、评价决策、待办提醒及异常 |
| 4 | [招聘管理验收附件](招聘管理验收附件.md) | 需求追踪、测试步骤和预期结果 |

公共校验、授权、审计和数据生命周期要求见[字段与表单校验规范](公共规范/字段与表单校验规范.md)及[权限与数据治理规范](公共规范/权限与数据治理规范.md)。统计复算与试点效果评估见[指标与试点基线](指标与试点基线.md)。

[可点击原型](prototype/index.html)使用虚构数据，刷新后重置。用于演示页面及样例流程；多轮快照、换人／替代、前轮迟交、CTO不参与、合并、真实通知与服务端鉴权未完整模拟，以PRD及验收附件为实现依据。

内推资料接收与实际沟通确认方式尚待业务落实，影响对应渠道的实施。需求联合评审与实现验收尚未执行。
"""


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    from check_product_delivery import review
    generated = {destination.resolve(): export_text(source, destination)
                 for source, destination in SOURCES.items()}
    generated[(OUTPUT / 'README.md').resolve()] = export_readme(generated)
    documents = {path.resolve(): path.read_text() for path in OUTPUT.rglob('*.md')}
    documents.update(generated)
    result = review(documents, OUTPUT)
    if result['errors']:
        raise ValueError('交付预检失败，未写入生成文件：\n' + '\n'.join(result['errors']))
    for destination, text in generated.items():
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(text)
    for note in result['review_notes']:
        print('阅读提示：' + note)
    print('已更新正式需求及公共规范、指标配套；本地引用均在output交付包内。')


if __name__ == '__main__':
    main()
