# 变更日志

## v0.2.0-beta

### 重构

- 将单文件 `service.py` 拆分为 `service/` 包，按业务域划分为 `service.py`、`task_ops.py`、`comments.py`、`formatting.py`、`_helpers.py`，提升可维护性。

### 新增

- 新增 `move_dida_task` LLM 工具：支持将任务移动到指定项目或收集箱；
- 新增 `filter_dida_tasks` LLM 工具：支持按标题、优先级、标签、项目、日期范围等条件筛选任务；
- 新增 `list_completed_dida_tasks` LLM 工具：查询指定日期范围内的已完成任务；
- 新增 `list_dida_task_comments` / `add_dida_task_comment` / `delete_dida_task_comment` LLM 工具：任务评论的完整 CRUD；
- 在 `DidaService` 中新增对应的业务方法（`move_task()`、`filter_tasks()`、`list_completed_tasks()`、评论相关方法）；
- 新增 `release-manifest.json`，定义发布文件清单，配合 CI 工作流实现 `main` 分支自动同步；
- 测试引入 AstrBot 模块桩（`tests/conftest.py`），不再依赖本机 AstrBot 安装目录，测试完全自包含。

### 文档

- 全面整改所有文档：架构说明、API 参考、编码规范、开发/发布工作流、环境搭建、测试指南均同步更新；
- 用户文档（README、配置说明、LLM 工具用法、安装指南、变更日志）同步至最新功能。

## v0.1.1-beta

### 杂项

- 新增 `logo.png` 插件图标，用于 AstrBot WebUI 插件列表展示。

## v0.1.0-beta

### 修复

- 修复 `list_dida_tasks` 因参数名 `filter` 与 AstrBot 模块名冲突导致生产环境注册失败的问题，已重命名为 `task_filter`；

### 新增

- 新增 `create_dida_task` LLM 工具：支持标题、项目、备注、优先级、标签、截止日期；
- 新增 `complete_dida_task` LLM 工具：按任务 ID 标记完成；
- 新增 `delete_dida_task` LLM 工具：按任务 ID 永久删除；
- 在 `DidaService` 中新增对应的 `create_task()`、`complete_task()`、`delete_task()` 业务方法；
- `docs/development/architecture.md`：新增「文档与代码同步策略」章节，修正 LLM 工具注册描述。

## v0.0.1-beta — 初始预发布

首个预发布版本，核心功能已基本就绪。

### 功能

- 查询所有未完成任务 (含收集箱 / Inbox)；
- 查询今日到期任务；
- 创建、完成、更新、移动、删除任务；
- 管理员指令 (`/dida_ping`、`/dida_probe`) 和 LLM 自然语言 (`list_dida_projects`、`list_dida_tasks`) 两种交互方式；
- 正确支持收集箱 (Inbox) 任务；
- 所有 Python 代码及日志统一使用英文。
