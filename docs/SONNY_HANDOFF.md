# Sonny ApplyPilot 本地交接文档

## 1. 项目路径

```text
D:\Codex\ApplyPilot-spencer
```

虚拟环境：

```text
D:\Codex\ApplyPilot-spencer\.venv
```

## 2. 当前分支

长期本地适配分支：

```text
sonny/applypilot-codex-energy-adaptation
```

该分支用于 Sonny 本地 ApplyPilot 适配，不直接作为 upstream PR 分支。

## 3. Git remotes

当前已知 remote：

```text
origin   -> https://github.com/Sonny332/ApplyPilot.git
middle   -> https://github.com/spencerthayer/ApplyPilot.git
upstream -> https://github.com/Pickle-Pixel/ApplyPilot.git
```

当前 remote 命名已按 fork-of-fork 工作流配置：

```text
origin   -> Sonny 自己的 ApplyPilot fork
middle   -> https://github.com/spencerthayer/ApplyPilot.git
upstream -> https://github.com/Pickle-Pixel/ApplyPilot.git
```

不要在未获得 Sonny 明确批准前继续修改 remotes、fetch、pull、push 或创建 PR。

## 4. Fork / PR 当前策略

* `Pickle-Pixel/ApplyPilot` 是原始 upstream。
* `spencerthayer/ApplyPilot` fork 自 `Pickle-Pixel/ApplyPilot`，并包含 Codex CLI 适配。
* Sonny 的 fork 基于 `spencerthayer/ApplyPilot`。
* Sonny 的长期本地分支是 `sonny/applypilot-codex-energy-adaptation`。
* 本地个人规则、`AGENTS.md`、handoff、H-1B/job-search preferences、Energy/HVAC/data-center scoring rules 留在 Sonny 分支，不提交 upstream。
* Windows `codex.CMD` / `npx.CMD` 路径修复通常留在本地，除非 `spencerthayer` 也需要。
* Gemini provider 修复如果原项目也有相同问题，可考虑给 `Pickle-Pixel/ApplyPilot`。
* scoring token budget / Gemini fallback 如果实现足够通用，可考虑给 `Pickle-Pixel/ApplyPilot`。
* 未来 DeepSeek provider 如果实现为通用 provider，可考虑给 `Pickle-Pixel/ApplyPilot`。
* Codex CLI replacement / adapter 工作更适合给 `spencerthayer/ApplyPilot`。
* 任何 upstream PR 都必须拆成干净小分支，并在 push 或创建 PR 前由 Sonny 明确确认。

## 5. 项目目标

本地目标是让 Sonny 的 ApplyPilot fork 能稳定完成：

1. LinkedIn-only 小批量发现；
2. job enrich；
3. Gemini scoring；
4. 针对 energy / building / HVAC / renewable / data-center thermal 的候选识别；
5. 高分候选人工审查；
6. 经 Sonny 批准后生成 tailoring / cover / PDF；
7. 经 Sonny 批准后进行单 URL `apply --gen` 和 `apply --dry-run`；
8. 真实投递必须单独明确批准。

## 6. 数据目录规则

正式数据目录：

```text
D:\Codex\ApplyPilot-data
```

smoke 测试目录：

```text
D:\Codex\ApplyPilot-smoke-data
```

当前任务不得修改正式数据目录。所有实验性 discover/enrich/score/apply dry-run 都应默认使用 smoke 目录，并且需要 Sonny 明确批准。

## 7. 已完成修复

已知本地修复和适配：

1. Gemini / LiteLLM provider 调用修复：Gemini native provider 不再混用 Google OpenAI-compatible `/openai` base URL。
2. Codex backend Windows 路径修复：subprocess 使用 `shutil.which("codex")` 解析实际 Codex CLI 路径。
3. MCP config 中 `npx` 路径修复：使用 `shutil.which("npx")`，避免 Windows `[WinError 2]`。
4. scoring `max_output_tokens` 从临时 `8192` 收敛为 `SCORING_MAX_OUTPUT_TOKENS = 3072`。
5. scoring-only `SCORING_LLM_MODELS` fallback：遇到 429/rate-limit 时按顺序尝试 Gemini 多模型。
6. deterministic scoring rules 已增强对 energy/building/HVAC/renewable/data-center thermal 的识别。
7. smoke data 目录已用于隔离测试，避免污染正式数据。

## 8. 当前未提交改动

当前存在未提交本地改动，主要包括：

* `AGENTS.md`
* `docs/SONNY_HANDOFF.md`
* `package-lock.json`
* `src/applypilot/apply/agent_backends.py`
* `src/applypilot/llm.py`
* `src/applypilot/scoring/scorer.py`
* `tests/test_scoring_resilience.py`

