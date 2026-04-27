# Codex Claude Cross Review

让 Codex 和 Claude Code 对同一个任务做交叉评审的本地 review workflow。

它可以作为 Codex skill 使用，也可以在 Claude Code 里直接按这个仓库的说明运行脚本。

它适合用来 review：

- 当前代码改动
- branch / commit / PR
- 架构方案
- 设计方案
- 文档和验收说明

## 安装

把这个 GitHub 仓库交给你的 agent，让它安装或使用即可。

Codex 里可以这样说：

```text
请安装这个 Codex skill：
https://github.com/Bryant-Yang/codex-claude-cross-review
```

Claude Code 里可以这样说：

```text
请使用这个仓库里的 cross review workflow：
https://github.com/Bryant-Yang/codex-claude-cross-review
安装到本机后，用它来让 Codex 和 Claude Code 双模型 review 当前项目。
```

如果手动安装，放到 Codex skills 目录：

```bash
mkdir -p ~/.agents/skills
git clone https://github.com/Bryant-Yang/codex-claude-cross-review \
  ~/.agents/skills/codex-claude-cross-review
```

如果只想在 Claude Code 里当普通工具用，也可以 clone 到任意目录：

```bash
git clone https://github.com/Bryant-Yang/codex-claude-cross-review
```

## 怎么触发

安装后，直接用自然语言说你要“双模型 review”或“Codex 和 Claude 交叉评审”。

例子：

```text
请用 Codex 和 Claude 双模型 review 当前改动
```

```text
请交叉评审这个架构方案
```

```text
请让 Codex 和 Claude 互相 challenge 对方的 review 结论
```

```text
请用这个 skill review 当前分支相对 main 的改动
```

在 Claude Code 里也可以这样说：

```text
请用 codex-claude-cross-review 这个仓库里的脚本，双模型 review 当前改动
```

skill 会自动判断是代码、设计、架构、文档还是混合 review。  
有 diff 时会优先保留 diff；需要整体上下文时会附加仓库上下文。

## 输出在哪里

默认输出到当前仓库：

```text
.agent-review/<timestamp>/
```

常看的三个文件：

- `progress.log`：执行过程
- `review-summary.md`：每轮摘要
- `arbitration.md`：最终仲裁结论

默认只保留最近 10 次脚本生成的报告。

## 调试

如果你想直接跑脚本：

```bash
python3 ~/.agents/skills/codex-claude-cross-review/scripts/cross_review.py \
  --repo "$(pwd)" \
  --mode uncommitted
```

如果是在 Claude Code 里 clone 到普通目录，把脚本路径换成实际路径即可：

```bash
python3 /path/to/codex-claude-cross-review/scripts/cross_review.py \
  --repo "$(pwd)" \
  --mode uncommitted
```

常用参数：

```bash
--mode base --base main       # review 当前分支相对 main 的 diff
--mode commit --commit HEAD   # review 某个 commit
--rounds 3                    # 多跑一轮最终收敛
--skip-claude                 # Claude 不可用时只跑 Codex
--skip-codex                  # Codex 不可用时只跑 Claude
--no-prune-reports            # 保留全部报告
```

依赖：

- `python3`
- `git`
- `codex`
- `claude`

脚本本身只用 Python 标准库。

## 安全边界

- 默认只 review，不改文件、不提交代码。
- Codex 使用 read-only sandbox。
- Claude 默认不启用工具调用。
- `.agent-review/` 不会污染后续 review。
- untracked symlink 不会被跟随读取。

## License

MIT
