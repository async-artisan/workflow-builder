# Workflow Builder

一个面向 Codex 与 Agent Skills 的通用业务工作流搭建、执行、审计与复用 Skill。

它把真实业务目标落实为可执行、可检查、可恢复、可复用的工作流，并严格区分设计、试跑、人工验收、复用验证和交接验证，避免把模板或 AI 自评当作运行证据。

## 能力

- 设计 / 搭建 / 执行 / 审计四种请求路由
- 工作流卡片、最小闭环与运行前就绪检查
- 人工门禁、异常恢复、权限边界与证据分级
- 平台选择矩阵和可插拔平台适配器契约
- 参数化 SOP 模板与 SOP → Agent Skill 生成器
- 人工意见、检查证据和签核记录模板
- 知识库检索、版本更新与跨平台迁移验证

## 目录

```text
workflow-builder/
├── SKILL.md
├── agents/openai.yaml
├── assets/
│   ├── sop.template.md
│   └── verification-signoff.template.md
├── references/
│   ├── workflow-method.md
│   ├── platform-adapters.md
│   ├── sop-format.md
│   └── knowledge-base.md
└── scripts/
    └── sop_to_skill.py
```

## 安装

将本仓库目录复制或链接到 Codex Skills 目录：

```text
~/.codex/skills/workflow-builder/
```

在 Windows 上通常为：

```text
C:/Users/<用户名>/.codex/skills/workflow-builder/
```

新建 Codex 会话后，可这样调用：

```text
请使用 $workflow-builder，帮我把这个重复业务任务搭建为可验证、可复用的工作流。
```

也可以请求设计、执行或审计：

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

## 验收与签核

复制 `assets/verification-signoff.template.md` 到业务项目，记录：

- 检查方法、实际结果与证据位置
- 问题严重度、复现方式和修订结果
- 人工验收原话及处理记录
- 签核版本、范围、条件和授权动作
- 各证据状态及后续行动

沉默不视为批准，Agent 互审不替代人工业务验收。实质变更后，需要重新验收相关环节。

## 许可证

[MIT](LICENSE)
