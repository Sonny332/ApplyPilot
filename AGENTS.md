# ApplyPilot 本地开发规则 - Sonny 分支

## 0. 项目定位

本项目基于外部 GitHub 项目 ApplyPilot 进行本地适配。当前目标不是重写原项目，而是在尊重原项目结构的基础上，完成 Sonny 的本地求职自动化需求，包括：

* 使用 Codex 替代 Claude 执行自动投递流程；
* 修复 Windows、Gemini、Codex CLI 相关兼容问题；
* 针对 energy、building、HVAC、renewable、data center thermal 方向优化 scoring；
* 保持所有真实投递行为可控、可回滚、可人工审查。

默认工作分支：

```text
sonny/applypilot-codex-energy-adaptation
```

除非 Sonny 明确批准，不得直接在 `main` 或 `master` 上进行功能开发。

## 1. 语言规则

1. 面向 Sonny 的总结、进度报告、风险说明、下一步建议，默认使用中文。
2. 代码、命令、文件名、函数名、错误信息、commit message、PR title 可以保留英文。
3. 只有 Sonny 明确要求英文回复时，才使用英文。
4. 不得因为上下文压缩或任务复杂而切换为英文报告。

## 2. 安全与密钥规则

1. 严禁打印、展示、复制、总结或暴露以下内容：
   * `.env` 完整内容；
   * Gemini API key；
   * DeepSeek API key；
   * OpenAI / OpenRouter API key；
   * LinkedIn 账号密码；
   * Gmail / Google 凭据；
   * 任何 cookie、token、session、secret。
2. 可以检查 `.env` 是否存在、某个 key 是否为空，但不得显示具体值。
3. 若需要修改 `.env`，必须先向 Sonny 说明原因，并等待明确批准。
4. 默认不读取正式数据目录中的密钥文件内容。

## 3. Git 分支与协作规则

1. 不得直接在 `main` 或 `master` 上继续开发。
2. 当前本地长期工作分支使用：

```text
sonny/applypilot-codex-energy-adaptation
```

3. `main` / `master` 只用于同步原项目或 fork 默认分支，不作为日常开发分支。
4. 每一类修改应尽量独立：
   * Gemini / LiteLLM provider 修复；
   * Codex / npx Windows 路径修复；
   * scoring token / fallback 修复；
   * energy / building / HVAC scoring 规则；
   * data center thermal scoring 规则；
   * 文档 / handoff 规则。
5. 未经 Sonny 批准不得执行：
   * `git commit`
   * `git push`
   * `git reset --hard`
   * `git clean`
   * `git rebase`
   * `git merge`
   * force push
6. 如果需要向原作者贡献，必须先整理为干净、独立、可解释的 commit，再由 Sonny 决定是否创建 PR。
7. 对原项目可能有普遍价值的修改，优先考虑 upstream PR。
8. 与 Sonny 私人求职偏好相关的修改，应保留在 Sonny 分支，不强行提交上游。
9. 如果存在 upstream remote，应保持 upstream 指向原作者仓库；origin 应指向 Sonny 自己的 fork。若无法确认，不得自动修改 remote，必须报告。

## 4. Fork 层级与 Pull Request 规则

1. 当前项目存在三层关系：
   * 原始上游仓库：`Pickle-Pixel/ApplyPilot`
   * 中间 fork：`spencerthayer/ApplyPilot`
   * Sonny 的个人 fork：Sonny 自己 GitHub 账号下的 ApplyPilot fork
2. `spencerthayer/ApplyPilot` fork 自 `Pickle-Pixel/ApplyPilot`，并已做 Codex CLI 替代 Claude CLI 的适配。
3. Sonny 的本地长期分支为：

```text
sonny/applypilot-codex-energy-adaptation
```

4. Sonny 分支默认用于本地适配，不直接作为 upstream PR 分支。
5. PR 目标仓库必须根据修改类型决定：
   * 与 Codex CLI 替代 Claude CLI、`spencerthayer` fork 结构强相关的修改，优先考虑 PR 给 `spencerthayer/ApplyPilot`；
   * 与 Gemini provider、scoring token、Gemini fallback、DeepSeek provider 等通用 LLM/provider/scoring 能力相关的修改，如果 `Pickle-Pixel` 原项目也存在相同机制，优先考虑 PR 给 `Pickle-Pixel/ApplyPilot`；
   * Sonny 个人求职偏好、中文 `AGENTS.md`、handoff、H-1B 筛选、Energy/HVAC/data-center scoring profile、smoke-data 规则，不提交 upstream。
