# Astrbot 滴答清单插件改进版

滴答清单改进版 —— 在 AstrBot 中连接 Dida365/TickTick/滴答清单，支持完整的任务管理功能，包括收集箱（Inbox）任务。

事情的起因是我之前使用 [wuhuqif176](https://github.com/wuhuqif176)/[astrbot_plugin_dida_todo](https://github.com/wuhuqif176/astrbot_plugin_dida_todo) 的时候发现插件的使用无法访问滴答清单的内建清单 `Inbox` 的问题。于是我 Fork 了原仓库，改进了插件项目，改进后的代码也在刚才提到的文件夹里面。我向原作者提交了 Issue 并声称可以提供 PR，但是他还没有回复我。于是我打算独立开发 `astrbot_plugin_dida_improved`，支持更多 API 功能。

## Features

- 查询所有未完成任务（含收集箱）
- 查询今日到期任务
- 创建、完成、更新、移动、删除任务
- 管理员指令 / 自然语言 LLM 两种交互方式
- 正确处理收集箱（Inbox）任务（原插件遗漏的功能）

## 安装

1. 将插件目录放置到 AstrBot 的 `data/plugins/` 下。
2. 重启 AstrBot 或在 WebUI 中重载插件。
3. 在插件配置中填写 `access_token`。

## 配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `access_token` | string | (空) | Dida365 Open API Access Token，必填 |
| `api_base_url` | string | `https://api.dida365.com/open/v1` | API 基础地址 |
| `default_project` | string | (空) | 创建任务时的兜底项目 |
| `timezone` | string | `Asia/Shanghai` | 插件时区 |
| `request_timeout_seconds` | int | `15` | API 请求超时秒数 |

### 获取 Access Token

1. 访问 [Dida365 Developer](https://developer.dida365.com)
2. 登录后创建应用，获取 Access Token
3. 将 Token 填入插件配置的 `access_token` 字段

## 使用方法

### 管理员指令

| 指令 | 说明 |
|------|------|
| `/dida_ping` | 检查插件加载状态和配置 |
| `/dida_probe` | 执行一次只读 API 探测 |
| `/dida_projects` | 列出所有项目（含收集箱） |
| `/dida_today` | 列出今日到期任务 |
| `/dida_unfinished` | 列出所有未完成任务 |

### LLM 自然语言交互

插件注册了以下 LLM Function Tool（需在支持 LLM 的会话中使用）：

| 工具名称 | 功能 |
|----------|------|
| `create_dida_task` | 创建滴答清单任务 |
| `list_dida_tasks` | 查询当前未完成的任务列表 |
| `update_dida_task` | 更新任务的任意字段（标题、备注、截止日期、优先级等） |

在对话中直接说"帮我创建一个任务"或"我的待办有哪些"即可触发。

## API 支持

| 端点 | 方法 | 说明 |
|------|------|------|
| `/open/v1/project` | GET | 获取所有项目 |
| `/open/v1/project/{id}/data` | GET | 获取项目内所有任务 |
| `/open/v1/project/inbox/data` | GET | 获取收集箱任务 |
| `/open/v1/task` | POST | 创建任务 |
| `/open/v1/task/{id}` | POST | 更新任务（需 POST 完整对象） |
| `/open/v1/project/{id}/task/{id}/complete` | POST | 完成任务 |
| `/open/v1/project/{id}/task/{id}` | DELETE | 删除任务 |

## 开发

### 环境要求

- Python >= 3.11
- [AstrBot](https://github.com/AstrBotDevs/AstrBot) >= 4.0.0

### 项目结构

```
astrbot_plugin_dida_improved/
├── main.py           # 插件入口：命令处理器和 LLM 工具注册
├── client.py         # Dida365 Open API HTTP 客户端
├── service.py        # 业务逻辑层（查询、格式化、错误处理）
├── models.py         # 数据模型
├── exceptions.py     # 自定义异常层次
├── time_utils.py     # 时区工具
├── _conf_schema.json # 插件配置 Schema（WebUI 自动渲染）
├── metadata.yaml     # 插件元数据
├── requirements.txt  # Python 依赖
├── README.md         # 本文件
├── LICENSE           # 许可证
└── .gitignore        # Git 忽略规则
```

## 许可证

本项目基于 2007 年 3 月 19 日发行的第三版 GNU Affero General Public 许可证发布，具体的详情另请参阅 [LICENCE](LICENCE)。
