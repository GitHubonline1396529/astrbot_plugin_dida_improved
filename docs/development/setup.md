# 开发环境搭建

## 前置要求

如果你需要开发本插件，建议您首先配置您的开发环境。这里需要：

- Python >= 3.11；
- Git；
- [AstrBot](https://github.com/AstrBotDevs/AstrBot) 开发实例，即运行在您的主机上的 Astrbot。

## 克隆项目

```bash
git clone https://github.com/GitHubonline1396529/astrbot_plugin_dida_improved.git
cd astrbot_plugin_dida_improved
```

## 安装依赖

开发本插件所需的依赖比用户侧更多，额外的依赖项位于 `requirements-dev.txt`。使用如下的命令可以安装。

```bash
pip install -r requirements-dev.txt
```

`requirements-dev.txt` 包含运行时依赖 (`httpx`) 、项目测试用的 `pytest`、代码风格化检查所需的 `ruff`、文档开发使用的 `mkdocs` 相关的库 (主题包和 DocString 抽取工具) 和所有测试工具。AstrBot 在安装插件时不会读取此文件，用户侧不会安装测试依赖。当然，您也可以视实际情况手动安装所需的部分。

## 运行测试

```bash
pytest -v
```

运行全部单元测试（含 Mock 和集成测试）。集成测试需要 Dida365 Access Token 才会执行，默认自动跳过。

进入测试目录运行单个文件：

```bash
pytest tests/test_service.py -v
```

## 本地预览文档

本项目的文档使用 MkDocs 工具自动构建。

```bash
mkdocs serve
```

浏览器访问 `http://localhost:8000/` 即可实时预览。

## 构建文档

如果你对文档进行了修改更新，可以使用如下的命令重新生成新的文档。

```bash
mkdocs build  # 执行文档自动构建命令
```

构建产物在 `site/` 目录下。

!!! note "文档工作流"
    本文的对于“文档工作流”有非常详细的记叙。您可以通过左侧索引菜单访问。