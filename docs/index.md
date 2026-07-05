# 滴答清单改进版

滴答清单改进版 —— 在 AstrBot 中连接 Dida365/TickTick/滴答清单，支持完整的任务管理功能，包括收集箱（Inbox）任务。

事情的起因是我之前使用 [wuhuqif176](https://github.com/wuhuqif176)/[astrbot_plugin_dida_todo](https://github.com/wuhuqif176/astrbot_plugin_dida_todo) 的时候发现插件的使用无法访问滴答清单的内建清单 `Inbox` 的问题。于是我 Fork 了原仓库，改进了插件项目，改进后的代码也在刚才提到的文件夹里面。我向原作者提交了 Issue 并声称可以提供 PR，但是他还没有回复我。于是我打算独立开发 `astrbot_plugin_dida_improved`，支持更多 API 功能。

尽管我不得不承认这个项目赶工上马，大部分内容基本都还是 Vibe Coding 的产物 (Opencode + DeepSeek-v4-Flash)，而且是我第一次尝试通过 Vibe Coding 的方式开发一个项目，但我还是尽我所能对项目进行了测试，并保障代码的质量。

## 特性

本项目目前实现了如下的功能：

- 查询所有未完成任务 (含收集箱)；
- 查询今日到期任务；
- 创建、完成、更新、移动、删除任务；
- 管理员指令 / 自然语言 LLM 两种交互方式；
- 正确处理收集箱 (Inbox) 任务 (原插件遗漏的功能)。

## 安装

由于本项目目前还没有发布到 Astrbot 插件市场，目前您可以先通过手动安装的方式使用本项目，具体的操作流程如下：

1. 将插件目录放置到 AstrBot 的运行时目录下的 `data/plugins/` 下；
2. 在 WebUI 中重载插件，或者直接重启 AstrBot；
3. 在插件配置中至少应当填写您的 `access_token`。

!!! note "关于 Astrbot 的运行时目录所在的位置"
    需要注意的是，由于安装方式的不同，运行时目录可能略有区别。具体的路径请参阅 [Astrbot 官方文档中有关部署方法的部分](https://docs.astrbot.app/deploy/astrbot/package.html)。