不要在 Sonny 未批准前 commit 或 push。

## 9. 已通过测试

已知通过的验证：

1. `python -m compileall src/applypilot` 曾通过。
2. Gemini LLM minimal smoke test 曾返回 `OK`。
3. Codex CLI backend dry-run 基础设施曾能启动 Chrome 和 Codex。
4. scoring truncation focused regression test 曾通过。
5. `SCORING_LLM_MODELS` parsing / 429 fallback / malformed JSON no fallback focused tests 曾通过。
6. deterministic helper inspection 已确认：
   * energy / building / HVAC / renewable / data-center thermal 能被识别；
   * Technician / NOC / operator / marketing 没有被错误抬高。

新窗口接手时，如果要继续改代码，应重新跑与当前修改相关的 focused tests。

## 10. 当前 scoring 状态

当前 scoring runtime 状态良好：

* 最近 smoke scoring 没有 score errors。
* 最近 smoke scoring 没有 Gemini 429 rate-limit errors。
* 当前问题不是 scoring runtime，而是候选池质量。
* 当前没有 `fit_score >= 6` 的候选。

当前默认 scoring fallback：

```text
SCORING_LLM_MODELS=gemini-3.1-flash-lite,gemini-3.5-flash,gemini-3-flash,gemini-2.5-flash
```

## 11. 当前候选池状态

最近一次 LinkedIn-only smoke search 发现的候选质量不足：

* 有 data-center thermal/cooling 相关职位，但多为 senior/principal 或方向偏电力/系统研究。
* 有 building-energy/HVAC 相关职位，但没有达到 `fit_score >= 6`。
* 混入了一些 sales、financial analyst、project controls、principal/senior 等错配职位。

建议下一轮搜索进一步排除：

```text
principal
senior
sr.
director
project controls
financial analyst
sales engineer
```

并尝试更精确关键词：

```text
energy analyst building
building energy modeler
energy efficiency analyst
HVAC energy analyst
building performance analyst
utility energy analyst
```

## 12. 已知问题

1. LinkedIn 搜索结果质量不稳定，需要持续调小 batch 并改进 queries / exclude_titles。
2. Gemini 免费或低限额模型可能出现 429，需要使用 fallback，但不得暴力重试。
3. high-fit 候选不足时，不应强行 tailor、cover、apply。
4. 正式数据目录不能被 smoke 测试污染。
5. upstream PR 需要先拆分，不能从 Sonny 长期分支直接提交。

## 13. 下一步建议

建议下一步不要改代码，先做更干净的小批量 search/scoring：

1. 使用 `D:\Codex\ApplyPilot-smoke-data`。
2. 保持 `workers=1`。
3. LinkedIn-only。
4. 每轮候选数控制在 20 以下。
5. 在出现 `fit_score >= 6` 后，先报告候选，不自动生成材料。
6. Sonny 确认后，再运行 tailor / cover / pdf。
7. 再由 Sonny 确认后，运行单 URL `apply --gen` 或 `apply --dry-run`。

## 14. 禁止动作

除非 Sonny 明确批准，禁止：

1. 读取或展示 `.env` 内容；
2. 修改 `D:\Codex\ApplyPilot-data`；
3. 删除任何正式数据、历史 logs、历史 resumes、历史 cover letters；
4. 运行 real apply；
5. 运行 `apply --dry-run`；
6. 运行 `apply --gen`；
7. 运行 tailor / cover / pdf；
8. 运行 discover / enrich / score；
9. commit；
10. push；
11. 修改 remotes；
12. 创建 PR；
13. rebase / merge / reset / clean。

## 15. 新窗口接手步骤

新窗口接手时按以下顺序：

1. 读取 `AGENTS.md`。
2. 读取 `docs/SONNY_HANDOFF.md`。
3. 运行只读检查：

```powershell
git status --short
git branch --show-current
git remote -v
git log --oneline -5
```

4. 确认当前分支是：

```text
sonny/applypilot-codex-energy-adaptation
```

5. 不读取或展示 `.env`。
6. 不运行 pipeline，除非 Sonny 明确批准。
7. 若要继续 smoke search，先设置：

```powershell
$env:APPLYPILOT_DIR="D:\Codex\ApplyPilot-smoke-data"
$env:SCORING_LLM_MODELS="gemini-3.1-flash-lite,gemini-3.5-flash,gemini-3-flash,gemini-2.5-flash"
```

8. 只在 Sonny 明确批准后运行 discover / enrich / score。
9. 任何 `fit_score < 6` 的职位默认停止在报告，不生成材料。
10. 任何真实投递都必须单独明确批准。
