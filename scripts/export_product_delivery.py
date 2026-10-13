"""从权威正文生成交付目录；输出不直接编辑，业务规则只维护一处。"""
from pathlib import Path
import os
import re

ROOT = Path(__file__).resolve().parents[1]
PRODUCT = ROOT / 'docs/product'
OUTPUT = ROOT / 'docs/output'
SOURCES = {
    PRODUCT / '产品总览.md': OUTPUT / '产品项目总览.md',
    PRODUCT / '模块/招聘管理/产品需求文档.md': OUTPUT / '招聘管理PRD.md',
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
        names = list(dict.fromkeys(DECISION_NAMES.get(i.zfill(3), '相关业务规则') for i in ids))
        return '及'.join(names) if len(names) <= 2 else '相关业务规则'

    # 内部决策链接不导出，含义在正文中直接表达。
    text = re.sub(r'\[([^\]]*)\]\([^)]*产品探索/产品决策记录\.md[^)]*\)',
                  lambda m: re.sub(DECISION_REF, business_name, m[1]).replace('产品决策 ', '').replace('决策', ''), text)
    text = re.sub(DECISION_REF, business_name, text)
    text = re.sub(r'(?:已确认|正式已确认)业务依据', '业务依据', text)
    text = text.replace('规则规则', '规则').replace('业务依据相关业务规则', '业务定义')
    text = text.replace('、TS-DUP-020', '，对应验收TS-DUP-020')
    text = re.sub(r'\(\s*\)', '', text)
    return text


def export_text(source, destination):
    text = source.read_text()
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
    text = reader_text(text)
    if re.search(r'\bD-\d+', text) or '产品探索/产品决策记录.md' in text:
        raise ValueError(f'{destination.name}仍含内部决策溯源信息')
    return text.rstrip() + '\n'


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for source, destination in SOURCES.items():
        destination.write_text(export_text(source, destination))
    print('已更新输出目录中的产品项目总览、招聘PRD及验收附件。')


if __name__ == '__main__':
    main()
