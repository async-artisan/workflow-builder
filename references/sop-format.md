# 标准 SOP 与 Skill 生成

需要把已验证流程沉淀为可参数化 SOP，或从 SOP 生成独立 Agent Skill 时使用。先复制 [SOP 模板](../assets/sop.template.md) 并替换业务内容；不要为了套模板改写已验证的业务事实。

## 格式约定

SOP 文件使用 `<workflow-name>.sop.md`，包含：

1. **Frontmatter：** `name`、`description`、`version` 必填。`name` 使用小写字母、数字和连字符，并同时作为生成目录名。
2. **Overview：** 目标、对象、触发、范围和边界。
3. **Parameters：** 使用固定表格 `Name / Type / Required / Default / Description`。参数名使用 `snake_case`，必填列只写 `yes/no`，类型使用 `string/text/integer/number/boolean/enum/path/json`。
4. **Inputs 与 Steps：** 输入标明来源和就绪状态；每步写动作、约束、产物和失败去向。
5. **Human Gates：** 人工审批人、内容、范围和批准后动作。没有门禁时说明理由。
6. **Outputs 与 Validation：** 输出、验收标准和各证据层级。
7. **Troubleshooting：** 常见失败、恢复和人工兜底，不保存秘密信息。

约束词保持一致：

- **MUST / MUST NOT：** 不满足就不能继续或不能声称完成。
- **SHOULD / SHOULD NOT：** 默认遵循；偏离时记录理由和影响。
- **MAY：** 可选项，不应变成隐含的必需步骤。

参数只描述复用时真正变化的输入。把稳定业务规则留在步骤或项目规则中，避免把所有内容都参数化。敏感值使用安全配置引用，不将真实密钥写进参数默认值或示例。

## 验证与生成

在本 Skill 目录执行：

```bash
# 只检查格式，不写文件
python scripts/sop_to_skill.py /path/to/example.sop.md --check

# 生成 <output-dir>/<name>/SKILL.md
python scripts/sop_to_skill.py /path/to/example.sop.md --output-dir /path/to/skills

# 明确允许覆盖同名生成文件时才使用
python scripts/sop_to_skill.py /path/to/example.sop.md --output-dir /path/to/skills --force
```

生成器仅使用 Python 标准库，执行以下检查：

- frontmatter 和必需章节完整；
- Skill 名称和参数名合法，参数无重复；
- 参数类型及 `yes/no` 标记有效；
- 输出目录不发生名称穿越，已有文件默认不被覆盖。

生成结果保留 SOP 正文，并写入符合 Agent Skills 约定的 `name` 和 `description`。生成器检查的是结构和格式，不验证业务正确性、工具连接或实际可运行性。

## 生成后的必要动作

1. 阅读生成的 `SKILL.md`，确认触发描述不会与其他 Skill 冲突。
2. 检查参数是否足以复用，步骤是否仍与真实运行记录一致。
3. 在目标 Agent 环境按该平台的安装方式启用；复制文件不等于已经自动加载。
4. 用真实输入试跑，再用不同输入复跑。分别报告“Skill 已生成、已加载、已试跑、已复用验证”。
5. 修改时以 `.sop.md` 为源重新生成，或明确改为直接维护 Skill；避免两边独立修改造成漂移。