6. 不得直接用 Sonny 长期分支创建 PR。若需要 PR，必须从 Sonny 分支或合适 base 拆出干净小分支，例如：
   * `fix/gemini-litellm-provider`
   * `fix/scoring-token-budget`
   * `feature/gemini-scoring-fallback`
   * `feature/deepseek-provider`
   * `fix/windows-codex-npx-resolution`
7. 每个 PR 分支只包含一个主题，禁止混入 Sonny 私人规则、smoke data、handoff、个人 resume/profile/search 配置。
8. 创建 PR 前必须由 Sonny 明确确认：
   * PR 目标仓库：`spencerthayer/ApplyPilot` 或 `Pickle-Pixel/ApplyPilot`；
   * PR base branch；
   * PR head branch；
   * 是否包含私人化内容；
   * 是否需要 squash、rebase 或 cherry-pick。
9. 不得自动创建 PR。
10. 不得自动 push 到 upstream / middle。
11. 只能在 Sonny 明确批准后 push 到 Sonny 自己 fork 的对应分支。

## 5. 数据目录规则

1. 测试默认使用：

```text
D:\Codex\ApplyPilot-smoke-data
```

2. 正式数据默认使用：

```text
D:\Codex\ApplyPilot-data
```

3. 未经 Sonny 明确批准，不得修改、删除、重置、覆盖正式数据目录。
4. smoke 测试可以重置 smoke 数据库，但必须明确说明只操作 smoke 目录。
5. 不得删除历史生成的 resume、cover、prompt、logs，除非 Sonny 明确批准。
6. Playwright Chromium 缓存、旧 `.applypilot` 目录等清理操作必须单独确认。

## 6. 投递安全规则

1. 真实投递必须由 Sonny 在同一轮对话中明确批准。
2. 默认禁止执行真实 apply、submit、最终提交按钮点击、批量投递。
3. `apply --dry-run` 可以用于测试，但必须满足：
   * 使用 `D:\Codex\ApplyPilot-smoke-data`；
   * 针对单个明确 URL；
   * 不提交真实申请；
   * 执行后报告 final RESULT、agent log path、是否进入 LinkedIn Easy Apply flow。
4. `apply --gen` 可以在已选择目标 job URL、且已有 resume / cover 材料后运行，用于生成 agent prompt；但不得自动继续执行 dry-run 或 real apply。
5. `apply --gen` 生成的 prompt 文件可能包含 job 信息、材料路径和申请指令，不得上传、外发或展示敏感内容。
6. 对于 `fit_score < 5` 的职位，不得继续生成材料或 dry-run，除非 Sonny 明确批准。
7. 对于 `fit_score 5-5.9` 的职位，只能进入 manual review。
8. 对于 `fit_score >= 6` 的职位，可以建议生成材料、`apply --gen` 和 dry-run，但仍不得真实投递。
9. dry-run 失败时必须区分：
   * 环境失败；
   * Chrome / MCP 失败；
   * 登录 / captcha 失败；
   * Easy Apply 不可用；
   * location / sponsorship / eligibility 失败；
   * agent 判断失败。

## 7. Scoring 与职位筛选规则

1. 当前 scoring 目标优先支持 Sonny 的核心方向：
   * Energy Analyst
   * Energy Efficiency Engineer
   * Building Performance Analyst
   * Building Energy Analyst
   * HVAC Energy Engineer
   * Decarbonization Consultant
   * Sustainability Analyst with energy/building focus
   * Utility Program Analyst
   * Renewable / Solar / Storage Analyst
   * Data Center Cooling / Thermal / Facilities Engineer
2. 不得盲目增加过宽类别。
3. 不得把以下岗位误抬高：
   * Technician
   * NOC Technician
   * Control Room Operator
   * Field Service Engineer
   * Sales Engineer
   * Account Executive
   * Marketing / Performance Marketing
   * Director / VP / Principal 级别明显过高岗位
   * US citizen only / clearance required
   * no sponsorship / unable to sponsor
4. 修改 scoring 规则时，优先从 deterministic baseline 入手：
   * `_ROLE_FAMILY_PATTERNS`
   * `_SKILL_PATTERNS`
   * `role_family_bonus`
