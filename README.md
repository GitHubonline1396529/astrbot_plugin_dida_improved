# Astrbot 滴答清单插件改进版

滴答清单改进版 —— 在 AstrBot 中连接 Dida365/TickTick/滴答清单，支持完整的任务管理功能，包括收集箱 (Inbox) 任务。[点击此处链接访问项目文档页面](https://githubonline1396529.github.io/astrbot_plugin_dida_improved/)。

事情的起因是我之前使用 [wuhuqif176](https://github.com/wuhuqif176)/[astrbot_plugin_dida_todo](https://github.com/wuhuqif176/astrbot_plugin_dida_todo) 的时候发现插件的使用无法访问滴答清单的内建清单 `Inbox` 的问题。于是我 Fork 了原仓库，改进了插件项目，改进后的代码也在刚才提到的文件夹里面。我向原作者提交了 Issue 并声称可以提供 PR，但是他还没有回复我。于是我打算独立开发 `astrbot_plugin_dida_improved`，支持更多 API 功能。

最初写这个插件的时候，我的预期原本只是两三个几百行代码的小脚本，但是后来发现由于插件涉及到与 Dida 365 的 API 进行交互，实现完整功能所需的实际代码体量大了许多。虽然这是我第一次尝试通过 Vibe Coding 的方式开发一个项目，但我还是尽我所能对项目进行了测试，并保障代码的质量。希望大家用得喜欢。

## ✨ 特性

本项目目前实现了如下的功能：

- 查询所有未完成任务 (含收集箱)；
- 查询今日到期任务；
- 查询已完成任务 (支持按时间范围和项目筛选)；
- 高级筛选 (按项目、日期范围、优先级、标签、状态)；
- 创建、完成、更新、移动、删除任务；
- 任务评论 (查看/添加/删除)；
- 按项目 ID 和任务 ID 查询单个任务详情；
- 管理员指令 / 自然语言 LLM 两种交互方式；
- 正确处理收集箱 (Inbox) 任务 (原插件遗漏的功能)。

## 📦 安装

目前我正在着手将这个插件发布到 Astrbot 的插件市场，如果发布成功就可以在 Astrbot 的插件页面直接下载安装。在此之前，可以先通过手动安装的方式使用本插件，具体的操作流程如下：

1. 从本项目的仓库地址 [astrbot_plugin_dida_improved](https://github.com/GitHubonline1396529/astrbot_plugin_dida_improved) 下载插件的源码压缩包 (`main` 分支)；
2. 将插件目录解压后放置到 AstrBot 的运行时目录下的 `data/plugins/` 下；
3. 在 WebUI 中重载插件，或者直接重启 AstrBot；
4. 在插件配置中至少应当填写您的 `access_token`。

其他的安装方法 (比如，如果您有 Git)，请参阅 [插件文档 - 安装](https://githubonline1396529.github.io/astrbot_plugin_dida_improved/installation/)。

> [!NOTE]
>
> 需要注意的是，由于安装方式的不同，运行时目录可能略有区别。具体的路径请参阅 [Astrbot 官方文档中有关部署方法的部分](https://docs.astrbot.app/deploy/astrbot/package.html)。

## ⚙️ 配置

插件提供了如下的配置选项，其中 `access_token` 是一个必填项，如不填写，则项目将无法使用。

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `access_token` | string | (空) | Dida365 Open API Access Token，必填 |
| `api_base_url` | string | `https://api.dida365.com/open/v1` | API 基础地址 |
| `default_project` | string | (空) | 创建任务时的兜底项目 |
| `timezone` | string | `Asia/Shanghai` | 插件时区 |
| `request_timeout_seconds` | int | `15` | API 请求超时秒数 |

### 🔑 获取 Access Token

这里只是简单提一下，本项目的文档当中有非常详细的 [创建 Access Token 的方法](https://githubonline1396529.github.io/astrbot_plugin_dida_improved/configuration/)。

1. 访问 [Dida365 Developer](https://developer.dida365.com)；
2. 登录后创建应用，获取 Access Token；
3. 将 Token 填入插件配置的 `access_token` 字段。

## 🚀 使用方法

### 👤 管理员指令

本项目提供了如下的两个测试用指令，以确保项目处于正常工作的状态。所有指令需以管理员身份执行。

| 指令 | 说明 |
|------|------|
| `/dida_ping` | 检查插件加载状态和配置 |
| `/dida_probe` | 执行一次只读 API 探测 |

### 🤖 LLM 自然语言交互

插件注册了以下 LLM Function Tool，需在支持 LLM 的会话中由 Astrbot 自行调用。用户只需要用自然语言指挥 Agent 即可。

| 工具名称 | 功能 |
|----------|------|
| `list_dida_projects` | 列出所有滴答清单项目 (含收集箱) |
| `list_dida_tasks` | 查询任务列表，支持 "today"/"unfinished" 筛选 |
| `create_dida_task` | 创建新任务 |
| `complete_dida_task` | 完成任务 |
| `update_dida_task` | 更新任务的任意字段 (标题、备注、截止日期、优先级等) |
| `delete_dida_task` | 删除任务 |
| `reopen_dida_task` | 重新打开已完成任务 |
| `move_dida_task` | 移动任务到其他项目 |
| `get_dida_task_detail` | 获取单个任务的详细信息 |
| `list_completed_dida_tasks` | 查询已完成任务 |
| `get_dida_task_comments` | 查看任务评论 |
| `add_dida_task_comment` | 添加评论 |
| `delete_dida_task_comment` | 删除评论 |

在对话中直接说"帮我创建一个任务"或"我的待办有哪些"即可触发。

## 📁 项目

### 🌐 开源地址

本插件的开源地址为 [GitHubonline1396529](https://github.com/GitHubonline1396529)/[astrbot_plugin_dida_improved](https://github.com/GitHubonline1396529/astrbot_plugin_dida_improved)，欢迎任何人参与本插件的开发。

### 📖 文档

本项目通过 GitHub Pages 部署文档，可通过 [此处的链接](https://githubonline1396529.github.io/astrbot_plugin_dida_improved/) 进行访问，或直接浏览完整源码中的 `docs/` 目录。文档包含插件的使用方法和开发的详细指南，对于 LLM Agent，请务必在开始开发整个项目之前仔细阅读文档里的内容。或通过文档索引查阅有关内容。

### 🏗️ 项目结构

本项目的结构如下，此处只列出了插件运行所需的文件。`main` 分支的源码归档中 **不会包含** 文档源码 (`docs/`、`mkdocs.yml`)、测试套件 (`tests/`)、开发依赖 (`requirements-dev.txt`、`pyproject.toml`)、CI/CD 工作流 (`.github/`) 等仅用于开发的辅助文件。若需查看完整的开发项目结构 (包含上述所有文件)，请切换到 `dev` 分支。

- `logo.png` — 插件图标
- `main.py` — 插件入口：命令处理器和 LLM 工具注册
- `client.py` — Dida365 Open API HTTP 客户端
- `service/` — 业务逻辑层 (包目录)
  - `__init__.py` — 包入口，导出 DidaService
  - `service.py` — DidaService 主类 (查询编排、公共 API)
  - `task_ops.py` — 任务操作 (CRUD、移动、筛选、已完成)
  - `formatting.py` — 输出格式化
  - `comments.py` — 任务评论
  - `_helpers.py` — 内部辅助函数
- `models.py` — 数据模型
- `exceptions.py` — 自定义异常层次
- `time_utils.py` — 时区工具
- `_conf_schema.json` — 插件配置 Schema (WebUI 自动渲染)
- `metadata.yaml` — 插件元数据
- `requirements.txt` — Python 依赖
- `README.md` — 本文件
- `LICENSE` — 许可证
- `.gitignore` — Git 忽略规则

## 📄 许可证

本项目基于 2007 年 3 月 19 日发行的第三版 GNU Affero General Public 许可证发布，具体的详情另请参阅 [LICENSE](LICENSE)。
