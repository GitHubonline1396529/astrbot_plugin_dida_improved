# 滴答清单改进版

滴答清单改进版 —— 在 AstrBot 中连接 Dida365/TickTick/滴答清单，支持完整的任务管理功能，包括收集箱（Inbox）任务。

事情的起因是我之前使用 [wuhuqif176](https://github.com/wuhuqif176)/[astrbot_plugin_dida_todo](https://github.com/wuhuqif176/astrbot_plugin_dida_todo) 的时候发现插件的使用无法访问滴答清单的内建清单 `Inbox` 的问题。于是我 Fork 了原仓库，改进了插件项目，改进后的代码也在刚才提到的文件夹里面。我向原作者提交了 Issue 并声称可以提供 PR，但是他还没有回复我。于是我打算独立开发 `astrbot_plugin_dida_improved`，支持更多 API 功能。

## 特性

- 查询所有未完成任务（含收集箱）
- 查询今日到期任务
- 创建、完成、更新、移动、删除任务
- LLM 自然语言交互，通过 Function Tool 完成所有任务操作
- 正确处理收集箱（Inbox）任务

## 快速开始

遵循如下的步骤以手动安装本插件：

1. 将插件目录放置到 AstrBot 的 `data/plugins/` 下。
2. 重启 AstrBot 或在 WebUI 中重载插件。
3. 在插件配置中填写 `access_token`。