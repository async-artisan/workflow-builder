# 示例与证据边界

`readonly-minutes/` 是一个完整的只读 SOP 示例，包含合成输入、预期结果和对应评测用例。它演示如何组织业务断言、人工验收和运行证据。

这些材料是**合成 fixture**，用于验证生成器、发布绑定和运行清单机制，不构成真实业务效果、跨智能体兼容性或复用稳定性的证据。真实项目应替换为已获授权的实际输入，并保存真实运行结果与基线。

在仓库根目录可执行：

```bash
# 校验示例 SOP
python scripts/sop_to_skill.py examples/readonly-minutes/workflow.sop.md --check

# 将 SOP、输入、预期结果和评测用例绑定为候选发布
python scripts/build_release.py \
  examples/readonly-minutes/workflow.sop.md \
  examples/readonly-minutes/input.md \
  examples/readonly-minutes/expected.md \
  evals/cases/readonly-minutes.json \
  --base-dir . --output examples/readonly-minutes/release.json
```

生成 release 后，将其嵌入实际运行清单。不要把仅由模板产生的状态当成已完成试跑。
