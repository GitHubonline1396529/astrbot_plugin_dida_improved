# 文档工作流

## 工具栈

- **MkDocs** — 静态站点生成器；
- **Material for MkDocs** — 主题；
- **mkdocstrings** — 从 Python docstring 自动生成 API 参考；
- **GitHub Actions** — 自动构建和部署。

## 编写文档

所有文档源文件为 Markdown 格式，存放在 `docs/` 目录下。

### 文档编写规范

文档的编写应当遵循如下的规范：

1. 如非必要，不使用分隔符 `---`，这将降低最终生成的文档的版式连贯性。
2. 使用标准的 Markdown 语法，如非必要，不引入兼容性更低的专有语法，但 MkDocs 原生的以 `!!!` 用作行头的 Callout / Alert 应当被保留。
3. 对于每一个连贯的段落，不进行折行；当且仅当涉及将文本分割为 2 个独立的段落时，在文本之间插入 2 个折行。
4. 永远不使用 ASCII Art + 代码块的格式展示内容。
5. 中文和英文字符、中文和数字在正常表意的情况下，需留有 1 个空格的间距。
6. 中文文本中的括号请使用"空格 + 西文括号"，即：用 `(` 代替 `（`，用 `)` 代替 `）`。如果括号与中文标点符号相邻，例如 `！(` 或者 `)。`，则括号与标点符号之间不应存在空格。
7. 对于无序列表和有序列表，如果一个列表行包含多个以句号"。"、感叹号"！"、问号"？"结尾的句子，则结尾的表点符号为句号"。"、感叹号"！"，或者问号"？"。如果一个列表行不包含一个完整的中文句子，使用分号"；"。
8. 如果涉及多级列表，则必须以四个空格为缩进，否则 MkDocs 无法正确渲染。


### 标题与锚点

标题的锚点由 `pymdownx.slugs.slugify` 生成，该覆盖项写在本仓库 `mkdocs.yml` 的 `toc` 扩展中，规则是：**保留中文与字母数字，丢弃标点，空格转为连字符，统一小写**。因此 `## 预览分支` 的锚点是 `#预览分支`，`## LLM 工具注册与参数类型解析` 的锚点是 `#llm-工具注册与参数类型解析`。

这与 GitHub 网页端浏览同一份 Markdown 时的锚点一致，便于两种渲染方式下的链接互相通用。

!!! warning "不要移除 `toc` 的 `slugify` 覆盖"
    Python-Markdown 默认的 slugify 会**整体剥离非 ASCII 字符**，使纯中文标题退化为 `_1`、`_2` 这类由顺序决定的锚点 (例如若不覆盖，`## 预览分支` 的锚点会是 `#_6`)。这种锚点不可引用：在页内任意位置插入一个新标题都会让它整体漂移。

跨页面引用标题时：

1. 直接使用标题文本对应的锚点，中文可原样写在链接里，例如 `[发布流程](release-workflow.md#发布流程)`；
2. 当标题文本**可能变动**时 (如带编号的 `### 6. …`、同页出现重复标题)，改用显式的 ASCII 锚点 `## 标题 { #some-id }`，并在引用方使用 `#some-id`；
3. 不要依赖 `_1` 这类由重复标题自动派生的后缀锚点，它同样与顺序绑定。例如 `release-workflow.md` 的页面标题是 `# 发布流程`，页内又有一个同名小节 `## 发布流程`，后者的锚点便是 `#发布流程_1`。

!!! note "关于 `{ #... }` 的兼容性"
    `attr_list` 的 `{ #some-id }` 是 Python-Markdown 的扩展语法，GitHub 网页端不解析它，会将其作为标题文字原样显示。因此仅在中文锚点确实不稳定时才使用，并同时确认该引用在 GitHub 上失效是可接受的。

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
mkdocs serve  # 启动开发服务器
```

服务启动后将会运行在本机的 8000 端口，通过 `http://127.0.0.1:8000/astrbot_plugin_dida_improved/` 可用访问。其中，`astrbot_plugin_dida_improved` 请替换为您本地项目文件夹的实际名称。或者，在服务启动后的终端窗口中也会弹出正确的文档预览地址。

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

- 推送到 `dev` 分支 (`main` 是自动同步的发布分支，不直接接收推送)；
- 且变更涉及：`docs/**`、`mkdocs.yml`、`**/*.py`、`requirements.txt`。

执行步骤：

1. 检出代码
2. 安装 Python 3.11；
3. 安装 `mkdocs`、`mkdocs-material`、`mkdocstrings[python]`；
4. 执行 `mkdocs build`；
5. 执行 `mkdocs gh-deploy` 推送到 `gh-pages` 分支。

## 变更日志同步到 main

`docs/changelog.md` 是变更日志的唯一来源。在发布 (推送 `v*` 标签) 时，`sync-main-on-tag.yml` 工作流会依据 `release-manifest.json` 的 `copies` 映射，将其复制为仓库根目录下的 `CHANGELOG.md` 并同步到 `main` 分支，以配合 AstrBot 插件市场展示更新历史。

因此，`CHANGELOG.md` 不需要 (也不应) 在 `dev` 分支的根目录中手动维护——只需在发布前更新 `docs/changelog.md`，根目录版本会在发布时自动生成。详见[发布流程](release-workflow.md)。
