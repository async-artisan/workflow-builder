---
name: example-workflow
description: 说明适用任务、触发方式和预期结果。
version: 1.0.0
---

# 工作流名称

## Overview

说明业务目标、使用对象、触发方式、范围和预期价值。列出明确不处理的事项。

## Parameters

| Name | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| task_name | string | yes | — | 本次任务或运行名称 |
| source_material | path | yes | — | 已提供的真实输入位置 |
| audience | string | no | internal | 结果使用对象 |
| mode | enum | no | draft | draft 或 live；未经授权不得执行外部发布 |

参数名使用 `snake_case`。Required 只填 `yes` 或 `no`；无默认值填 `—`。Type 使用 `string`、`text`、`integer`、`number`、`boolean`、`enum`、`path` 或 `json`。枚举值和额外约束在 Description 中说明。

## Inputs

列出必需和可选输入、来源、版本及就绪条件。区分待提供、已收到、已读取和不可用。

## Steps

### 1. 步骤名称

- **Action：** 说明要执行的动作。
- **Constraints：** 使用 MUST、SHOULD、MAY 写明必要约束。
- **Output：** 说明本步可检查产物及保存位置。
- **On failure：** 说明重试、降级、跳过、恢复或转人工方式。

### 2. 下一步骤

按需增加步骤。每一步保持前置条件明确、产物可检查、失败有去向。

## Human Gates

列出需要人工决定或接受的方向、冲突、例外、外部副作用和最终验收。写明审批人、审批内容和批准后的下一步；没有人工门禁时说明理由。

## Outputs

列出最终交付物、格式、保存位置、验收标准和复用入口。

## Validation

列出结构检查、真实试跑、异常测试、人工验收和不同输入复跑的证据要求。区分已设计、已试跑、已人工验收、已复用验证和已交接验证。

## Troubleshooting

记录常见缺口、工具失败、权限问题、部分完成和重复执行的处理方式。不得写入密钥、令牌或私密材料。
