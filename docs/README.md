# 仓脉 WMS 文档

## 权威源

| 类型 | 权威路径 | 说明 |
|------|----------|------|
| 领域术语 | `CONTEXT-MAP.md` + `src/*/CONTEXT.md` | 仅 glossary（Matt Pocock 多上下文布局） |
| 模块需求 | `docs/domains/*.md` | 模块化 SRS（WMS-SRS-001） |
| 开发设计 | `docs/dev/*.md` | 架构、API、数据模型、后端状态（WMS-SDD-001） |
| 架构决策 | `docs/adr/` | ADR |
| 任务 spec | GitHub Issues | 单次功能/任务（`to-spec`） |
| 人类门户 | `docs/*.html` | 索引与导航；正文以 Markdown 为准 |

## 目录

- [`domains/`](./domains/README.md) — 模块需求（SRS）
- [`dev/`](./dev/README.md) — 开发设计说明书（SDD）
- [`adr/`](./adr/) — 架构决策记录
- [`mini-program/`](./mini-program/README.md) — 小程序实现说明
- [`uat/`](./uat/README.md) — UAT 与需求追溯
- [`runbooks/`](./runbooks/) — 运维手册
- [`agents/`](./agents/) — Agent / 工程技能消费规则
- [`requirements/`](./requirements/README.md) — **已废弃**，指针至 `domains/`

浏览器入口：[`index.html`](./index.html)
