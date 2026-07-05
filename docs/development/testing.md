# 测试

## 测试架构

插件采用两层测试策略：**单元测试（Mock 层）**和 **集成测试（真实 API 层）**。单元测试覆盖核心逻辑且无需网络，集成测试仅限于验证真实 Dida365 API 连通性。

### 测试文件结构

```
tests/
├── conftest.py              # 共享 fixtures 和 sys.path 配置
├── test_models.py            # 数据模型序列化
├── test_exceptions.py        # 异常继承链
├── test_time_utils.py        # 时区解析、日期计算
├── test_client.py            # HTTP 客户端（respx mock）
├── test_service.py           # 业务逻辑（排序/过滤/格式化/异常处理）
├── test_main.py              # 插件集成（Mock Context）
└── integration/
    └── test_real_api.py      # 真实 API 连通性测试（可选）
```

### 涉及的技术栈

- **pytest** — 测试框架
- **pytest-asyncio** — 异步测试支持（配置了 `asyncio_mode = "auto"`）
- **respx** — httpx HTTP 请求 mock
- **python-dotenv** — 环境变量加载（仅集成测试使用）

---

## 环境准备

### 安装测试依赖

```bash
pip install -r requirements-dev.txt
```

`requirements-dev.txt` 包含运行时依赖（`httpx`）和所有测试工具。AstrBot 在安装插件时只会读取 `requirements.txt`，不会安装测试依赖。

### Python 版本

项目要求 Python >= 3.11，测试代码同样遵循该要求。

### 模块名称说明

项目源码中的核心数据模块命名为 `models.py`，而非 `types.py`，原因如下：

- Python 标准库有一个同名模块 `types`
- 如果当前工作目录是项目根目录，`import types` 会加载本地的文件而非标准库，导致 Python 自身、pip、pytest 等工具的底层调用因循环 import 崩溃
- 该问题在开发阶段暴露后，已将模块重命名为 `models.py`，避免与标准库冲突

### sys.path 配置说明

插件的源码使用了相对导入（`from .client import DidaClient`、`from .models import ...`），而测试代码需要从项目外部导入这些模块。因此 `tests/conftest.py` 中做了两件事：

1. 将项目的父目录加入 `sys.path`，使 `from astrbot_plugin_dida_improved.xxx import` 可解析
2. 通过 `ASTRBOT_CORE_PATH` 环境变量获取 AstrBot core 的路径并加入 `sys.path`，因为源码中引用了 `astrbot.api` 中的类和函数。该变量从项目根目录的 `.env` 文件中读取（详见下方的 `.env` 配置示例）

---

## 运行测试

### 跑全部测试

```bash
pytest -v
```

测试用例数量视当前代码状态而定，集成测试默认跳过（需要真实 API Token）。

### 跑特定测试文件

```bash
pytest tests/test_service.py -v
pytest tests/test_time_utils.py -v
```

### 跑集成测试（需要 Token）

```powershell
# PowerShell
$env:DIDA_ACCESS_TOKEN="your_token_here"
pytest tests/integration/ -v
```

集成测试需要 Dida365 Open API Access Token。Token 通过环境变量 `DIDA_ACCESS_TOKEN` 传入，也可在项目根目录创建 `.env` 文件：

```
# AstrBot core 源码目录（运行测试必需）
ASTRBOT_CORE_PATH=/path/to/AstrBot/core

# Dida365 Access Token（集成测试需要）
DIDA_ACCESS_TOKEN=your_token_here
DIDA_BASE_URL=https://api.dida365.com/open/v1
```

`.env` 文件已在 `.gitignore` 中，不会提交到版本控制系统。项目提供了一个 `.env.example` 文件作为模板。

### 跳过集成测试

集成测试通过 `@pytest.mark.skipif` 守卫：当 `DIDA_ACCESS_TOKEN` 未设置时自动跳过。这是默认行为，不影响日常开发。

---

## 测试分层详解

### 第一层：单元测试（Mock）

