# API 参考

本文档通过从代码的 docstring 自动生成，涵盖了插件各模块的公开 API，与源码内容保持一致，只不过主要是英文的。(项目作者意思有强迫症，中文在 Visual Studio Code 里面看上去不是等宽的，而是微调过字距的状态，文本末尾对不齐，长一阵短一阵看起来非常的难受。)

除了自动生成的 API 签名与 docstring 之外，本文档在每个模块标题下方还配有手动编写的说明性段落，概括该模块的职责、边界、以及在整个三层架构中所处的位置，辅助读者快速理解项目结构。

## 客户端

`client` 模块是三层架构的**基础设施层**，封装了所有与 Dida365 Open API 的 HTTP 通信。核心类 `DidaClient` 基于 `httpx.AsyncClient` 实现异步请求，统一负责认证头部构建、URL 拼接、超时控制，并将各种非 2xx 响应映射为对应的异常类型 (401/403 → `DidaAuthenticationError`，404 → `DidaNotFoundError`，其余 ≥400 → `DidaApiError`，网络层异常 → `DidaNetworkError`)。业务逻辑层不直接调用 `httpx`，所有 API 调用全部经由 `DidaClient` 的公开方法完成。

::: client.DidaClient

## 插件入口

`main` 模块是插件的**入口层**。`DidaImprovedPlugin` 继承自 `Star`，根据 Astrbot 插件开发文档的标准：

- 通过 `@filter.command` 装饰器注册 AstrBot 文本命令 (`dida_ping`、`dida_probe`)；
- 通过 `@filter.llm_tool` 装饰器注册 LLM Function Tool (如 `list_dida_projects`、`create_dida_task`、`update_dida_task` 等 12 个工具)。

除此之外，另有：

- `_build_service()` 方法负责依赖注入——从配置构建 `DidaPluginSettings`，再注入 `DidaClient` 来组装 `DidaService`；
- `_run_service()` 提供统一的 try/except 外壳，捕获任何异常后交由 `DidaService.explain_error()` 转译为用户友好的消息。

::: main.DidaImprovedPlugin

## 业务服务

`service` 包是三层架构的**业务逻辑层**，以 `DidaService` 为核心控制器。它编排所有面向用户的业务流程：跨项目与收件箱的任务聚合 (`_collect_all_tasks()`)、今天到期/未完成/已完成任务列表的生成、任务的创建/更新/完成/删除/移动，以及任务评论的增删查。`DidaService` 本身不直接发 HTTP 请求，而是将底层操作委托给 `task_ops`、`comments`、`formatting`、`_helpers` 等子模块。`explain_error()` 静态方法将所有 `DidaError` 异常转译为可供 AstrBot 直接回复的中文消息。

::: service.DidaService

## 业务逻辑辅助函数

`_helpers` 模块是纯函数集合，**零 I/O、零副作用**。它提供一系列作用于 `DidaTask` 对象的谓词和工具函数：判断任务是否完成 (`is_completed`)、解析 API 返回的日期时间字符串 (`parse_datetime`——考虑任务的时区覆盖)、计算有效到期时间 (`effective_due_datetime`——对全天任务自动减一天以确保日期比较符合直觉)、检查是否今天到期或逾期 (`is_task_due_today` / `is_overdue`)、以及构建排序键 (`sort_due_value` / `unfinished_sort_key`) 和序列化方法 (`task_to_raw`)。这些函数被 `DidaService` 大量消费，也是其他 `service.*` 子模块的底层依赖。

::: service._helpers.is_completed
::: service._helpers.parse_datetime
::: service._helpers.effective_due_datetime
::: service._helpers.is_task_due_today
::: service._helpers.is_overdue
::: service._helpers.sort_due_value
::: service._helpers.unfinished_sort_key
::: service._helpers.task_to_raw

## 任务 CRUD 操作

`task_ops` 模块是任务操作的具体实现层，在 `DidaClient` 的 HTTP 方法之上添加了参数校验和文档中强调的注意事项。每个函数接受 `DidaClient` 为首个参数，将实际 HTTP 调用委托给 client 层。`create_task` 会校验标题非空；`update_task` 通过 `raw` 参数实现 full-object replacement (使用时必须注意先通过 `task_to_raw` 获取当前任务快照，合并变更后传入)；`filter_tasks` 和 `list_completed_tasks` 支持可选的复合筛选条件。`DidaService` 中的高层方法 (如 `update_task_details`) 在此基础上进一步封装了查找 → 合并 → 剥离 `reminders` → 更新的完整流程。

