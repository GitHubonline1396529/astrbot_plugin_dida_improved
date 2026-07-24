# 架构设计

## 分层架构

插件采用三层架构设计：

1. **入口层** — `main.py`：命令处理器和 LLM 工具注册；
1. **业务逻辑层** — `service/` 包：查询编排、格式化、错误处理；
1. **基础设施层** — `client.py`：Dida365 Open API HTTP 客户端封装；
1. **支撑模块**；
    - `models.py` — 数据模型；
    - `exceptions.py` — 异常层次；
    - `time_utils.py` — 时区工具。

### 各模块职责

- **`main.py`** — 插件入口，继承 `Star` 类。注册 AstrBot 命令处理器和 LLM Function Tool。负责构建配置对象和依赖注入。
- **`client.py`** — `DidaClient` 类封装了所有 Dida365 Open API 的 HTTP 调用。使用 `httpx.AsyncClient` 实现异步请求。
- **`service/` 包** — 业务逻辑层，按业务域拆分为子模块；
    - `service.py` — `DidaService` 核心类：构造、查询编排、公共 API 入口；
    - `task_ops.py` — 任务操作：创建、更新、完成、删除、移动、筛选、列出已完成；
    - `formatting.py` — 输出格式化 (纯函数)；
    - `comments.py` — 任务评论操作；
    - `_helpers.py` — 内部辅助函数 (时区处理、排序、状态判断)。
- **`models.py`** — 数据模型定义，使用 `dataclass(slots=True)`。
- **`exceptions.py`** — 自定义异常层次，所有异常继承自 `DidaError`。
- **`time_utils.py`** — 时区感知的日期时间工具函数。

除此之外，项目主目录下面还有一份 `__init__.py`，这个文件是完全空白的。其仅有的作用就是让 `pytest` 将本项目识别成一个 Python 包，以便测试命令能正确运行。除此之外什么用也没有。

## 核心设计决策

### 1. 收集箱任务独立获取

Dida365 API 的收集箱 (Inbox) 是一个虚拟项目，不能通过 `/project/{id}/data` 访问，必须使用独立的端点 `/project/inbox/data`。因此在 `DidaService._collect_all_tasks()` 中，分别从两个渠道获取任务后合并。实际上，在滴答清单中像这样的虚拟项目一共有 5 个，分别是所有 (All)、收集箱 (Inbox)、今天 (Today)、最近 7 天 (Next 7 Days)、摘要。但是翻阅官方文档并实际进行了一些 API 测试之后发现其中似乎只有这个收集箱可以通过 Inbox 进行访问，其余的都不行。

### 2. 任务更新不包含 reminders

通过 API 更新任务时，如果包含 `reminders` 字段，Dida365 服务端会返回 HTTP 500。因此在更新任务前必须移除该字段。

### 3. 时区处理

Dida365 API 返回的日期时间可能不带时区信息。`parse_api_datetime()` 函数实现了：

- 对带时区信息的时间戳进行正确的时区转换；
- 对不带时区的时间戳按配置的时区进行假设；
- 最终统一转换为目标时区；

### 4. 错误处理

所有 Dida365 API 错误通过 `DidaClient._request()` 方法集中处理，转换为特定的异常类型 (`DidaAuthenticationError`、`DidaNotFoundError`、`DidaApiError`、`DidaNetworkError`)。`DidaService.explain_error()` 将这些异常转换为用户友好的中文消息。

### 5. 已完成任务可见性

「完成」状态的任务通过 `/project/{id}/data` 或 `/project/inbox/data` 均不可见。查询已完成任务需使用 `/task/completed` 端点。

`find_task_by_id()` 采用二级回退策略：

1. 先在未完成任务集合（`_collect_all_tasks()`）中查找；
2. 未命中时，通过 `/task/completed`（无时间范围过滤）回退搜索已完成任务。

这使得 `update_dida_task`、`delete_dida_task`、`complete_dida_task`、`reopen_dida_task` 均能作用于已完成任务。

**注意：** 判断任务是否已完成必须依据 `status` 字段，详见下方 `completedTime` 残留问题。

### 6. LLM Function Tool 注册

通过 `@filter.llm_tool(name=...)` 装饰器在类定义阶段注册 LLM 工具。装饰器解析方法的 Google 风格 docstring 提取参数名和类型，自动构建 OpenAI 兼容的 function-calling schema。注册后的工具会加入全局 `llm_tools.func_list`，由 `PluginManager.load()` 在插件实例化后绑定 handler 并激活。

!!! warning "方法参数名的潜在冲突"
    需要注意的是，LLM 工具的**方法参数名不应与 AstrBot 模块名冲突** (如避免使用 `filter` 作为参数名，因为它也是 `astrbot.api.event` 导出的模块名)，否则可能导致注册被静默跳过！

