---
## 状态: 已批准
创建: 2026-05-19
更新: 2026-05-29
负责人: 
相关: design/0001_phase1-modification-plan.md
---

## 背景

README 中定义了 Package Monitor 的核心功能：监控和展示每天安装的第三方包。本检查报告用于评估当前实现与 README 需求的匹配程度，识别偏差并明确修复优先级。

## 目标与范围

- 对照 README 功能点逐项检查实现状态
- 识别核心需求偏差及其风险
- 为第一期修改规划提供依据

## 需求对照

| README 需求 | 实现状态 | 说明 |
|---|---|---|
| macOS 桌面应用 | 基本满足 | 使用 Tauri 2 + Vue 3，macOS 系统要求依赖运行环境 |
| 监控和展示每天安装的第三方包 | 部分满足 | 扫描的是当前已安装包，未做差异比较 |
| 支持 Homebrew、pip、npm、cargo、gem、go | 基本满足 | 六类扫描器均存在，Go 无版本信息，Homebrew 未含 cask |
| 按日期浏览历史安装记录 | 满足 | 左侧日期列表，选择日期刷新包列表 |
| 实时搜索过滤 | 满足 | 按包名和管理器过滤 |
| 生成 HTML 报告 | 满足 | 可生成并尝试通过浏览器打开 |
| JSON 格式存储 | 满足 | UTF-8 缩进格式 |
| 配置文件路径 `~/.pkg-monitor/config.json` | 满足 | 默认读取该路径 |
| 安装记录路径 `~/.pkg-monitor/records.json` | 满足 | 保存路径符合 README |
| HTML 报告路径 `~/.pkg-monitor/reports/` | 满足 | 报告目录符合 README |
| 配置项 `scan_interval_hours` | 未实现 | 配置中存在但无定时扫描逻辑 |
| 配置项 `auto_scan_on_startup` | 满足 | 启动时自动扫描 |
| 配置项 `show_notifications` | 未实现 | 配置中存在但 UI 未使用该配置 |
| 配置项 `enabled_managers` | 满足 | 按配置过滤启用的扫描器 |

## 主要风险

1. **"当天安装"语义不准确**：扫描返回当前全量包清单，无法区分新旧安装
2. **`scan_interval_hours` 没有生效**：无定时器或后台调度
3. **`show_notifications` 没有生效**：配置项为空实现
4. **部分扫描结果信息不足**：Go 无版本，Homebrew 无 cask，pip 仅取单一环境

## 修复优先级

| 优先级 | 事项 | 说明 |
|---|---|---|
| P1 | 增加快照差异机制 | 保存扫描快照，比较新增包 |
| P1 | 明确报告文案 | 统一"当天安装"的产品语义 |
| P2 | 实现 `scan_interval_hours` | GUI 启动后周期性触发扫描 |
| P2 | 接入 `show_notifications` | 控制 messagebox 弹出 |
| P3 | 扩展扫描器覆盖范围 | Homebrew cask、Go 版本、多 Python 环境 |

## 变更记录

| 日期 | 变更内容 |
| --- | --- |
| 2026-05-19 | 初始检查报告 |
| 2026-05-29 | 迁移至 docs/requirements，按规范格式化 |
