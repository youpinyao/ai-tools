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
├── .cursor/rules/graphify.mdc   # Graphify 生成的查询优先规则
├── .graphifyignore              # Graphify 专用排除规则
└── graphify-out/
    ├── graph.json               # 可查询的完整图谱
    ├── GRAPH_REPORT.md          # 架构与关键关系摘要
    └── graph.html               # 本地图谱可视化
```

建议提交以上三个核心产物，让团队成员拉取代码后即可查询。`cost.json` 属于本地成本记录，`cache/` 是否提交取决于仓库体积和构建速度。

建议加入目标项目的 `.gitignore`：

```gitignore
graphify-out/cost.json
graphify-out/cache/
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
# 安装项目级 Cursor 规则
graphify cursor install --project

# 可选：安装本地 Git hook，在提交后更新图谱
graphify hook install
```

随后在 Cursor 中运行：

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

推荐采用“本地 hook + 手动兜底”：

```bash
# 每位开发者在本地执行一次
graphify hook install

# 手动增量更新
graphify update .

# 或在 Cursor 中
/graphify . --update
```

团队协作约定：

1. 首位接入者生成并提交核心 `graphify-out/` 产物。
2. 其他成员拉取后安装本地 hook。
3. 代码提交后同步提交更新的图谱产物。
4. 并行修改导致 `graph.json` 冲突时，使用 Graphify hook 安装的 merge driver 处理。
5. 图谱节点异常减少时先排查提取错误；不要默认使用 `--allow-partial` 覆盖完整图谱。

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
graphify cursor uninstall
graphify hook uninstall
```

随后删除 `.cursor/rules/graphify.mdc`、`.graphifyignore` 和 `graphify-out/`。移除 Graphify 不影响 OpenSpec change、主规格或历史验证记录。

## 10. 验收清单

- [ ] `graphify --version` 可正常执行。
- [ ] Cursor 已加载项目级 Graphify rule。
- [ ] 首次构建生成三个核心图谱产物。
- [ ] `query`、`path`、`explain` 各完成一次冒烟查询。
- [ ] `.graphifyignore` 已排除密钥、依赖和构建产物。
- [ ] Git 仅跟踪约定的核心图谱产物。
- [ ] 一次代码变更后可通过 hook 或手动命令增量更新。
- [ ] AI-SDD / OpenSpec 结论仍可追溯到源码、规范和测试证据。

## 11. 后续可选增强

首期稳定后可按需评估：

- 在 CI 中检查图谱是否过期。
- 使用 `graphifyy[mcp]` 提供 stdio MCP 工具。
- 为团队部署带 API key 的共享 HTTP MCP 服务。
- 将多个仓库图谱合并为跨项目全局图谱。

这些增强会增加 CI、服务运维或访问控制成本，不作为基础接入要求。
