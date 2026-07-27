## Why

<!-- Explain the motivation for this change. What problem does this solve? Why now? -->

## What Changes

<!-- Describe what will change. Be specific about new capabilities, modifications, or removals. -->

## Risk Level

<!--
选择 Low / Medium / High，并说明判断依据。

- Low：单模块、无公共契约或数据结构变化、容易回滚。
- Medium：跨模块、前后端契约变化、可兼容的数据迁移或需要功能开关。
- High：破坏性契约、不可逆迁移、权限/资金/隐私、核心性能或跨系统高影响变更。
-->

- **Level:** <!-- Low / Medium / High -->
- **Rationale:** <!-- 风险来源和影响范围 -->
- **Required approval:** <!-- Medium/High 的设计、发布或人工审批要求 -->

## Capabilities

### New Capabilities
<!--
前后端使用独立 capability spec。只包含后端时省略 frontend，只包含前端时省略 backend。
通过 API 路径、OpenAPI operationId、Schema 名称或版本描述双方关联关系。
-->
- `<domain>-backend`: <!-- 服务端行为、接口契约、数据与错误语义 -->
- `<domain>-frontend`: <!-- 用户行为、页面状态、交互与契约消费 -->

### Modified Capabilities
<!-- Existing capabilities whose REQUIREMENTS are changing (not just implementation).
     Only list here if spec-level behavior changes. Each needs a delta spec file.
     Use existing spec names from openspec/specs/. Leave empty if no requirement changes. -->
- `<existing-backend-name>`: <!-- 服务端需求变化 -->
- `<existing-frontend-name>`: <!-- 前端需求变化 -->

### Contract Link

- **Contract owner:** <!-- 通常为后端 spec -->
- **Consumer:** <!-- 对应前端 spec -->
- **Reference:** <!-- API 路径 / operationId / Schema / 版本 -->
- **Compatibility:** <!-- 向后兼容策略或明确的破坏性变更 -->

## Impact

<!-- Affected code, APIs, dependencies, systems -->
