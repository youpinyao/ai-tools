# Graphify 接入方案

## 1. 目标与定位

[Graphify](https://github.com/Graphify-Labs/graphify) 将代码、文档、SQL schema 和配置解析为可查询的知识图谱，可用于回答跨文件依赖、架构路径和概念关联问题。

本方案将 Graphify 作为 AI-SDD / OpenSpec 工作流的**可选上下文增强层**：

- Graphify 用于快速定位相关文件、符号和依赖路径。
- 源代码、OpenSpec 规划产物和实际验证结果仍是事实依据。
- 图谱查询结果必须在涉及实现判断时回到源码或测试复核。
- 首期采用本地 CLI 与 Cursor 项目规则，不引入常驻 MCP 服务。

## 2. 前置条件

- Python 3.10+
- `uv`（推荐）或 `pipx`
- 支持 Agent Skills 的 AI 编程助手；本方案以 Cursor 为例

安装官方包（PyPI 包名为 `graphifyy`，命令名为 `graphify`）：

```bash
uv tool install graphifyy
# 或
pipx install graphifyy
```

若安装后找不到命令：

```bash
uv tool update-shell
# 或
pipx ensurepath
```

## 3. 推荐接入结构

目标项目接入后包含以下内容：

```text
<project>/
├── .agents/skills/graphify/     # Cursor 可调用的项目级 Graphify Skill
├── .cursor/rules/graphify.mdc   # Graphify 生成的查询优先规则
├── .gitattributes               # graph.json merge driver 关联
├── .graphifyignore              # Graphify 专用排除规则
└── graphify-out/
    ├── graph.json               # 可查询的完整图谱
    ├── GRAPH_REPORT.md          # 架构与关键关系摘要
    ├── graph.html               # 本地图谱可视化
    └── manifest.json            # 增量提取所需的可移植清单
```

建议提交项目级 Skill、Cursor rule、`.gitattributes`、`.graphifyignore`，以及 `graphify-out/` 中的三个核心图谱产物和 `manifest.json`，让团队成员拉取代码后即可查询并复用增量状态。`cost.json` 属于本地成本记录，`cache/` 是否提交取决于仓库体积和构建速度；包含本机路径的元数据不应提交。

建议加入目标项目的 `.gitignore`：

```gitignore
graphify-out/cost.json
graphify-out/cache/
graphify-out/.graphify_python
```

建议建立 `.graphifyignore`，排除依赖、构建产物、密钥和无关大文件：

```gitignore
node_modules/
dist/
build/
.env*
*.key
*.pem
```

`.gitignore` 会被 Graphify 自动读取；`.graphifyignore` 用于补充 Graphify 特有的排除范围。

## 4. 首次接入

在目标项目根目录执行：

```bash
# 安装 Cursor 可调用的项目级 Agent Skill
graphify install --platform agents --project

# 安装项目级 Cursor 查询优先规则
graphify cursor install

# 团队协作项目：安装本地 Git hook、注册 merge driver
graphify hook install
```

项目级 Agent Skill 是 `/graphify` 工作流的执行入口；Cursor rule 只负责在图谱已存在时引导 Agent 优先执行限定查询，不能替代 Skill。个人单机使用可跳过 Git hook；需要提交共享图谱或处理并行修改的团队项目应安装 hook。随后在 Cursor 中运行：

```text
/graphify .
```

首次构建应生成：

```text
graphify-out/graph.json
graphify-out/GRAPH_REPORT.md
graphify-out/graph.html
```

仅允许本地 AST 解析代码、不希望文档或媒体进入模型语义处理时，可使用：

```bash
graphify extract . --code-only
```

## 5. 日常使用

优先查询限定子图，避免直接加载完整报告或无范围地遍历文件：

```bash
graphify query "鉴权流程如何连接到数据库？"
graphify path "AuthService" "DatabasePool"
graphify explain "RateLimiter"
```

推荐决策顺序：

```text
提出问题
  → 查询 Graphify
  → 获得相关节点、边和源文件位置
  → 回读必要源码、规范与测试
  → 形成结论并记录证据
```

图谱查询无结果、结果冲突或图谱明显过期时，直接回到源码搜索，不应为了遵循“图谱优先”而阻塞工作。

## 6. 与 OpenSpec 工作流的结合

### explore

- 用 `query`、`path`、`explain` 快速识别影响范围和跨模块关系。
- 将图谱结果视为调查线索，不直接写成需求事实。

### propose / update

- 用图谱辅助识别受影响能力、模块和文档。
- proposal、specs、design、tasks 仍按 OpenSpec schema 和源码事实编写。

### apply

- 实现前查询相关调用链和依赖节点，减少漏改。
- 修改后通过 hook 或手动增量更新图谱。
- 测试结果和实现证据不能由图谱输出替代。

### verify

- 独立验证 Agent 可用图谱检查需求到实现的关联和潜在遗漏。
- 最终结论必须基于重新执行的检查、源码和测试，不能只依据 `GRAPH_REPORT.md`。

### archive

- 归档前确认图谱已随最终代码更新。
- Graphify 状态不应成为 OpenSpec 归档门禁，除非目标项目另行制定强制策略。

## 7. 更新与团队协作

推荐采用“提交前手动更新 + 本地 hook 异步兜底”：

```bash
# 每位开发者在本地执行一次
graphify hook install

# 代码提交前手动增量更新，可将代码与对应图谱放入同一提交
graphify update .

# 文档或其他语义内容发生变化时，在 Cursor 中更新
/graphify . --update
```

`graphify hook install` 安装的是异步 `post-commit` 和 `post-checkout` hook。提交完成后，hook 只在后台更新工作区中的图谱，不会修改刚刚创建的提交，也不会自动提交产物。因此，不应依赖 hook 将最新图谱自动带入当前代码提交；若未在提交前手动更新，应等待后台重建完成、检查产物后再单独提交。

团队协作约定：

1. 首位接入者生成并提交项目级 Skill、Cursor rule、`.graphifyignore`、`.gitattributes`、核心图谱产物和 `manifest.json`。
2. 其他成员拉取后执行 `graphify hook install`，在本地 Git 配置中注册 merge driver。
3. 代码提交前优先运行 `graphify update .`，将代码与更新后的图谱产物放入同一提交。
4. 若依赖 `post-commit` hook 兜底，等待后台重建完成后检查并另行提交图谱产物。
5. 并行修改导致 `graph.json` 冲突时，由已注册的 Graphify merge driver 和仓库中的 `.gitattributes` 共同处理。
6. 图谱节点异常减少时先排查提取错误；不要默认使用 `--allow-partial` 覆盖完整图谱。

## 8. 隐私与安全

- 代码 AST 解析在本地完成，不需要 API key。
- 文档、PDF 和图片的语义提取可能调用所选模型后端。
- 敏感仓库优先使用 `--code-only`，或显式配置本地 Ollama 后端。
- `.env`、密钥、证书、客户数据和导出数据必须通过忽略规则排除。
- 不对外暴露 `graphify-out/` 或 HTTP MCP 服务；如后续启用共享 HTTP MCP，必须同时配置访问密钥和网络边界。

## 9. 故障恢复与移除

图谱过期或提取异常时：

```bash
graphify extract . --force
```

移除项目接入时：

```bash
graphify uninstall --project --platform agents
graphify cursor uninstall
graphify hook uninstall
```

上述命令会分别移除项目级 Agent Skill、Cursor rule、Git hook、merge driver 配置及其 `.gitattributes` 条目。随后删除 `.graphifyignore` 和 `graphify-out/`；若安装过程曾被中断，再检查并清理残留的 `.agents/skills/graphify/` 或 `.cursor/rules/graphify.mdc`。移除 Graphify 不影响 OpenSpec change、主规格或历史验证记录。

## 10. 验收清单

- [ ] `graphify --version` 可正常执行。
- [ ] Cursor 可发现并调用项目级 Graphify Skill。
- [ ] Cursor 已加载项目级 Graphify rule。
- [ ] 首次构建生成三个核心图谱产物和 `manifest.json`。
- [ ] `query`、`path`、`explain` 各完成一次冒烟查询。
- [ ] `.graphifyignore` 已排除密钥、依赖和构建产物。
- [ ] Git 仅跟踪约定的图谱产物和可移植元数据，不包含成本、缓存或本机路径。
- [ ] `.gitattributes` 已提交，且本地 merge driver 已注册。
- [ ] 一次代码变更后可通过提交前手动命令更新，或在异步 hook 完成后另行提交。
- [ ] AI-SDD / OpenSpec 结论仍可追溯到源码、规范和测试证据。

## 11. 后续可选增强

首期稳定后可按需评估：

- 在 CI 中检查图谱是否过期。
- 使用 `graphifyy[mcp]` 提供 stdio MCP 工具。
- 为团队部署带 API key 的共享 HTTP MCP 服务。
- 将多个仓库图谱合并为跨项目全局图谱。

这些增强会增加 CI、服务运维或访问控制成本，不作为基础接入要求。
