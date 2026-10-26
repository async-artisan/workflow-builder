# 发布内容绑定与漂移检测

需要试跑、签核、复用验证、灰度或审计追溯时使用。`release_id` 将运行和批准绑定到一组具体内容，避免源文件改变后仍沿用旧证据。

## 纳入发布的内容

按工作流实际依赖选择：

- SOP 源文件与生成的 `SKILL.md`；
- 运行清单规范、平台适配器和必要模板；
- 工具配置、权限范围或连接器版本的可获得快照；
- 知识库、索引或业务规则的版本快照；
- 评测计划和阈值。

不要为绑定而复制密钥或个人敏感信息。无法获得的模型版本等信息记录“未知”，不要猜测。发布绑定用于追溯，不代表非确定性模型可以逐字复现。

## 生成与检查

在仓库或业务项目根目录执行：

```bash
# 生成 release JSON；路径必须位于 base-dir 内
python scripts/build_release.py workflow.sop.md SKILL.md adapter.json \
  --base-dir . --output release.json

# 将 release 对象嵌入运行清单和签核记录后，再检查内容漂移
python scripts/build_release.py --check release.json --base-dir .
```

生成器计算每个文件的 SHA-256，再对排序后的路径和摘要计算 `release_id`。默认不覆盖已有输出；明确需要覆盖时使用 `--force`。

## 使用约束

- 任一纳入文件变化后生成新的 `release_id`，重新确定受影响的评测和人工验收。
- 运行清单中的批准必须匹配当前 `release_id`；旧批准不能自动覆盖新产物。
- 源 SOP 与生成 Skill 都纳入绑定，以便发现只修改一边造成的漂移。
- 发布 ID 相同只表示纳入文件内容一致；外部环境、权限和模型行为仍需单独核实。
