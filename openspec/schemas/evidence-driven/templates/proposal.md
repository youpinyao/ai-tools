<!--
Superpowers brainstorming 前门（薄适配）：撰写或覆盖本提案前须已澄清意图、
对比方案并获用户批准（或同一会话已选定方案时先简短复述范围确认）。
纯只读探索不强制写提案；未获用户要求时不要自动 commit。
-->

## 背景与动机

<!-- 说明本次变更的动机：要解决什么问题？为什么现在需要变更？ -->

## 变更内容

<!-- 描述具体变更，明确说明新增、修改或移除的能力。 -->

## 能力

### 新增能力
<!-- 本次引入的能力。路径段使用 kebab-case（例如 user-auth 或 identity/user-auth），
     并遵循项目既有规范目录组织。每项能力都会创建 specs/<capability-path>/spec.md。 -->
- `<capability-path>`：<简要说明该能力涵盖的内容>

### 修改能力
<!-- 需求发生变化的现有能力（不只是实现变化）。
     仅在规范层行为发生变化时列出。每项能力都需要一个增量规范（delta spec）文件。
     使用 openspec/specs/ 下的既有完整路径。没有需求变化时留空。
     若完全没有任何能力（纯重构、工具链、文档），必须在 .openspec.yaml 中设置
     `skip_specs: true`——否则 openspec validate 会拒绝零增量变更。
     若本变更会移除某能力的最后一条需求并删除其 main spec，另须设置
     `retire_capabilities: true`（OpenSpec 1.8+）。
     不要为了通过校验而捏造需求。 -->
- `<existing-capability-path>`：<说明发生变化的需求>

## 影响

<!-- 受影响的代码、API、依赖或系统 -->
