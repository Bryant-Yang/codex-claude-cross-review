# Codex Claude Cross Review

一个让 Codex 和 Claude Code 对同一份代码、设计、架构方案或文档做交叉评审的 Codex skill。

它的核心流程很简单：

1. Codex 和 Claude Code 先并行独立 review。
2. 第二轮互相挑战对方结论。
3. 可选第三轮只收敛争议和新增高风险问题。
4. 最终生成结构化报告，区分确认问题、驳回问题、需要人工判断的问题。

## 适合用来做什么

- 代码改动 review
- 分支 / commit / PR 前置 review
- 架构方案 review
- 产品设计 / 交互设计 review
- 文档和验收说明 review
- 两个 AI reviewer 结论不一致时做交叉验证

## 依赖

脚本本身只使用 Python 标准库。

需要本机已经可用：

- `python3`
- `git`
- `codex`
- `claude`

如果其中一个 reviewer 不可用，脚本会把这一侧标记为 `BLOCKED`，仍然保存另一侧结果。

## 安装

把整个目录放到 Codex skills 目录：

```bash
mkdir -p ~/.agents/skills
cp -R codex-claude-cross-review ~/.agents/skills/
```

如果你已经在 `~/.agents/skills/codex-claude-cross-review` 下，可以直接使用。

## 基本用法

Review 当前未提交改动：

```bash
python3 ~/.agents/skills/codex-claude-cross-review/scripts/cross_review.py \
  --repo "$(pwd)" \
  --mode uncommitted \
  --task "Review the current changes."
```

Review 分支相对 `main` 的差异：

```bash
python3 ~/.agents/skills/codex-claude-cross-review/scripts/cross_review.py \
  --repo "$(pwd)" \
  --mode base \
  --base main
```

Review 某个 commit：

```bash
python3 ~/.agents/skills/codex-claude-cross-review/scripts/cross_review.py \
  --repo "$(pwd)" \
  --mode commit \
  --commit HEAD
```

做三轮交叉评审：

```bash
python3 ~/.agents/skills/codex-claude-cross-review/scripts/cross_review.py \
  --repo "$(pwd)" \
  --rounds 3
```

## Scope 和 Review Type

默认 `--scope auto`：

- 有实际 diff 时，优先保留 diff。
- 如果任务需要整体、设计、架构或文档视角，会使用 `diff+full`：真实 diff 加选中的仓库上下文。
- 没有 meaningful diff 时，才使用 full-context review。

默认 `--review-type auto`，会自动选择：

- `code`
- `design`
- `architecture`
- `documentation`
- `mixed`

也可以手动指定：

```bash
python3 ~/.agents/skills/codex-claude-cross-review/scripts/cross_review.py \
  --repo "$(pwd)" \
  --scope full \
  --review-type architecture
```

## 输出文件

默认报告目录：

```text
.agent-review/<timestamp>/
  progress.log
  review-summary.md
  arbitration.md
  task.md
  diff.md
  run.json
  codex-*.md
  claude-*.md
```

重点看：

- `progress.log`：执行过程
- `review-summary.md`：每一轮摘要
- `arbitration.md`：最终仲裁结果

默认只保留最近 10 个脚本生成的报告目录。可以用：

```bash
--keep-runs 3
--keep-runs -1
--no-prune-reports
```

自定义 `--out` 指向已有非空目录时，脚本默认拒绝写入，避免覆盖用户文件。确实要覆盖时传 `--force-output`。

## 安全边界

- 默认 review-only，不会编辑文件、打 patch、提交代码。
- Claude 默认不启用工具调用。
- Codex 使用 read-only sandbox。
- `.agent-review/` 不会被纳入后续 review 输入。
- untracked symlink 不会被跟随读取。

## License

MIT
