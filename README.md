# Codex Claude Cross Review

让 Codex 和 Claude Code 对同一个任务做双模型交叉评审的 skill。适用于代码、架构、设计、文档、方案、分支、提交等评审场景。

## 安装

Codex 默认 skill 路径：

```bash
~/.agents/skills/codex-claude-cross-review
```

安装：

```bash
git clone https://github.com/Bryant-Yang/codex-claude-cross-review \
  ~/.agents/skills/codex-claude-cross-review
```

Claude Code 默认 skill 路径：

```bash
~/.claude/skills/codex-claude-cross-review
```

安装：

```bash
git clone https://github.com/Bryant-Yang/codex-claude-cross-review \
  ~/.claude/skills/codex-claude-cross-review
```

也可以直接把仓库地址发给 agent：

```text
请安装这个 skill：
https://github.com/Bryant-Yang/codex-claude-cross-review
```

## 触发

安装后直接自然语言触发：

```text
请用 Codex 和 Claude 双模型 review 当前改动
```

```text
请对这个架构方案做 Codex / Claude 交叉评审
```

```text
请让 Codex 和 Claude 分别 review，然后互相 challenge 对方结论
```

## 调试

直接运行脚本：

```bash
python3 ~/.agents/skills/codex-claude-cross-review/scripts/cross_review.py \
  --repo "$(pwd)" \
  --mode uncommitted
```

快速 review：

```bash
python3 ~/.agents/skills/codex-claude-cross-review/scripts/cross_review.py \
  --repo "$(pwd)" \
  --profile fast
```

深度 review：

```bash
python3 ~/.agents/skills/codex-claude-cross-review/scripts/cross_review.py \
  --repo "$(pwd)" \
  --profile deep
```

`fast`/`normal`/`deep` 默认让 Claude Code 使用脚本层面的只读工具集 `Read,Grep,Glob` 做证据核对，不开放编辑或 shell 命令。可用 `--claude-tools none` 强制只看传入的 diff/context；这种模式下脚本会要求 Claude 不尝试工具调用。只有确实需要 Claude Code 自身默认工具集时，才显式加 `--claude-tools default`；这依赖 Claude Code 自身权限配置，不是脚本层面的只读沙箱。

带最终仲裁（`--arbiter` 可选 `none`/`codex`/`claude`，默认 `none`）：

```bash
python3 ~/.agents/skills/codex-claude-cross-review/scripts/cross_review.py \
  --repo "$(pwd)" \
  --profile deep \
  --arbiter codex
```

Claude Code 路径下运行：

```bash
python3 ~/.claude/skills/codex-claude-cross-review/scripts/cross_review.py \
  --repo "$(pwd)" \
  --mode uncommitted
```

报告默认在：

```text
.agent-review/<timestamp>/
```

常看：

- `progress.log`
- `review-summary.md`
- `arbitration.md`
- `recommended-actions.md`
- `findings.json`
- `reviewer-outputs.md`：只有需要完整 reviewer 原文时再看

依赖：`python3 >= 3.10`、`git`、`codex`、`claude`。脚本本身只用 Python 标准库。

## License

MIT
