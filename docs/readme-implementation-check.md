# README 需求实现检查报告

检查日期：2026-05-19

## 结论

当前实现覆盖了 README 中大部分显式功能点，包括 GUI 启动、包管理器扫描、按日期浏览、搜索过滤、HTML 报告生成、JSON 存储和基础配置读取。

但实现并未严格满足核心目标“监控和展示每天安装的第三方包”。目前扫描逻辑记录的是扫描时系统中“已安装的全部包”，而不是当天新增安装的包。因此，报告中的“今日安装包数/今日安装详情”在语义上会被高估，尤其是首次启动或每天首次扫描时。

## 需求对照

| README 需求 | 实现状态 | 证据 | 说明 |
|---|---:|---|---|
| macOS 桌面应用 | 基本满足 | `main.py:65`、`ui.py:20` | 使用 tkinter 创建桌面窗口。README 的 macOS 系统要求主要依赖运行环境，代码未做 macOS 版本检查。 |
| 监控和展示每天安装的第三方包 | 部分满足 | `README.md:3`、`scanner.py:21-23`、`scanner.py:54`、`main.py:56-58`、`ui.py:235-238` | 扫描的是各管理器当前已安装包列表，并把扫描结果写入当天日期；没有和前一次快照做差异比较，也没有读取真实安装时间。 |
| 支持 Homebrew、pip、npm、cargo、gem、go | 基本满足 | `README.md:7`、`scanner.py:238-244` | 六类扫描器均存在。Go 扫描只枚举 `$GOPATH/bin` 可执行文件，无法得到模块版本；Homebrew 未包含 cask。 |
| 按日期浏览历史安装记录 | 满足 | `README.md:8`、`ui.py:174-191`、`storage.py:55-62` | 左侧日期列表来自 JSON 记录日期，选择日期后刷新包列表。 |
| 实时搜索过滤 | 满足 | `README.md:9`、`ui.py:136-138`、`ui.py:204-219`、`storage.py:72-90` | 搜索框变更会实时按包名和管理器过滤当前日期记录。 |
| 生成 HTML 报告 | 满足 | `README.md:10`、`ui.py:254-269`、`report.py:294-324` | 可生成 HTML，并尝试通过默认浏览器打开。 |
| JSON 格式存储 | 满足 | `README.md:11`、`storage.py:16-31` | 记录以 JSON 文件读写，使用 UTF-8 和缩进格式。 |
| 配置文件路径 `~/.pkg-monitor/config.json` | 满足 | `README.md:38`、`config.py:27-35` | 默认读取该路径；若不存在不会自动写出默认配置文件。 |
| 安装记录路径 `~/.pkg-monitor/records.json` | 满足 | `README.md:39`、`config.py:68-71`、`storage.py:26-31` | 保存路径符合 README。 |
| HTML 报告路径 `~/.pkg-monitor/reports/` | 满足 | `README.md:40`、`config.py:73-76`、`report.py:290-292` | 报告目录符合 README。 |
| 配置项 `scan_interval_hours` | 未实现 | `README.md:48`、`config.py:9-16` | 配置中存在，但没有定时扫描逻辑读取或使用该值。 |
| 配置项 `auto_scan_on_startup` | 满足 | `README.md:49`、`main.py:51-58` | 启动时会自动扫描。 |
| 配置项 `show_notifications` | 未实现 | `README.md:50`、`config.py:14-15` | 配置中存在，但 UI 只使用 messagebox，没有按该配置控制系统通知或弹窗。 |
| 配置项 `enabled_managers` | 满足 | `README.md:51`、`main.py:43-45`、`scanner.py:247-250` | 会按配置过滤启用的扫描器。 |
| Python 3.8+ | 基本满足 | `requirements.txt:1` | 代码语法兼容 Python 3.8；未配置显式版本约束。 |
| tkinter 依赖 | 满足 | `ui.py:4-5` | GUI 使用 tkinter/ttk。 |

## 主要风险

1. “当天安装”语义不准确  
   `HomebrewScanner`、`PipScanner`、`NpmScanner`、`CargoScanner`、`GemScanner` 和 `GoScanner` 都返回当前已安装包清单，并统一把 `time` 设置为扫描时间。`Storage.add_packages()` 只按当天已有 `(manager, name)` 去重，不能判断某个包是在今天安装，还是早已存在。

2. `scan_interval_hours` 没有生效  
   README 提供了扫描间隔配置，但程序没有定时器、后台调度或上次扫描时间判断。实际扫描只发生在启动自动扫描和用户点击“立即扫描”时。

3. `show_notifications` 没有生效  
   配置文件暴露了通知开关，但当前没有条件判断；扫描完成和报告完成都会弹出 messagebox。

4. 部分扫描结果信息不足  
   Go 扫描没有版本信息，只记录 `"installed"`；Homebrew 没有 cask；pip 只取 `pip3` 或 `pip` 中第一个成功结果，不能覆盖多个 Python 环境。

## 建议修复优先级

1. 增加快照差异机制  
   保存每次扫描的全量快照，再把“本次扫描新增且之前不存在”的包写入当天安装记录。这样能最直接对齐“每天安装”的需求。

2. 明确报告文案  
   如果产品目标只是展示“当天扫描到的已安装包”，应修改 README 和报告文案；如果目标是“当天新增安装包”，应修改实现。

3. 实现 `scan_interval_hours`  
   可在 GUI 启动后使用 `root.after()` 周期性触发扫描，并记录上次扫描时间，避免重复扫描过密。

4. 接入或尊重 `show_notifications`  
   至少用该配置控制 messagebox 是否弹出；若需要 macOS 系统通知，可再增加平台通知实现。

5. 扩展扫描器覆盖范围  
   Homebrew 增加 cask；Go 尝试读取模块来源或命令版本；pip 可支持多个解释器/虚拟环境策略。

## 校验

已执行：

```bash
python3 -m py_compile main.py config.py storage.py scanner.py report.py ui.py
```

结果：通过，无语法错误。
