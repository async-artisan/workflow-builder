---
name: readonly-minutes
description: 将会议纪要整理为决定事项、行动项和未决项；用于只读、无外部写入的会议整理与评测示例。
version: 1.0.0
---

# 只读会议纪要整理

## Overview

把已提供的会议纪要整理为可核查的决定事项、行动项和未决项。仅生成草稿，不写回外部系统，不推测缺失负责人、日期或决定。

## Parameters

| Name | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| source_material | path | yes | — | 已读取的会议纪要位置 |
| audience | string | no | project_team | 结果使用对象 |

## Inputs

必需输入为已读取的会议纪要。记录输入来源和摘要；合成材料必须明确标注，不得冒充真实业务试跑。

## Steps

### 1. extract-decisions

- **Action：** 提取明确决定和范围外事项。
- **Constraints：** MUST 保留否定和条件；MUST NOT 把未决事项写成决定。
- **Output：** 决定事项清单。
- **On failure：** 无法确认时放入未决项。

### 2. extract-actions

- **Action：** 提取行动、负责人和日期，并核对未决项。
- **Constraints：** MUST 保留原始责任分配；MUST NOT 编造缺失字段。
- **Output：** 行动项、未决项和整理结果。
- **On failure：** 保留原文位置和待人工确认项。

## Human Gates

仅生成只读草稿，无强制发布门禁。业务负责人验收内容是否忠于原文；任何外部写回都应另建更高风险工作流。

## Outputs

输出决定事项、行动项和未决项。验收以 `evals/cases/readonly-minutes.json` 的业务断言和实际输入要求为准。

## Validation

保存输入摘要、输出摘要和逐项断言证据。真实复用验证还需使用未参与调参的不同输入、实际业务基线和预先冻结的阈值。

## Troubleshooting

纪要缺少负责人或日期时保留空缺并转人工；材料不可读取时停止并报告；不要根据上下文猜测上线日期或功能范围。
