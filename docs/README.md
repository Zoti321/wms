# 仓脉 WMS 文档

## 权威源

| 类型 | 权威路径 | 说明 |
|------|----------|------|
| 领域术语 | `CONTEXT-MAP.md` + `src/*/CONTEXT.md` | 仅 glossary（Matt Pocock 多上下文布局） |
| 模块需求 | `docs/requirements/*.md` | 模块化 SRS；PR2 将迁至 `docs/domains/` |
| 开发设计 | `docs/dev/*.md` | 架构、API、数据模型、后端状态 |
| 架构决策 | `docs/adr/` | ADR |
| 任务 spec | GitHub Issues | 单次功能/任务（`to-spec`） |
| 人类门户 | `docs/*.html` | 索引与导航；正文以 Markdown 为准 |

## 目录

- [`dev/`](./dev/README.md) — 开发设计说明书（WMS-SDD-001）
- [`requirements/`](./requirements/README.md) — 需求文档（WMS-SRS-001）
- [`adr/`](./adr/) — 架构决策记录
- [`mini-program/`](./mini-program/README.md) — 小程序实现说明
- [`uat/`](./uat/README.md) — UAT 与需求追溯
- [`runbooks/`](./runbooks/) — 运维手册
- [`agents/`](./agents/) — Agent / 工程技能消费规则

浏览器入口：[`index.html`](./index.html)
