# Astrbot 滴答清单插件改进版

滴答清单改进版 —— 在 AstrBot 中连接 Dida365/TickTick/滴答清单，支持完整的任务管理功能，包括收集箱 (Inbox) 任务。

事情的起因是我之前使用 [wuhuqif176](https://github.com/wuhuqif176)/[astrbot_plugin_dida_todo](https://github.com/wuhuqif176/astrbot_plugin_dida_todo) 的时候发现插件的使用无法访问滴答清单的内建清单 `Inbox` 的问题。于是我 Fork 了原仓库，改进了插件项目，改进后的代码也在刚才提到的文件夹里面。我向原作者提交了 Issue 并声称可以提供 PR，但是他还没有回复我。于是我打算独立开发 `astrbot_plugin_dida_improved`，支持更多 API 功能。

尽管我不得不承认这个项目赶工上马，大部分内容基本都还是 Vibe Coding 的产物 (Opencode + DeepSeek-v4-Flash)，而且是我第一次尝试通过 Vibe Coding 的方式开发一个项目，但我还是尽我所能对项目进行了测试，并保障代码的质量。

## 特性

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

## 安装

由于本项目目前还没有发布到 Astrbot 插件市场，目前您可以先通过手动安装的方式使用本项目，具体的操作流程如下：

1. 将插件目录放置到 AstrBot 的运行时目录下的 `data/plugins/` 下；
2. 在 WebUI 中重载插件，或者直接重启 AstrBot；
3. 在插件配置中至少应当填写您的 `access_token`。

> [!NOTE]
>
> 需要注意的是，由于安装方式的不同，运行时目录可能略有区别。具体的路径请参阅 [Astrbot 官方文档中有关部署方法的部分](https://docs.astrbot.app/deploy/astrbot/package.html)。

## 配置

插件提供了如下的配置选项，其中 `access_token` 是一个必填项，如不填写，则项目将无法使用。

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `access_token` | string | (空) | Dida365 Open API Access Token，必填 |
| `api_base_url` | string | `https://api.dida365.com/open/v1` | API 基础地址 |
| `default_project` | string | (空) | 创建任务时的兜底项目 |
| `timezone` | string | `Asia/Shanghai` | 插件时区 |
| `request_timeout_seconds` | int | `15` | API 请求超时秒数 |

### 获取 Access Token

这里只是简单提一下，本项目的文档当中有非常详细的创建 Access Token 的方法。

1. 访问 [Dida365 Developer](https://developer.dida365.com)；
2. 登录后创建应用，获取 Access Token；
3. 将 Token 填入插件配置的 `access_token` 字段。

## 使用方法

### 管理员指令

本项目提供了如下的两个测试用指令，以确保项目处于正常工作的状态。所有指令需以管理员身份执行。

| 指令 | 说明 |
|------|------|
| `/dida_ping` | 检查插件加载状态和配置 |
| `/dida_probe` | 执行一次只读 API 探测 |

### LLM 自然语言交互

插件注册了以下 LLM Function Tool (需在支持 LLM 的会话中使用)：

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

## 开发

### 环境要求

如果您想参与本项目的开发，项目的文档对此有十分详细的说明以供你查阅。请务必在开始开发整个项目之前仔细阅读文档里的内容。或者，如果你对项目的结构大致有一些了解，请通过文档索引查阅有关内容。

### 项目结构

下面展示的是本项目发布的代码的结构，也就是插件本身的部分。本项目还包含很多开发流程涉及的文件，请切换到 `dev` 分支进行查看。

```
astrbot_plugin_dida_improved/
├── logo.png            # 插件图标
├── main.py             # 插件入口：命令处理器和 LLM 工具注册
├── client.py           # Dida365 Open API HTTP 客户端
├── service/            # 业务逻辑层 (包目录)
│   ├── __init__.py     #   包入口，导出 DidaService
│   ├── service.py      #   DidaService 主类 (查询编排、公共 API)
│   ├── task_ops.py     #   任务操作 (CRUD、移动、筛选、已完成)
│   ├── formatting.py   #   输出格式化
│   ├── comments.py     #   任务评论
│   └── _helpers.py     #   内部辅助函数
├── models.py           # 数据模型
├── exceptions.py       # 自定义异常层次
├── time_utils.py       # 时区工具
├── _conf_schema.json   # 插件配置 Schema (WebUI 自动渲染)
├── metadata.yaml       # 插件元数据
├── requirements.txt    # Python 依赖
├── README.md           # 本文件
├── LICENSE             # 许可证
└── .gitignore          # Git 忽略规则
```

## 许可证

本项目基于 2007 年 3 月 19 日发行的第三版 GNU Affero General Public 许可证发布，具体的详情另请参阅 [LICENSE](LICENSE)。