5. 不优先修改 LLM prompt / output schema，除非 deterministic 层已经验证不足。
6. 每次 scoring 修改后，必须先跑 helper inspection，再跑 smoke scoring。
7. 判断规则成功的标准不是“所有岗位都升分”，而是：
   * 目标岗位能被正确识别；
   * 错配岗位没有被误抬高；
   * 分数原因可解释。

## 8. 测试规则

1. 代码修改后至少运行：

```powershell
python -m compileall src/applypilot
```

2. 有 focused tests 时，优先运行 focused tests。
3. 不得未经批准运行全量 pipeline。
4. 不得未经批准运行：
   * discover
   * enrich
   * score
   * tailor
   * cover
   * pdf
   * apply --gen
   * apply --dry-run
   * apply
5. 若 Sonny 批准 pipeline 测试，默认：
   * `APPLYPILOT_DIR=D:\Codex\ApplyPilot-smoke-data`
   * `workers=1`
   * LinkedIn-only source
   * 小批量
6. Gemini scoring 默认使用：

```text
SCORING_LLM_MODELS=gemini-3.1-flash-lite,gemini-3.5-flash,gemini-3-flash,gemini-2.5-flash
```

7. 出现 429 时，不得暴力重试；应报告 rate-limit 并等待下一步指示。

## 9. Handoff 交接规则

1. 必须维护：

```text
docs/SONNY_HANDOFF.md
```

2. 该文件用于新旧聊天窗口交接，不依赖聊天上下文。
3. 每次完成重要阶段后，应更新 handoff，包括：
   * 当前分支；
   * 当前目标；
   * 已完成修复；
   * 当前未提交文件；
   * 测试结果；
   * 已知问题；
   * 下一步建议；
   * 禁止动作；
   * 最近一次 pipeline / scoring / dry-run 状态。
4. handoff 文件不得包含任何 secret、token、cookie、账号密码。
5. 新窗口开始工作前，应先读取 `AGENTS.md` 和 `docs/SONNY_HANDOFF.md`。

## 10. Codex 执行报告格式

每次 Codex 完成任务后，必须用中文报告：

1. 执行了什么；
2. 改了哪些文件；
3. 跑了哪些命令；
4. 测试是否通过；
5. 是否出现错误；
6. 是否有未提交修改；
7. 是否触碰了正式数据目录；
8. 是否运行了 apply / dry-run；
9. 是否启用了 superpowers 插件和计划模式；
10. 下一步建议。

禁止只给英文技术摘要。

## 11. 范围控制规则

1. 优先做最小、可逆、可测试修改。
2. 不得一次混合多个无关目标。
3. 不得为了测试而改业务逻辑。
4. 不得为了绕过失败而降低安全门槛。
5. 不得在没有解释风险的情况下修改 scoring 阈值、投递阈值、密钥配置或正式数据。
6. 如果发现新的阻塞问题，先报告，不要自行扩大修改范围。
7. 凡是涉及代码功能改变或新增的任务，必须先启用 superpowers 插件和计划模式。
8. 在计划模式下，Codex 必须先输出：
   * 目标；
   * 将修改的文件；
   * 不会修改的文件；
   * 风险；
   * 测试计划；
   * 回滚方式。
9. 只有 Sonny 明确确认计划后，才允许进入代码修改。
10. 如果 superpowers 插件不可用、无法确认是否启用，或者计划模式无法启动，必须停止并报告，不得继续改代码。

## 12. 当前已知本地修改方向

当前 Sonny 分支已经或计划包含以下本地适配：

1. Gemini / LiteLLM 调用修复；
2. Codex CLI / npx Windows 路径解析修复；
3. scoring `max_output_tokens` 收敛到 `3072`；
4. scoring-only Gemini 多模型 fallback；
5. energy / building / HVAC / renewable / data-center thermal deterministic scoring 规则；
6. smoke-data 测试流程；
7. handoff 文档机制；
8. 后续 sponsorship / work authorization 严格筛选；
9. 后续可考虑 DeepSeek provider 兼容。

## 13. 当前不做事项

在 Sonny 明确批准前，不做：

1. 真实投递；
2. 批量 dry-run；
3. 接入 DeepSeek；
4. 改 LLM scoring prompt；
5. 改 output schema；
6. 改正式数据目录；
7. 删除缓存或历史文件；
8. push 到远程；
9. 给 upstream 提 PR；
10. 合并回 `main` / `master`。
