# LLM 工具

插件注册了 LLM Function Tool，可在支持 LLM 的会话中通过自然语言调用。

## 工具列表

| 工具名称 | 功能 | 触发示例 |
|----------|------|----------|
| `list_dida_projects` | 列出所有滴答清单项目（含收集箱） | "我的项目有哪些" |
| `list_dida_tasks` | 查询任务列表，支持筛选 | "今天有什么任务"、"我的待办有哪些" |
| `update_dida_task` | 更新任务的任意字段（标题、备注、截止日期、优先级等） | "把任务备注改成已完成"、"把优先级改为高" |

## 使用示例

### 列出项目

> 我的滴答清单里有哪些项目？
> 帮我看看项目列表

LLM 会自动调用 `list_dida_projects` 工具返回项目列表。

### 查询今日任务

> 今天有什么任务
> 今天到期的待办有哪些

LLM 会自动调用 `list_dida_tasks(filter="today")` 返回今日到期任务。

### 查询未完成任务

> 我的待办有哪些
> 还有哪些事情没有做

LLM 会自动调用 `list_dida_tasks(filter="unfinished")` 返回所有未完成任务列表。

### 更新任务

> 把任务 6a2a9b91e4b039e491b1de54 的备注改为"已完成"
> 将任务标题改为"新标题"，优先级调到高

LLM 会自动调用 `update_dida_task` 工具。传入参数：

- `task_id` — 任务 ID（必填）
- `updates_json` — JSON 对象字符串（必填），键使用 Dida365 API 的 camelCase 字段名

**示例：**

```json
{"title": "新标题", "content": "新备注内容", "priority": 5}
```

支持更新任意 API 字段：`title`、`content`、`dueDate`、`priority`（0/1/3/5）、`tags`、`status` 等。
