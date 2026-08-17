# 工作流文档一致性调整

## 目标

修正 `docs/ai-sdd-workflow.md` 对官方 OpenSpec 流转条件的过度约束，并同步
`README.md` 对该文档的定位，使两份文档不再互相矛盾。

## 设计

- 将 `verify` 表述为推荐核验步骤，而不是所有路径及 `sync`、`archive` 的官方硬前置。
- 明确 `verify`、`sync`、`archive` 的具体条件与行为以目标项目当前 OpenSpec 官方
  生成物为准。
- 保留场景图的导航用途，但允许 `sync` 作为“只同步 delta specs、不归档”的独立旁路。
- 将 README 中工作流文档的说明收窄为“官方命令场景选择”；`evidence-driven` 制品
  语义继续由 README 的 Schema 章节和 schema 文件维护，避免重复说明产生漂移。
- 在不改变官方命令语义的前提下，新增独立的“SDD 增强闭环”说明：
  - 串联规格与验证制品、实现、验证回流及流转结果。
  - 明确 `verify` 先直接修复可安全处理的阻塞并复验；仍未解决时，再按实现缺陷、
    规划偏差或证据不足分别回到 `apply`、`update` 或补充检查。
  - 仅在目标项目按接入文档安装验证增强规则后，将 Verify 门禁作为 `sync` /
    `archive` 的强制入口条件。
  - `sync` 修改 main specs 并使原工作区指纹失效；后续归档前必须重新验证并刷新门禁。
  - 发布后发现问题时，若 change 仍为 active，则按问题类型回到 `update`、`apply`
    或补充检查；若已归档，则建立新 change，避免修改已结束 change。

## 验收

- 工作流文档不再声明“每条路径都应进入 verify”。
- 工作流文档不再声明 sync 必须发生在 verify 之后。
- README 对工作流文档的定位与文档实际内容一致。
- `verify`、`sync`、`archive` 的官方行为免责声明清晰可见。
- 官方场景导航与本仓库增强闭环分层表达，不把增强门禁误写成官方默认行为。
- 发布后问题能够根据 change 状态回流到 active change 或新 change。
