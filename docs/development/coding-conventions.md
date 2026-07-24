# 编码规范

## Python 风格

- 遵循 Google Python Style Guide 文档字符串格式 (`Args:`、`Returns:`、`Raises:`)；
- 使用 `ruff` 进行格式化和 lint 检查；
- 行宽 80 列 (在 `pyproject.toml` 中配置)；
- 每个模块顶部添加 `from __future__ import annotations`；

## 代码规范

- 使用 `pathlib.Path` 处理文件路径，不使用原始字符串路径；
- 使用 `astrbot.api.logger` 进行日志记录；
- 使用 `httpx.AsyncClient` 进行 HTTP 请求；
- 优先使用 `dataclass(slots=True)` 作为数据容器；
- 为所有函数签名添加类型注解；
- 不添加不必要的注释，仅在逻辑不直观时才注释；
- 保持函数短小精悍，遵循 KISS 原则；
- Python 源码全部使用英文，包括字符串字面量和日志文本。

本项目的 docstring 注释非常重要，因为 MkDocs 会抽取 docstring，用于构建项目的 API 文档。本项目的

- 基本语法基于 Markdown，而不是 reStructedText；
- 为每个函数、方法和类添加 docstring，以一行简明扼要的功能说明开始，随后，取决于所实现功能的复杂程度，为模块添加一个段落的更为详细的说明 (可以没有)；
- docstring 应列出函数的输入、输出参数；
- 需要额外向开发者指明的关键信息，用 Note 标记；
- See Also 可以被追加在 docstring 的末尾，用于索引或者类方法函数被关键性地调用的位置。

### Docstring 中的 Markdown 语法

项目使用 mkdocstrings 将 docstring 渲染为 API 文档，docstring 中的内联标记必须使用 Markdown 语法：

- **字面量/代码引用**：使用单反引号 `` `code` ``，不使用 `\`\`code\`\``（RST 双反引号）或 `:class:\`X\`` 等 RST 角色；
- **交叉引用**：直接用 `` `ClassName` ``、`` `method_name` ``、`` `function_name` ``，不使用 `:class:\`ClassName\``、`:meth:\`method_name\``、`:func:\`function_name\`` 等 Sphinx 角色；
- **参数名引用**：在 docstring 正文中引用参数时，用 `` `param_name` ``（代码风格）而非 `*param_name*`（斜体）；
- **强调**：`**bold**` 和 `*italic*` 均可使用（两种语法一致）；
- **注意块**：使用 Google 风格 `Note:` 段落头，内容缩进 4 空格，不使用 `.. note::` RST 指令；
- **Google 风格段落**：`Note:`、`See Also:`、`Priority:`、`Values:` 等段落头下的**内容必须缩进 4 空格**，否则不会被 griffe 关联到段落头；
- **已知渲染局限**：griffe 会将 `Returns:` 段落中的每行文本独立解析为一条 return entry，而非在一个单元格内折行。跨行描述会在 API 文档中呈现为多个表格行。此行为由 griffe 决定，无法通过格式调整绕过。

## AstrBot 插件规范

- 插件类必须继承自 `Star` 并位于 `main.py`；
- 使用 `@register("plugin_name", ...)` 装饰器；
- 使用 `@filter.command()` 注册命令处理函数；
- 使用 `@filter.permission_type()` 控制访问权限；
- 通过 `yield event.plain_result(...)` 返回结果；
- 在 `__init__` 中接受 `config: AstrBotConfig` 获取插件配置；
- 配置通过 `_conf_schema.json` 在 WebUI 中自动渲染。

## LLM 工具注册与参数类型解析

### docstring 是参数 schema 的唯一来源

`@filter.llm_tool()` 装饰器在解析 LLM 工具的参数时，**只读取 docstring 的 `Args:` 段落**，完全忽略 Python 函数签名中的类型注解。

具体的数据流如下：

1. 读取 `awaitable.__doc__` 字符串。
2. 用第三方库 `docstring_parser.parse()` 解析为结构化 docstring 对象。
3. 遍历 `Docstring.params` 列表，提取每个参数的 `arg_name`、`type_name`、`description`。
4. 通过 `PY_TO_JSON_TYPE` 映射表将提取出的类型名称转为 JSON Schema 类型名。
5. 校验转换后的类型是否属于 `SUPPORTED_TYPES`。
6. 组装成 OpenAI 兼容的 JSON Schema 参数描述。

对应 AstrBot 源码位置：`core/astrbot/core/star/register/star_handler.py` 的 `register_llm_tool()` 函数（约 L626–L659）。

### Python 类型注解为何被忽略

装饰器的实现中没有任何调用 `typing.get_type_hints()` 或 `inspect.signature()` 的逻辑。即使你为函数参数写了精确的 Python 类型注解，它们也不会被读取：

```python
@filter.llm_tool("example")
async def my_tool(self, count: int, name: str) -> str:
    """示例工具。
    Args:
        count (number): 数量。
        name (string): 名称。
    """
```

AstrBot 仍然只从 docstring 读取 `(number)` 和 `(string)`，`count: int` 和 `name: str` 如同不存在。这意味着 docstring 中的类型标注本质上**独立于函数签名的类型注解**，两者必须分开维护。

### 参数 docstring 缺失或遗漏的后果

