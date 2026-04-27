# Codex Claude Cross Review

让 Codex 和 Claude Code 对同一个任务做双模型交叉评审的 skill。

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

依赖：`python3`、`git`、`codex`、`claude`。脚本本身只用 Python 标准库。

## License

MIT