::: service.task_ops.create_task
::: service.task_ops.update_task
::: service.task_ops.complete_task
::: service.task_ops.delete_task
::: service.task_ops.move_task
::: service.task_ops.filter_tasks
::: service.task_ops.list_completed_tasks
::: service.task_ops.get_task_by_id

## 任务评论操作

`comments` 模块是 `DidaClient` 评论相关端点的薄封装，提供三个标准的 CRUD 函数：获取评论列表、添加评论、删除评论。每个函数接受 `project_id` 和 `task_id` 来定位目标任务，直接委托给 client 层发起 HTTP 请求。`DidaService` 中的同名方法 (`get_task_comments`、`add_task_comment`、`delete_task_comment`) 在此基础上加入错误处理，是 LLM 工具 (`get_dida_task_comments`、`add_dida_task_comment`、`delete_dida_task_comment`) 的直接调用目标。

::: service.comments.get_task_comments
::: service.comments.add_task_comment
::: service.comments.delete_task_comment

## 任务格式化

`formatting` 模块是纯函数集合，负责将 `DidaTask` / `DidaTaskWithProject` 的内部字段转换为人类可读的纯文本字符串，供 AstrBot 直接回复。`format_due` 考虑全天/定时任务的差异；`format_priority` 将 API 的整数编码 (0/1/3/5) 映射为可读标签；`format_status` 返回 `"completed"` 或 `"open"`；`format_single_task` 整合所有字段并支持可选的序号前缀和逾期标记，是任务列表输出的核心函数。

::: service.formatting.format_due
::: service.formatting.format_priority
::: service.formatting.format_status
::: service.formatting.format_single_task

## 数据模型

`models` 模块定义了插件内部使用的全部数据结构，全部实现为 `@dataclass(slots=True)` 以节省内存并加速属性访问。每个模型类都提供了 `from_api()` 工厂方法，用于将 Dida365 API 返回的 JSON 字典反序列化为类型安全的 Python 对象。`DidaPluginSettings` 承载插件配置并在三层间传递；`DidaTask` 是核心数据载体，包含任务的全部字段 (含子任务列表 `items: list[ChecklistItem]`)；`DidaProjectData` 将项目与其任务列表绑定，是整个数据流的顶层容器；`DidaTaskWithProject` 将任务与所属项目上下文关联，是任务列表展示的基本单元。

::: models.DidaPluginSettings
::: models.DidaProject
::: models.ChecklistItem
::: models.DidaTask
::: models.DidaProjectData
::: models.DidaTaskWithProject
::: models._to_optional_int

## 异常

`exceptions` 模块定义了插件的自定义异常层次，所有异常继承自基类 `DidaError` (继承自 `Exception`)。

- `DidaConfigurationError` 在缺少访问令牌或 API 基址时抛出；
- `DidaNetworkError` 在 HTTP 连接超时或失败时抛出；
- `DidaApiError` 携带 `status` 和 `payload` 属性记录服务端返回的 HTTP 状态码与响应体摘要；
- `DidaAuthenticationError` 和 `DidaNotFoundError` 继承自 `DidaApiError`，分别对应 401/403 和 404 响应；
- `DidaValidationError` 在插件侧参数校验失败时抛出。

`DidaClient._request()` 是异常的集中抛出点，`DidaService.explain_error()` 是异常的集中消费点，二者形成闭环。

::: exceptions.DidaError
::: exceptions.DidaConfigurationError
::: exceptions.DidaNetworkError
::: exceptions.DidaApiError
::: exceptions.DidaAuthenticationError
::: exceptions.DidaNotFoundError
::: exceptions.DidaValidationError

## 时区工具

`time_utils` 模块为整个插件提供统一的时区感知日期时间支持。`resolve_timezone_name()` 负责校验并回退 IANA 时区名称——传入无效名称时不会崩溃而是回落到系统或默认时区。`parse_api_datetime()` 是核心函数，处理 Dida365 API 返回的各种 datetime 格式 (含时区偏移、`Z` 后缀、无分隔符偏移量、纯日期等边缘情况)，对不带时区的时间戳按传入的 `assume_timezone_name` 做假设，最终统一转换至目标时区。`now_in_timezone()` 和 `today_in_timezone()` 提供便捷的当前时刻/日期获取方式，被 `DidaService` 的查询方法广泛使用。

::: time_utils.resolve_timezone_name
::: time_utils.get_timezone
::: time_utils.now_in_timezone
::: time_utils.today_in_timezone
::: time_utils.parse_api_datetime
