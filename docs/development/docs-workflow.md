# 文档工作流

## 工具栈

- **MkDocs** — 静态站点生成器
- **Material for MkDocs** — 主题
- **mkdocstrings** — 从 Python docstring 自动生成 API 参考
- **GitHub Actions** — 自动构建和部署

## 编写文档

所有文档源文件为 Markdown 格式，存放在 `docs/` 目录下。

### 文档编写规范

文档的编写应当遵循如下的规范：

1. 使用标准的 Markdown 语法，如非必要，不引入兼容性更低的专有语法，但 MKDocs 原生的以 `!!!` 用作行头的 Callot / Alert 应当被保留。
2. 对于每一个连贯的段落，不进行折行；当且仅当涉及将文本分割为 2 个独立的段落时，在文本之间插入 2 个折行。
3. 永远不使用 ASCII Art + 代码块的格式展示内容。
4. 中文和英文字符、中文和数字在正常表意的情况下，需留有 1 个空格的间距。
5. 中文文本中的括号请使用“空格 + 西文括号”，即：用 `（` 代替 `（`，用 `) ` 代替 `）`。如果括号与中文标点符号相邻，例如 `！(` 或者 `)。`，则括号与标点符号之间不应存在空格。
6. 对于无序列表和有序列表，如果一个列表行包含多个以句号“。”、感叹号“！”、问号“？”结尾的句子，则结尾的表点符号为句号“。”、感叹号“！”，或者问号“？”。如果一个列表行不包含一个完整的中文句子，使用分号“；”。


### 添加新页面

如果您需要为当前的文档添加一个新的页面，需要执行如下的 2 步操作：

1. 在 `docs/` 下创建对应的 `.md` 文件；
2. 在 `mkdocs.yml` 的 `nav` 中添加条目。

### API 参考 (自动生成) 

`docs/development/api-reference.md` 使用 `mkdocstrings` 插件从 Python 源文件的 Google 风格 docstring 自动生成。

示例语法：

```markdown
::: client.DidaClient
::: service.DidaService
::: models.DidaTask
```

当代码中的 docstring 更新后，重新构建文档即可反映变更。

## 本地开发

```bash
mkdocs serve  # 启动开发服务器 → http://localhost:8000
```

支持热重载，编辑文件后浏览器自动刷新。

## 构建

如果您想单次生成文档的构建，请使用如下的命令：

```bash
mkdocs build  # 构建到 site/ 目录
```

生成的构建位于 `site/` 目录下，该目录已被 `.gitignore` 排除，不会进入版本控制。正常情况下您不需要明确地浏览 `sites` 目录下的内容。

除此之外，如果你对文档的配置文件进行了修改，建议先执行如下的命令清理文档缓存，再重新生成文档。

```bash
mkdocs build --clean  # 或先 rm -rf site/ 再 build
```

## 部署到 GitHub Pages

### 手动部署

```bash
mkdocs gh-deploy  # 构建并推送到 gh-pages 分支
```

### CI 自动部署

`.github/workflows/deploy-docs.yml` 在以下条件满足时自动触发：

- 推送到 `dev` 分支（`main` 是自动同步的发布分支，不直接接收推送）
- 且变更涉及：`docs/**`、`mkdocs.yml`、`**/*.py`、`requirements.txt`

执行步骤：

1. 检出代码
2. 安装 Python 3.11
3. 安装 `mkdocs`、`mkdocs-material`、`mkdocstrings[python]`
4. 执行 `mkdocs build`
5. 执行 `mkdocs gh-deploy` 推送到 `gh-pages` 分支