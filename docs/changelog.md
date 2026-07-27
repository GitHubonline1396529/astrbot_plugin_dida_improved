# 变更日志

## v0.3.0

### 修复

- 修复 CI 工作流 `sync-main-on-tag.yml` 中推送命令使用硬编码 PAT token 的问题，改用 `git push origin main --force`，简化认证方式；
- 修复 `AGENTS.md` 构建与验证区块中格式对齐不一致的问题。

### 文档

- `README.md`：全面重写格式化，使用 Emoji 装饰标题和分类；添加在线文档链接；重写安装说明为「通过 Git 安装」和「手动安装」两种方式；新增「项目」章节包含开源地址和文档链接；简化项目结构展示并移入项目章节；
- `docs/usage/llm-tools.md`：全面重写使用示例，从逐个工具说明改为场景化的自然语言交互示例（开启高效的一天、从灵感到执行等），增强可读性和实用性；
- `docs/usage/commands.md`：指令返回示例格式从代码块改为 blockquote 引用风格；
- `docs/installation.md`：新增手动安装方式说明，补充 Git 安装步骤细节，添加配置提醒；
- `docs/index.md`：添加文档链接，移除重复的安装部分（已迁移至 `installation.md`）；
- `docs/development/release-workflow.md`：移除 `RELEASE_TOKEN` 和分支保护相关说明；更新误推 `main` 分支的处理指南；
- `docs/development/coding-conventions.md`：修正 docstring 标记语法示例中的格式化问题。

## v0.2.3-beta

### 新增

- 新增 `reopen_dida_task` LLM 工具：支持将已完成任务重新打开（取消完成），重置 `status` 为 `0`，使其重新出现在活跃任务列表中；
- 新增 `_find_task_by_id()` 业务方法：先搜索未完成任务，未找到时自动回退到搜索已完成任务，为跨状态任务操作提供基础。

### 修复

- 修复 `update_dida_task` 无法修改已完成任务的问题：旧版本中 `update_task()` 仅从项目数据中查找任务，已完成任务不在项目数据中导致无法定位。现通过 `_find_task_by_id()` 统一查找逻辑，支持对已完成任务进行编辑和重新打开操作；
- 修复已完成任务重新打开后无法再次标记为未完成的问题：新增 `reopen_task()` 业务方法，正确将任务 `status` 设为 `0` 并推送更新，同时移除 `completed_time` 残留旧值带来的误判风险。

### 文档

- 全面整改 docstring 格式：将 Google 风格 docstring 中的双反引号（`` ```backticks``` ``）统一替换为 Markdown 单反引号（`` `code` ``），以提升 API 参考文档的渲染效果；
- `docs/development/coding-conventions.md`：补充 docstring 标记语法规范，明确应使用 Markdown 单反引号而非双反引号；
- `docs/usage/llm-tools.md`：新增 `reopen_dida_task` 工具说明；
- `docs/development/architecture.md`：同步更新「查找任务」流程说明、`reopen_task` 相关架构描述；
- `docs/README.md`、`docs/index.md`、`docs/development/testing.md`：小幅优化措辞和排版。

### 测试

- 新增 `reopen_task` 单元测试（`tests/test_service.py`）：覆盖重新打开已完成任务、重新打开未完成任务（应拒绝）、查找已完成任务等场景；
- 新增 `_find_task_by_id` 单元测试：覆盖搜索未完成任务、回退到已完成任务、找不到任务等路径。

## v0.2.2-beta

### 修复

- 修复 LLM 工具 docstring 中 `limit` 参数类型标注：将 `(integer)` 改为 `(number)`，以兼容 AstrBot 的 docstring 解析器（不支持 `integer` 类型关键字）；
- 修复 `list_completed_dida_tasks` 的 `end_date` 参数 docstring 中残留的繁体中文标点 `、`；
- 修复 `docs/configuration.md` 中 Client ID 说明的标点符号。

### 文档

- `docs/development/coding-conventions.md`：大幅补充 LLM 工具编写规范，明确 docstring 参数类型应使用 AstrBot 解析器支持的关键字（如 `string`、`number`、`boolean`），避免使用 Python 原生类型名（如 `integer`、`str`、`int`）；
- `docs/development/architecture.md`：同步更新 LLM 工具注册与参数类型解析的相关说明。

## v0.2.1-beta

### 新增

- 新增 `display_limit` 配置项：支持通过插件配置控制列表查询（任务/项目）每次最多返回的条目数，默认为 50。设为 0 则不截断；Agent 仍可通过 LLM 工具参数覆盖该配置；
- LLM 工具 `list_dida_tasks`、`list_completed_dida_tasks` 新增 `limit` 参数，可动态控制返回条目数；
- 业务层 `list_projects_summary()`、`list_today_tasks_summary()`、`list_unfinished_tasks_summary()`、`filter_tasks()`、`list_completed_tasks()` 方法均接入 `display_limit` 配置，硬编码截断值（10/20/30）全部移除。

### 修复

- 修复 `is_completed()` 完成状态检测逻辑：`status` 字段作为首要判定依据（`status in (1, 2)` 视为已完成），不再单独依赖 `completed_time`。当任务被**重新打开**（取消完成）时 `status` 重置为 `0`，但 `completed_time` 可能残留旧值，旧逻辑会误判为已完成。

### 文档

- `docs/configuration.md`：新增 `display_limit` 配置说明；
- `docs/usage/llm-tools.md`：同步更新 `list_dida_tasks` 和 `list_completed_dida_tasks` 的 `limit` 参数；
- `docs/development/architecture.md`：补充关于 `completedTime` 字段与任务状态的说明。

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
