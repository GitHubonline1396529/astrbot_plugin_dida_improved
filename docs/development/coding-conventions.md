# 编码规范

## Python 风格

- 遵循 Google Python Style Guide 文档字符串格式（`Args:`、`Returns:`、`Raises:`）
- 使用 `ruff` 进行格式化和 lint 检查
- 行宽 80 列（在 `pyproject.toml` 中配置）
- 每个模块顶部添加 `from __future__ import annotations`

## 代码规范

- 使用 `pathlib.Path` 处理文件路径，不使用原始字符串路径
- 使用 `astrbot.api.logger` 进行日志记录
- 使用 `httpx.AsyncClient` 进行 HTTP 请求
- 优先使用 `dataclass(slots=True)` 作为数据容器
- 为所有函数签名添加类型注解
- 不添加不必要的注释，仅在逻辑不直观时才注释
- 保持函数短小精悍，遵循 KISS 原则
- Python 源码全部使用英文，包括字符串字面量和日志文本

## AstrBot 插件规范

- 插件类必须继承自 `Star` 并位于 `main.py`
- 使用 `@register("plugin_name", ...)` 装饰器
- 使用 `@filter.command()` 注册命令处理函数
- 使用 `@filter.permission_type()` 控制访问权限
- 通过 `yield event.plain_result(...)` 返回结果
- 在 `__init__` 中接受 `config: AstrBotConfig` 获取插件配置
- 配置通过 `_conf_schema.json` 在 WebUI 中自动渲染

## 构建与验证

```bash
ruff format .
ruff check .
```

## 测试规范

- 测试文件命名使用 `test_` 前缀，放在 `tests/` 目录下
- 测试函数命名格式：`test_<被测方法>_<场景>`，如 `test_parse_api_datetime_z_suffix`
- 共享测试数据在 `tests/conftest.py` 中以 pytest fixture 集中管理
- 边界值和异常数据在测试用例内现场构造，不放入共享 fixture
- 异步测试不需要手动添加 `@pytest.mark.asyncio`，`pyproject.toml` 中已配置 `asyncio_mode = "auto"`
- 遵守与业务代码相同的代码风格：ruff 80 列格式、Google 风格 docstring、源码全部使用英文

## 提交规范

本项目遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范。

格式：`type(scope): short description`

- **全小写** — 首字母不大写
- **末尾不加句号**
- **不使用 gitmoji**
- **使用英文** — 与源码语言保持一致

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
