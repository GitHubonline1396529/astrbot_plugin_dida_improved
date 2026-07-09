# 开发环境搭建

由于本项目的作者最开始就是因为使用其他人的插件感觉缺少了一些功能，才决定自己写代码的，所以也同样非常欢迎任何人加入协作。为了解决协作开发上的所有困难，也为了能够让 Vibe Coding 用户能够无痛参与开发。本项目的作者为这个项目保留了尽可能做到完善的开发文档和 Agent 引导。

## 前置要求

首先，在开始开发本插件之前，你至少应该了解如下两个文档的基本内容：

- 滴答清单 API 的手册：[TickTick Developer](https://developer.dida365.com/docs#/openapi)；
- Astrbot 插件文档：[AstrBot 插件开发指南 🌠 | AstrBot](https://docs.astrbot.app/dev/star/plugin-new.html)。

如果你需要开发本插件，建议您首先配置您的开发环境。这里需要：

- Python >= 3.11；
- Git；
- [AstrBot](https://github.com/AstrBotDevs/AstrBot) 开发实例，即运行在您的主机上的 Astrbot。

## 克隆项目

本项目的开源地址为 [GitHubonline1396529/astrbot_plugin_dida_improved](https://github.com/GitHubonline1396529/astrbot_plugin_dida_improved.git)，可以通过 Git 下载，当然直接下载源码压缩包也是没有问题的。但是务必要注意必须下载 `dev` 分支上的文件。

```bash
git clone -b dev https://github.com/GitHubonline1396529/astrbot_plugin_dida_improved.git
cd astrbot_plugin_dida_improved
```

!!! caution "注意分支"
    这里给出的 `git` 命令通过 `-b` 参数指定了 `dev` 分支，如果手工下载源码压缩包的话，请先在 GitHub 界面左上角的分支切换选项切换到 `dev` 分支，然后再下载源码包。否则您下载的压缩包可能不包含开发所需的全部文件！

## 安装依赖

### 方式一：使用虚拟环境 (推荐) 

首先，创建一个虚拟环境：

```bash
python -m venv .venv
```

然后，激活虚拟环境。在 **Windows** 下执行：

```bash
.venv\Scripts\activate
```

在 **Linux/macOS** 下执行：

```bash
source .venv/bin/activate
```

最后，安装开发依赖：

```bash
pip install -r requirements-dev.txt
```

### 方式二：直接安装

```bash
pip install -r requirements-dev.txt
```

`requirements-dev.txt` 包含运行时依赖 (`httpx`)、项目测试用的 `pytest`、代码风格化检查所需的 `ruff`、文档开发使用的 `mkdocs` 相关的库 (主题包和 docstring 抽取工具) 和所有测试工具。AstrBot 在安装插件时不会读取此文件，用户侧不会安装测试依赖。当然，您也可以视实际情况手动安装所需的部分。

### 测试环境

测试框架通过 `tests/conftest.py` 中的 AstrBot 模块桩 (stub) 隔离了对 AstrBot 运行时的依赖，因此运行测试 **不需要 AstrBot 环境**。clone 项目后直接执行以下命令即可全部跑通：

```bash
pip install -r requirements-dev.txt
pytest -v
```

!!! tip "需要真实的 Token"
    集成测试需要真实的 Dida365 Access Token，默认跳过。

!!! note "测试文档"
    本项目提供了足够详细而且完整的测试文档，请自行导航访问。

## 运行测试

```bash
pytest -v
```

运行全部单元测试 (含 Mock 和集成测试)。集成测试需要 Dida365 Access Token 才会执行，默认自动跳过。

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
    本文的对于"文档工作流"有非常详细的记叙。您可以通过左侧索引菜单访问。