!!! warning "docstring 参数类型解析的完整机制"
    `@filter.llm_tool` 注册 LLM 工具时，**只从 docstring 的 `Args:` 段落解析参数类型，完全忽略 Python 函数签名的类型注解**。详细的类型映射表与 SUPPORTED_TYPES、常见踩坑点，以及对应的 AstrBot 源码位置，请参阅[编码规范 → LLM 工具注册与参数类型解析](coding-conventions.md#llm-工具注册与参数类型解析)。

### 7. 文档与代码同步策略

插件的功能描述在三个层面间传播，任何新增或修改都应保持三者一致：

1. **元数据层** — `metadata.yaml` 和 `README.md` 声明的高级功能列表；
2. **客户端层** — `client.py` 中 `DidaClient` 的 HTTP 方法；
3. **工具入口层** — `main.py` 中 `@filter.llm_tool` 装饰的 LLM 工具。

每新增一个 LLM 工具，需同步更新以下 6 处，缺一不可：

| 序号 | 文件 | 需确认的内容 |
|------|------|-------------|
| 1 | `client.py` | HTTP 方法已存在；若否，先在此层添加 |
| 2 | `service/service.py` 或 `service/task_ops.py` / `service/comments.py` | 业务编排方法已实现 (视归属域而定)  |
| 3 | `main.py` | `@filter.llm_tool` 装饰器已添加，参数名不与 AstrBot 模块冲突 |
| 4 | `docs/usage/llm-tools.md` | 工具说明、参数描述、使用示例已更新 |
| 5 | `README.md` | LLM 工具表格已同步 |
| 6 | `tests/test_main.py` | 新增工具的 return 行为有测试覆盖 |
| 7 | `release-manifest.json` | 若新增文件，需确认是否应加入发布清单 |

## Dida365 API 技术细节

### 官方文档罗列的所有端口

| 端点 | 方法 | 说明 |
|------|------|------|
| `/open/v1/project` | GET | 获取所有项目 |
| `/open/v1/project/{id}` | GET | 按 ID 获取单个项目 |
| `/open/v1/project/{id}/data` | GET | 获取项目内所有任务 |
| `/open/v1/project/inbox/data` | GET | 获取收集箱任务 (独立端点) |
| `/open/v1/task` | POST | 创建任务 |
| `/open/v1/task/{id}` | POST | 更新任务 (需 POST 完整对象) |
| `/open/v1/project/{id}/task/{id}` | GET | 获取单个任务 |
| `/open/v1/project/{id}/task/{id}/complete` | POST | 完成任务 |
| `/open/v1/project/{id}/task/{id}` | DELETE | 删除任务 |
| `/open/v1/task/move` | POST | 移动任务 |
| `/open/v1/task/filter` | POST | 高级筛选任务 |
| `/open/v1/task/completed` | POST | 列出已完成任务 |
| `/open/v1/project/{id}/task/{id}/comments` | GET | 获取任务评论 |
| `/open/v1/project/{id}/task/{id}/comment` | POST | 添加评论 |
| `/open/v1/project/{id}/task/{id}/comment/{cid}` | DELETE | 删除评论 |

### API 调用注意事项

1. **认证**：所有请求需要在 Header 中携带 `Authorization: Bearer {access_token}`；
2. **Inbox 特殊处理**：收集箱数据不能通过 `/project/{id}/data` 获取，必须使用 `/project/inbox/data`。收集箱的 `projectId` 为虚拟 ID (如 `inbox1014302018`)，不能用于其他端点；
3. **reminders 字段**：更新任务时如果包含 `reminders` 字段，服务端返回 HTTP 500。解决方案是先 GET 获取完整任务，移除 `reminders` 字段后再 POST 更新；
4. **任务更新是整体替换**：`POST /task/{id}` 需要传入完整的任务对象，不能只传变更字段。
5. **`completedTime` 残留问题**：任务的 `completedTime` 字段在任务被**完成后再取消完成（重新打开）** 后不会清空，会残留旧的完成时间戳。判断任务是否已完成**必须依据 `status` 字段**，不能单独依赖 `completedTime`。详见 `service/_helpers.is_completed()`。
    - `status=0` = 未完成 (即使 `completedTime` 非空)；
    - `status=1` = 已完成 (部分端点使用)；
    - `status=2` = 已完成 (Open API 规范标准值)。

## 数据流

调用链：

1. 用户消息 → 命令处理器 (`main.py`)；
2. → `DidaService` (`service.py`)；
3. → `DidaClient` (`client.py`)；
4. → `httpx.AsyncClient` → Dida365 API；
5. ← 结构化响应返回；
6. ← 格式化字符串返回；
7. ← 返回结果给用户。
