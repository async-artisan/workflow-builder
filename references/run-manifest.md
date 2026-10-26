# 运行清单与证据校验

需要持久化运行、恢复中断、处理外部写入或核对证据状态时使用。复制 [运行清单模板](../assets/run-manifest.template.json)，并用 [发布绑定工具](release-binding.md) 生成当前 `release_id` 和文件摘要。

## 记录原则

- 每个步骤使用稳定的 `step_id`；完成时保存输入/输出 SHA-256、尝试次数和证据位置。
- 写入步骤保存副作用意图、幂等键或补偿方式、外部状态和回执。外部结果未知时先对账，不直接完成或重试。
- 关键检查通过时必须有证据；失败和未运行不能被平均值抵消。
- 人工批准保存审批人、明确原话、范围、证据和绑定的 `release_id`。
- 预算超过上限时标记 `budget_exhausted`，停止新的调用与写入并保留恢复入口。

## 状态推导

`scripts/validate_run.py` 不信任手工声明，按证据重新推导：

| 状态 | 最低证据 |
| --- | --- |
| `designed` | 有效发布绑定、工作流名称和版本 |
| `tested` | 非设计模式、真实输入摘要和具有证据的完成步骤 |
| `human_approved` | 当前 release 的有效人工批准或条件批准 |
| `reuse_validated` | 已试跑、不同输入、基线、冻结阈值达成且关键检查全部通过 |
| `handoff_validated` | 独立会话已验证入口发现和继续执行，并有证据 |

`declared_status` 必须与推导结果一致，避免漏记或过度声明。

## 执行校验

```bash
python scripts/validate_run.py /path/to/run.json
python scripts/validate_run.py /path/to/run.json --json
```

校验失败时按错误补证据或修正声明，不要仅修改文本绕过规则。

该工具验证的是清单结构、证据关联和状态一致性，不能自动证明证据文件本身真实、审批人确有权限或外部系统状态正确。这些仍需回读原始证据、查询平台或由负责人核实。