- **完全没有 docstring** —— `docstring_parser.parse("")` 返回空 Docstring 对象，`args=[]`，工具注册为无参数函数。LLM 调用时不会传入任何参数。
- **docstring 只覆盖了部分参数** —— 装饰器不会对比函数签名与 docstring 参数列表。遗漏的参数不会出现在 schema 中，LLM 不会传递该参数的值，运行时可能因缺少必填参数而抛出 `TypeError`。

建议：为 `@llm_tool` 装饰的方法始终完整编写 Google 风格的 docstring，并确保 `Args:` 下的参数列表与实际函数签名一一对应。

### 类型名称映射表 PY_TO_JSON_TYPE

定义于 `core/astrbot/core/provider/func_tool_manager.py`：

```python
PY_TO_JSON_TYPE = {
    "str": "string",
    "int": "number",
    "float": "number",
    "bool": "boolean",
    "dict": "object",
    "list": "array",
    "tuple": "array",
    "set": "array",
}
```

映射流程：`type_name = PY_TO_JSON_TYPE.get(type_name, type_name)` —— 若在映射表中找到，则替换为对应的 JSON Schema 类型名；若未找到，则保留原始字符串。随后检查该名称是否属于 `SUPPORTED_TYPES`：

```python
SUPPORTED_TYPES = ["string", "number", "object", "array", "boolean"]
```

因此，**表格中的 Python 类型名（`str`/`int`/`float`/`bool`/`dict`/`list`/`tuple`/`set`）和 JSON Schema 原生类型名（`string`/`number`/`boolean`/`object`/`array`）均被支持**。其他名称（如 `integer`、`Map`、自定义类名）则会因不在 `SUPPORTED_TYPES` 中而触发 `ValueError`。

### docstring 中的类型标注写法示例

下表罗列 `Args:` 段落下的参数：

| 写法 | 映射结果 | 有效？ | 说明 |
|------|----------|--------|------|
| `name (string)` | `string` | ✅ | 直接通过 `SUPPORTED_TYPES` |
| `count (number)` | `number` | ✅ | 直接通过 `SUPPORTED_TYPES` |
| `enabled (boolean)` | `boolean` | ✅ | 直接通过 `SUPPORTED_TYPES` |
| `data (object)` | `object` | ✅ | 直接通过 `SUPPORTED_TYPES` |
| `items (array)` | `array` | ✅ | 直接通过 `SUPPORTED_TYPES` |
| `tags (array[string])` | `array` | ✅ | 复合类型，`items.type = string` |
| `name (str)` | `string` | ✅ | 经 `PY_TO_JSON_TYPE` 映射为 `string` |
| `count (int)` | `number` | ✅ | 经 `PY_TO_JSON_TYPE` 映射为 `number` |
| `mapping (dict)` | `object` | ✅ | 经 `PY_TO_JSON_TYPE` 映射为 `object` |
| `limit (integer)` | `integer` | ❌ | `integer` 不在映射表中，也不在 `SUPPORTED_TYPES` 中 |

> **注意**：`int` 被映射为 `number` 而非 `integer`。OpenAI 的 JSON Schema 规范实际接受 `integer` 作为独立的 `type`，但 AstrBot 的映射表未包含它。若需让 LLM 明确知道参数应为整数，可在 `description` 中注明限制。

### 验证方法

如需确认 docstring 被正确解析为 function-calling schema，可在插件初始化时临时添加调试打印：

```python
from astrbot.core.provider.register import llm_tools

for func in llm_tools.func_list:
    print(f"Tool: {func.name}")
    print(f"Parameters JSON Schema: {func.args}")
```

`func.args` 即为最终发送给 LLM 的 JSON Schema 参数描述数组。

## 构建与验证

```bash
ruff format .
ruff check .
```

## 测试规范

- 测试文件命名使用 `test_` 前缀，放在 `tests/` 目录下；
- 测试函数命名格式：`test_<被测方法>_<场景>`，如 `test_parse_api_datetime_z_suffix`；
- 共享测试数据在 `tests/conftest.py` 中以 pytest fixture 集中管理；
- 边界值和异常数据在测试用例内现场构造，不放入共享 fixture；
- 异步测试不需要手动添加 `@pytest.mark.asyncio`，`pyproject.toml` 中已配置 `asyncio_mode = "auto"`；
- 遵守与业务代码相同的代码风格：ruff 80 列格式、Google 风格 docstring、源码全部使用英文。

## 提交规范

本项目遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范。

格式：`type(scope): short description`

- **全小写** — 首字母不大写；
- **末尾不加句号**；
- **不使用 gitmoji**；
- **使用英文** — 与源码语言保持一致。

| 类型       | 用途                          |
|------------|-------------------------------|
| `feat`     | 新功能                        |
| `fix`      | 缺陷修复                      |
| `chore`    | 仓库维护、配置、工具链         |
| `docs`     | 仅文档变更                    |
| `refactor` | 重构，不改变外部行为           |
| `test`     | 新增或修改测试                |
| `ci`       | CI/CD 工作流变更              |

示例：

```
feat(client): add inbox task query support
fix(service): handle empty project list
docs(readme): update installation steps
ci: sync dev to main on tag push
```

## 文档构建

```bash
mkdocs build       # 构建到 site/
mkdocs serve       # 本地预览
mkdocs gh-deploy   # 部署到 GitHub Pages
```
