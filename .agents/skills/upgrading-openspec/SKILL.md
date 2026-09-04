---
name: upgrading-openspec
description: Executes or reviews repeatable OpenSpec upgrades for this ai-tools repository. Use when upgrading OpenSpec CLI, rebasing evidence-driven on a newer official spec-driven schema, checking upgrade compatibility, or preparing an OpenSpec upgrade run.
compatibility: Requires Node.js, npm, OpenSpec CLI, jq, rg, Python, Git, and shell access.
---

# 升级 OpenSpec

按可重复、可审计的流程升级本仓库使用的 OpenSpec，并重新对齐官方 `spec-driven` 与本地 `evidence-driven` 派生层。

## 强制入口

1. 全程使用简体中文沟通；本流程产生的计划副本、验证结论、交付说明以及 Commit / PR 正文也使用简体中文。
2. 完整读取 [OpenSpec 可重复升级实施计划](reference.md)。该文件是只读计划模板，也是所有步骤、命令、预期结果和完成标准的唯一事实源。
3. 真正执行升级时逐项执行计划中的任务与检查点；只做解释或审阅时无需执行升级步骤。
4. 执行前把计划复制到仓库外的本次运行目录，只在副本中勾选任务，绝不修改模板中的复选框。

## 执行约束

- 从当前 `openspec --version` 取得源版本；优先使用用户明确指定的目标版本，否则查询 npm 最新稳定版，并在本次运行中固定为精确版本。
- 若源版本与目标版本相同，只能称为兼容性复核。
- 不在 ai-tools 根目录运行 `openspec init` 或 `openspec update`；官方对照样本全部放在仓库外临时目录。
- 以目标版本 CLI 动态生成的官方 schema 和工具产物为唯一上游基线，不从业务项目反向复制官方生成物。
- 只保留计划列出的本地差异白名单；上游行为变化必须同步到中文派生模板和相关文档。
- 开始时记录 Git 状态。工作区不干净时按计划停止，让用户决定如何处理，不覆盖或混入既有修改。
- 每一步记录关键命令、退出码和结论。失败项不得勾选，不得把未运行的验证描述为通过。
- 不自动创建 commit；只有用户明确授权时才提交。

## 完成条件

只有计划“完成标准”全部满足，才能声明升级或兼容性复核完成。最终报告源版本、目标版本、上游差异、本地适配、完整验证、目标项目冒烟、运行记录位置、回滚信息与剩余风险。
