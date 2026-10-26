# Workflow Builder

一个面向任何智能体的通用业务工作流搭建、执行、审计与复用 Skill。核心采用 Markdown、开放 Agent Skills 结构和可选 Python 标准库脚本，不绑定 Codex、Claude 或任何特定模型、平台。

它把真实业务目标落实为可执行、可检查、可恢复、可复用的工作流，并严格区分设计、试跑、人工验收、复用验证和交接验证，避免把模板或 AI 自评当作运行证据。

## 能力

- 设计 / 搭建 / 执行 / 审计四种请求路由
- 工作流卡片、最小闭环与运行前就绪检查
- 人工门禁、异常恢复、权限边界与证据分级
- 平台选择矩阵和可插拔平台适配器契约
- 参数化 SOP 模板与 SOP → Agent Skill 生成器
- 人工意见、检查证据和签核记录模板
- 结构化运行清单、证据状态推导和副作用对账校验
- 基线、业务 oracle、阈值和单位验收成本评测方法
- 只读 / 可逆写入 / 受限写入的风险分级与预算停止
- `release_id` 内容绑定、签核版本校验和漂移检测
- 知识库检索、版本更新与跨平台迁移验证

## 目录

```text
workflow-builder/
├── SKILL.md
├── agents/openai.yaml          # 可选宿主适配
├── assets/                    # SOP、运行清单与签核模板
├── references/                # 方法、评测、风险、发布与平台规范
├── scripts/                   # 生成、发布绑定和证据校验工具
├── evals/                     # 触发测试与业务评测用例
├── examples/                  # 合成端到端示例，不冒充真实效果
├── tests/                     # 正反向回归测试
└── .github/workflows/         # 自动校验
```

## 接入任意智能体

### 支持 Agent Skills 的宿主

将完整目录复制、链接或导入宿主的 Skills 目录，由宿主读取 `SKILL.md` 的 `name` 和 `description` 进行触发，并按需加载 `references/`、`assets/` 和 `scripts/`。

例如，Codex 可放在 `~/.codex/skills/workflow-builder/`，Claude Code 可放在 `~/.claude/skills/workflow-builder/`；其他智能体按各自的 Skill 发现或导入机制接入。`agents/openai.yaml` 只是可选的 OpenAI/Codex 展示适配，不是核心依赖，其他宿主可以忽略。

### 仅支持 Markdown 指令的宿主

将 `SKILL.md` 作为自定义指令、规则或系统提示的一部分，并确保智能体能够访问相关参考文件。不能自动加载链接资源时，按任务需要附上对应 `references/` 内容；没有脚本执行能力时，仍可使用 SOP、平台适配和验收签核方法。

### 调用示例

在支持 Skill 调用的环境中，可使用宿主对应的调用语法；也可以直接提出目标：

```text
请使用 workflow-builder，帮我把这个重复业务任务搭建为可验证、可复用的工作流。
```

在 Codex 中可写成 `$workflow-builder`。还可以请求设计、执行或审计：

```text
请使用 $workflow-builder，审计现有流程能否闭环，并给出有证据的问题清单。
```

## 参数化 SOP 与 Skill 生成

复制 `assets/sop.template.md`，填写业务目标、参数、步骤、人工门禁、输出和验证要求。格式说明见 `references/sop-format.md`。

在仓库根目录执行：

```bash
# 只检查 SOP，不写文件
python scripts/sop_to_skill.py /path/to/example.sop.md --check

# 生成 <output-dir>/<name>/SKILL.md
python scripts/sop_to_skill.py /path/to/example.sop.md --output-dir /path/to/skills
```

生成器仅使用 Python 标准库。默认不覆盖已有 `SKILL.md`；只有明确需要覆盖时才使用 `--force`。

“Skill 已生成”不代表已经安装、加载或运行验证通过。仍需在目标 Agent 环境中完成真实试跑和不同输入复跑。

## 运行证据、发布绑定与评测

复制 `assets/run-manifest.template.json` 记录运行。生成内容绑定的发布信息，再校验证据状态：

```bash
# 将实际依赖绑定到 release_id
python scripts/build_release.py workflow.sop.md SKILL.md \
  --base-dir . --output release.json

# 检查依赖是否漂移
python scripts/build_release.py --check release.json --base-dir .

# 从证据推导设计、试跑、验收、复用和交接状态
python scripts/validate_run.py /path/to/run.json --json
```

校验器会拒绝无证据完成、旧发布签核、未知外部结果直接重试和预算超限等不一致状态。它验证的是证据关联，不会自动证明证据文件真实或审批人有权限。

评测方法见 `references/evaluation.md`，风险与预算见 `references/risk-and-budgets.md`。`examples/readonly-minutes/` 和 `evals/cases/readonly-minutes.json` 提供合成示例；合成 fixture 不能冒充真实业务效果。

## 验收与签核

复制 `assets/verification-signoff.template.md` 到业务项目，记录：

- 检查方法、实际结果与证据位置
- 问题严重度、复现方式和修订结果
- 人工验收原话及处理记录
- 签核版本、范围、条件和授权动作
- 各证据状态及后续行动

沉默不视为批准，Agent 互审不替代人工业务验收。实质变更后，需要重新验收相关环节。

## 开发与回归

```bash
python scripts/check_repository.py
python -m unittest discover -s tests -v
```

GitHub Actions 会检查结构、内部链接、JSON、Python 语法、SOP 生成和正反向工具用例。跨宿主触发与真实业务效果仍需在对应环境中单独验证。

## 许可证

[MIT](LICENSE)
