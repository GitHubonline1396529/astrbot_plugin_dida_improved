# LLM 工具

插件注册了 LLM Function Tool，可在支持 LLM 的会话中通过自然语言调用。

## 工具列表

| 工具名称 | 功能 | 触发示例 |
|----------|------|----------|
| `list_dida_projects` | 列出所有滴答清单项目（含收集箱） | "我的项目有哪些" |
| `list_dida_tasks` | 查询任务列表，支持筛选 | "今天有什么任务"、"我的待办有哪些" |
| `create_dida_task` | 创建新任务 | "帮我创建一个任务" |
| `complete_dida_task` | 完成任务 | "把任务完成" |
| `update_dida_task` | 更新任务的任意字段（标题、备注、截止日期、优先级等） | "把任务备注改成已完成"、"把优先级改为高" |
| `delete_dida_task` | 删除任务 | "把这个任务删掉" |

## 使用示例

### 列出项目

> 我的滴答清单里有哪些项目？
> 
> 帮我看看项目列表

LLM 会自动调用 `list_dida_projects` 工具返回项目列表。

### 查询今日任务

> 今天有什么任务
> 
> 今天到期的待办有哪些

LLM 会自动调用 `list_dida_tasks(filter="today")` 返回今日到期任务。

### 查询未完成任务

> 我的待办有哪些
> 
> 还有哪些事情没有做

LLM 会自动调用 `list_dida_tasks(filter="unfinished")` 返回所有未完成任务列表。

### 创建任务

> 帮我创建一个任务
> 
> 创建一个叫"买牛奶"的任务，放到工作项目里

LLM 会自动调用 `create_dida_task` 工具。传入参数：

- `title` — 任务标题（必填）
- `project_id` — 目标项目 ID（可选，默认使用配置的兜底项目或收集箱）
- `content` — 任务备注（可选）
- `priority` — 优先级（可选）：`"none"`、`"low"`、`"medium"`、`"high"` 或 `0/1/3/5`
- `tags` — 逗号分隔的标签（可选），如 `"work,urgent"`
- `due_date` — ISO 格式的截止日期（可选），如 `"2026-07-10T18:00:00+08:00"`

### 完成任务

> 把任务 6a2a9b91e4b039e491b1de54 完成
> 
> 标记任务为已完成

LLM 会自动调用 `complete_dida_task` 工具。传入参数：

- `task_id` — 任务 ID（必填）

### 更新任务

> 把任务 6a2a9b91e4b039e491b1de54 的备注改为"已完成"
> 
> 将任务标题改为"新标题"，优先级调到高

LLM 会自动调用 `update_dida_task` 工具。传入参数：

- `task_id` — 任务 ID（必填）
- `updates_json` — JSON 对象字符串（必填），键使用 Dida365 API 的 camelCase 字段名

**示例：**

```json
{"title": "新标题", "content": "新备注内容", "priority": 5}
```

支持更新任意 API 字段：`title`、`content`、`dueDate`、`priority`（0/1/3/5）、`tags`、`status` 等。

### 删除任务

> 把任务 6a2a9b91e4b039e491b1de54 删掉
> 
> 删除这个任务

LLM 会自动调用 `delete_dida_task` 工具。传入参数：

- `task_id` — 任务 ID（必填）
