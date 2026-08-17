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

## 验收

- 工作流文档不再声明“每条路径都应进入 verify”。
- 工作流文档不再声明 sync 必须发生在 verify 之后。
- README 对工作流文档的定位与文档实际内容一致。
- `verify`、`sync`、`archive` 的官方行为免责声明清晰可见。
