# 架构设计

## 分层架构

插件采用三层架构设计：

1. **入口层** — `main.py`：命令处理器和 LLM 工具注册；
1. **业务逻辑层** — `service.py`：查询编排、格式化、错误处理；
1. **基础设施层** — `client.py`：Dida365 Open API HTTP 客户端封装；
1. **支撑模块**
   - `models.py` — 数据模型；
   - `exceptions.py` — 异常层次；
   - `time_utils.py` — 时区工具。

### 各模块职责

- **`main.py`** — 插件入口，继承 `Star` 类。注册 AstrBot 命令处理器和 LLM Function Tool。负责构建配置对象和依赖注入。
- **`client.py`** — `DidaClient` 类封装了所有 Dida365 Open API 的 HTTP 调用。使用 `httpx.AsyncClient` 实现异步请求。
- **`service.py`** — `DidaService` 类包含所有业务逻辑：任务收集、过滤、排序、格式化、任务更新（`update_task_details` 封装了 fetch-merge-POST 完整流程），以及错误消息的友好化处理。
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

- 对带时区信息的时间戳进行正确的时区转换
- 对不带时区的时间戳按配置的时区进行假设
- 最终统一转换为目标时区

### 4. 错误处理

所有 Dida365 API 错误通过 `DidaClient._request()` 方法集中处理，转换为特定的异常类型 (`DidaAuthenticationError`、`DidaNotFoundError`、`DidaApiError`、`DidaNetworkError`) 。`DidaService.explain_error()` 将这些异常转换为用户友好的中文消息。

### 5. LLM Function Tool 注册

在 `main.py` 的 `__init__` 中注册 LLM 工具，使插件在支持 LLM 的会话中可通过自然语言调用。

## Dida365 API 技术细节

| 端点 | 方法 | 说明 |
|------|------|------|
| `/open/v1/project` | GET | 获取所有项目 |
| `/open/v1/project/{id}/data` | GET | 获取项目内所有任务 |
| `/open/v1/project/inbox/data` | GET | 获取收集箱任务 (独立端点)  |
| `/open/v1/task` | POST | 创建任务 |
| `/open/v1/task/{id}` | POST | 更新任务 (需 POST 完整对象)  |
| `/open/v1/project/{id}/task/{id}/complete` | POST | 完成任务 |
| `/open/v1/project/{id}/task/{id}` | DELETE | 删除任务 |

### API 调用注意事项

1. **认证**：所有请求需要在 Header 中携带 `Authorization: Bearer {access_token}`
2. **Inbox 特殊处理**：收集箱数据不能通过 `/project/{id}/data` 获取，必须使用 `/project/inbox/data`。收集箱的 `projectId` 为虚拟 ID (如 `inbox1014302018`) ，不能用于其他端点
3. **reminders 字段**：更新任务时如果包含 `reminders` 字段，服务端返回 HTTP 500。解决方案是先 GET 获取完整任务，移除 `reminders` 字段后再 POST 更新
4. **任务更新是整体替换**：`POST /task/{id}` 需要传入完整的任务对象，不能只传变更字段

## 数据流

调用链：

1. 用户消息 → 命令处理器 (`main.py`) 
2. → `DidaService` (`service.py`) 
3. → `DidaClient` (`client.py`) 
4. → `httpx.AsyncClient` → Dida365 API
5. ← 结构化响应返回
6. ← 格式化字符串返回
7. ← 返回结果给用户
