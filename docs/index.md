# 滴答清单改进版

滴答清单改进版 —— 在 AstrBot 中连接 Dida365/TickTick/滴答清单，支持完整的任务管理功能，包括收集箱 (Inbox) 任务。[点击此处链接访问项目文档页面](https://githubonline1396529.github.io/astrbot_plugin_dida_improved/)。

事情的起因是我之前使用 [wuhuqif176](https://github.com/wuhuqif176)/[astrbot_plugin_dida_todo](https://github.com/wuhuqif176/astrbot_plugin_dida_todo) 的时候发现插件的使用无法访问滴答清单的内建清单 `Inbox` 的问题。于是我 Fork 了原仓库，改进了插件项目，改进后的代码也在刚才提到的文件夹里面。我向原作者提交了 Issue 并声称可以提供 PR，但是他还没有回复我。于是我打算独立开发 `astrbot_plugin_dida_improved`，支持更多 API 功能。

最初写这个插件的时候，我的预期原本只是两三个几百行代码的小脚本，但是后来发现由于插件涉及到与 Dida 365 的 API 进行交互，实现完整功能所需的实际代码体量大了许多。虽然这是我第一次尝试通过 Vibe Coding 的方式开发一个项目，但我还是尽我所能对项目进行了测试，并保障代码的质量。希望大家用得喜欢。

## 特性

### 基础功能

本项目目前实现了如下的功能，均通过 LLM 工具调用，核心是 Astrbot 的自然语言处理能力。你只需要通过自然语言向 Astrbot 下达命令，就能让它完全接管你的滴答清单，就像操作本地文件一样容易。

- 查询所有未完成任务 (含收集箱)；
- 查询今日到期任务；
- 创建、完成、更新、移动、删除任务；
- 管理员指令 / 自然语言 LLM 两种交互方式；
- 正确处理收集箱 (Inbox) 任务 (原插件遗漏的功能)。

### API 支持

本项目支持如下的 API，关于 API 的详情请查阅 [Dida365 Open API 手册](https://developer.dida365.com/docs#/openapi)。

| 端点 | 方法 | 说明 |
|------|------|------|
| `/open/v1/project` | GET | 获取所有项目 |
| `/open/v1/project/{id}/data` | GET | 获取项目内所有任务 |
| `/open/v1/project/inbox/data` | GET | 获取收集箱任务 |
| `/open/v1/task` | POST | 创建任务 |
| `/open/v1/task/{id}` | POST | 更新任务 (需 POST 完整对象) |
| `/open/v1/project/{id}/task/{id}` | GET | 获取单个任务 |
| `/open/v1/project/{id}/task/{id}/complete` | POST | 完成任务 |
| `/open/v1/project/{id}/task/{id}` | DELETE | 删除任务 |
| `/open/v1/task/move` | POST | 移动任务 |
| `/open/v1/task/filter` | POST | 高级筛选任务 |
| `/open/v1/task/completed` | POST | 列出已完成任务 |
| `/open/v1/project/{id}/task/{id}/comments` | GET | 获取任务评论 |
| `/open/v1/project/{id}/task/{id}/comment` | POST | 添加评论 |
| `/open/v1/project/{id}/task/{id}/comment/{cid}` | DELETE | 删除评论 |
