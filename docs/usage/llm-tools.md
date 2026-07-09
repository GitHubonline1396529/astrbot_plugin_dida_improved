# LLM 工具

插件注册了 LLM Function Tool，可在支持 LLM 的会话中通过自然语言调用。

## 工具列表

| 工具名称 | 功能 | 触发示例 |
|----------|------|----------|
| `list_dida_projects` | 列出所有滴答清单项目 (含收集箱)  | "我的项目有哪些" |
| `list_dida_tasks` | 查询任务列表，支持筛选 | "今天有什么任务"、"我的待办有哪些" |
| `create_dida_task` | 创建新任务 | "帮我创建一个任务" |
| `complete_dida_task` | 完成任务 | "把任务完成" |
| `update_dida_task` | 更新任务的任意字段 (标题、备注、截止日期、优先级等)  | "把任务备注改成已完成"、"把优先级改为高" |
| `delete_dida_task` | 删除任务 | "把这个任务删掉" |
| `move_dida_task` | 移动任务到其他项目 | "把这个任务移到工作项目" |
| `get_dida_task_detail` | 获取单个任务的详细信息 | "查看任务详情" |
| `list_completed_dida_tasks` | 查询已完成任务 | "已完成的任务有哪些" |
| `get_dida_task_comments` | 查看任务评论 | "看看这个任务有什么评论" |
| `add_dida_task_comment` | 添加评论 | "给这个任务加一条评论" |
| `delete_dida_task_comment` | 删除评论 | "删除这条评论" |

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

- `title` — 任务标题 (必填)；
- `project_id` — 目标项目 ID (可选，默认使用配置的兜底项目或收集箱)；
- `content` — 任务备注 (可选)；
- `priority` — 优先级 (可选)：`"none"`、`"low"`、`"medium"`、`"high"` 或 `0/1/3/5`；
- `tags` — 逗号分隔的标签 (可选)，如 `"work,urgent"`；
- `due_date` — ISO 格式的截止日期 (可选)，如 `"2026-07-10T18:00:00+08:00"`。

### 完成任务

> 把任务 6a2a9b91e4b039e491b1de54 完成
>
> 标记任务为已完成

LLM 会自动调用 `complete_dida_task` 工具。传入参数：

- `task_id` — 任务 ID (必填)；

### 更新任务

> 把任务 6a2a9b91e4b039e491b1de54 的备注改为"已完成"
>
> 将任务标题改为"新标题"，优先级调到高

LLM 会自动调用 `update_dida_task` 工具。传入参数：

- `task_id` — 任务 ID (必填)；
- `updates_json` — JSON 对象字符串 (必填)，键使用 Dida365 API 的 camelCase 字段名；

**示例：**

```json
{"title": "新标题", "content": "新备注内容", "priority": 5}
```

支持更新任意 API 字段：`title`、`content`、`dueDate`、`priority` (0/1/3/5)、`tags`、`status` 等。

### 删除任务

> 把任务 6a2a9b91e4b039e491b1de54 删掉
>
> 删除这个任务

LLM 会自动调用 `delete_dida_task` 工具。传入参数：

- `task_id` — 任务 ID (必填)。

### 移动任务

> 把任务 6a2a9b91e4b039e491b1de54 从项目 A 移到项目 B

LLM 会自动调用 `move_dida_task` 工具。传入参数：

- `task_id` — 任务 ID (必填)；
- `from_project_id` — 源项目 ID (必填)；
- `to_project_id` — 目标项目 ID (必填)。

### 查询已完成任务

> 近期完成了哪些任务
>
> 帮我看看上周完成了什么

LLM 会自动调用 `list_completed_dida_tasks` 工具。传入参数 (可选)：

- `project_ids` — 逗号分隔的项目 ID；
- `start_date` — ISO 格式的开始时间；
- `end_date` — ISO 格式的结束时间。

### 查看任务评论

> 看看任务 6a2a9b91e4b039e491b1de54 有什么评论

LLM 会自动调用 `get_dida_task_comments` 工具。传入参数：

- `project_id` — 项目 ID (必填)；
- `task_id` — 任务 ID (必填)。

### 添加评论

> 给任务 6a2a9b91e4b039e491b1de54 加一条评论："已完成"

LLM 会自动调用 `add_dida_task_comment` 工具。传入参数：

- `project_id` — 项目 ID (必填)；
- `task_id` — 任务 ID (必填)；
- `title` — 评论内容 (必填)。

### 删除评论

> 把任务 6a2a9b91e4b039e491b1de54 的评论 comment-1 删掉

LLM 会自动调用 `delete_dida_task_comment` 工具。传入参数：

- `project_id` — 项目 ID (必填)；
- `task_id` — 任务 ID (必填)；
- `comment_id` — 评论 ID (必填)。