通过 `respx` 模拟 HTTP 响应，或通过 `AsyncMock` 模拟 DidaClient 的数据方法。无需网络、无需 Token、不依赖 AstrBot 运行时。修改任意外层代码后 `pytest -v` 即可在几秒内给出反馈。

| 测试文件 | 依赖 | 测试内容 |
|----------|------|----------|
| `test_models.py` | 无 | DidaTask / DidaProject 字段映射、缺省值、status/priority 边界、tags 容错、DidaPluginSettings.from_config 回退逻辑、_to_optional_int 边界值 |
| `test_exceptions.py` | 无 | 异常继承链（DidaError ← ConfigurationError / NetworkError / ApiError ← AuthenticationError / NotFoundError）、api_error(status, payload) 构造 |
| `test_time_utils.py` | 无 | parse_api_datetime 各种输入（带 Z / 带偏移 / 无时区假设 / 纯日期 / 空串/ 无效）、resolve_timezone_name 回退链、today_in_timezone |
| `test_client.py` | respx | _request 方法：200 JSON / 200 空体 / 401 / 403 / 404 / 500 / 超时 / 连接错误 / 非 JSON 响应；公有方法返回值形状；空 token 和空 base_url 构造异常 |
| `test_service.py` | AsyncMock | _collect_all_tasks（项目失败 / inbox 失败 / 无项目）；list_today_tasks / list_unfinished_tasks 过滤和排序；_is_completed / _is_overdue 各分支；_effective_due_datetime all-day 偏移；_format_single_task 输出；explain_error 异常类型分发；update_task_details（成功 / 未找到 / reminders 自动移除 / 字段合并 / raw 空字典降级） |
| `test_main.py` | MagicMock | _build_settings 时区回退路径、_build_service 构建、_run_service 成功/异常兜底、command 方法的 yield 行为、LLM tool 方法的 return 行为 |

### 第二层：集成测试（真实 API）

通过 Dida365 真实 API 验证插件能否正常连通和获取数据。默认跳过，仅在设置了 `DIDA_ACCESS_TOKEN` 环境变量时执行。

| 测试 | 说明 |
|------|------|
| `test_list_projects` | 获取项目列表，至少返回一个项目 |
| `test_get_inbox_tasks` | 获取收集箱任务，返回列表 |
| `test_probe_read_access` | 端到端只读探测，返回成功消息 |

---

## 未覆盖的测试范围

以下场景需要完整的 AstrBot 运行时环境（启动 PluginManager 和消息平台），当前未通过测试覆盖：

1. **装饰器注册效果** — `@filter.command()`、`@filter.llm_tool()` 的 handler 注册到 `star_handlers_registry` 和 `llm_tools` 的过程，以及事件分发机制
2. **消息平台适配** — 不同平台（QQ、Telegram、Discord 等）的 `AstrMessageEvent` 子类与插件的交互
3. **WebUI 配置变更** — 通过 WebUI 修改配置后插件能否正确响应

建议通过 AstrBot 热重载功能手动验证上述场景：修改代码后在 WebUI 插件管理页点击「重载插件」。

---

## 测试编码规范

### 命名规则

- 测试函数命名格式：`test_<被测试方法>_<场景>`，例如 `test_parse_api_datetime_z_suffix`、`test_list_projects_empty_list`
- 测试类命名格式：`Test<被测试类>`，例如 `TestDidaClientInit`、`TestCollectAllTasks`

### 测试数据管理

- 通用样本数据在 `tests/conftest.py` 中以 pytest fixture 集中管理，尽量模拟 Dida365 API 的真实返回结构
- 边界值和异常数据在测试用例内部现场构造，不放入共享 fixture，避免测试用例间耦合
- fixture 返回值使用原始类型（`dict`、`list`）还是模型类型（`DidaTask`）取决于使用场景：Mock HTTP 响应用原始类型，Mock 业务层用模型类型

### 异步测试

所有涉及 `async def` 的测试方法不需要手动添加 `@pytest.mark.asyncio`。`pyproject.toml` 中已配置 `asyncio_mode = "auto"`，pytest 会自动识别异步测试并启用事件循环。
