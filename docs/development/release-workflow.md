# 发布流程

## 背景

AstrBot 内置的插件下载机制直接从 GitHub 仓库的默认分支下载源码 (ZIP 归档)，而不使用 GitHub Releases 的发布包。这意味着默认分支上的 **所有文件** 都会被包含在下载包中，无论它们是否对插件运行有用。

与此同时，本项目中存在大量仅在开发阶段需要的文件，包括但不限于：

- 文档源码 (`docs/` 目录、`mkdocs.yml`)；
- 测试套件 (`tests/` 目录)；
- 开发依赖声明 (`requirements-dev.txt`、`pyproject.toml`)；
- CI/CD 工作流 (`.github/` 目录)；
- 仅用于 `pytest` 包导入的 `__init__.py`；
- AI 辅助开发参考 (`AGENTS.md`)。

这些文件不应出现在 `main` 分支的下载包中 (因为它们对插件运行无意义)，但应当完整出现在 `dev` 分支的下载包中——协作者需要它们来完成开发工作流。

## 分支策略

为解决上述问题，我们采用三分支策略管理代码：

远程 GitHub 仓库：

- `main`：发布分支 (仅包含 13 个运行时必需文件，外加一份由 `docs/changelog.md` 自动生成的 `CHANGELOG.md`)；
- `dev`：开发分支 (包含全部源文件，包括测试、文档等)；
- `preview`：预览分支 (发布文件清单与 `main` 完全相同，但由每次 `dev` 推送自动重建，详见[预览分支](#预览分支) 章节) 。

本地开发环境下，`dev` 为唯一本地分支，包括：

- `feat/xxx` ——特性分支；
- `fix/xxx` ——修复分支；
- ……

日常开发在 `dev` 上进行；`main` 与 `preview` 都不创建于本地，仅由 GitHub Actions 维护。这里的命名策略与直觉相反：

- **`main`** 实际上是发布分支，只放插件运行所必需的最小文件集合，外加一份由 `docs/changelog.md` 自动生成的 `CHANGELOG.md` (供 AstrBot 插件市场展示更新历史)。
- **`dev`** 实际上是开发的主分支，所有工作都在此进行。

之所以如此命名，是因为 AstrBot 的插件下载机制读取的是 GitHub 仓库的默认分支。将 `main` 设为默认分支，并让它只包含发布文件，可以确保用户下载的永远是干净的插件包。

`preview` 分支解决的是另一个问题：开发新功能时，需要在一个干净的插件包上测试。若直接从 `dev` 分支安装，AstrBot 会把测试套件、文档源码、CI 配置等一并下载到 `data/plugins/` 目录中，既冗余又容易干扰测试。`preview` 提供了「当前的开发状态，但只含运行时文件」的包。

### 发布文件清单

发布文件清单由 `release-manifest.json` 定义，包含两个部分：

- `files` — 直接从 `dev` 分支原样暂存的运行时文件/目录；
- `copies` — 需要复制或重命名的文件 (源路径 → 目标路径)，例如将 `docs/changelog.md` 复制为根目录下的 `CHANGELOG.md`。

`files` 当前清单包含以下文件/目录：

| 文件/目录 | 用途 |
|-----------|------|
| `logo.png` | 插件入口图标 |
| `main.py` | 插件入口：命令处理器和 LLM 工具注册 |
| `client.py` | Dida365 Open API HTTP 客户端 |
| `service/` | 业务逻辑层 (包目录)  |
| `models.py` | 数据模型 |
| `exceptions.py` | 自定义异常层次 |
| `time_utils.py` | 时区工具 |
| `_conf_schema.json` | 插件配置 Schema (WebUI 自动渲染) |
| `metadata.yaml` | 插件元数据 |
| `requirements.txt` | 运行时依赖 |
| `README.md` | 使用说明 |
| `LICENSE` | AGPL v3 许可证 |
| `.gitignore` | Git 忽略规则 (保持模板原样)  |

`copies` 当前清单包含以下映射：

| 源路径 | 目标路径 | 用途 |
|--------|----------|------|
| `docs/changelog.md` | `CHANGELOG.md` | 变更日志，供 AstrBot 插件市场展示更新历史 |

!!! note "变更发布文件清单"
    如果需要新增/移除发布文件，修改 `release-manifest.json` 即可，无需编辑 CI 工作流。

## 技术实现

### 第一层防护：`.gitattributes`

`dev` 分支使用 `.gitattributes` 排除两项内容：

```gitattributes
.gitattributes    export-ignore
.env              export-ignore
```

- **`.gitattributes` 自身**：标准做法，不在下载包中携带导出规则文件。
- **`.env`**：包含 Dida365 Access Token (仅集成测试使用)。此文件在 `.gitignore` 中已有排除，`export-ignore` 作为双重保险。

其余所有文件 (文档源码 `docs/`、测试套件 `tests/`、CI 配置 `.github/` 等) 均**保留在下载包中**，以确保协作者下载 `dev` 分支后可以立即开展完整的开发工作流。

之所以这样做，是因为 `dev` 与 `main` 的设计目标不同：`main` 面向最终用户 (只需最小运行文件)，`dev` 面向协作者 (需要完整的开发环境)。

### 第二层防护：GitHub Actions 自动同步

真正的发布流程由 `sync-main-on-tag.yml` 工作流自动完成。该工作流在推送到 `dev` 分支的 `v*` 标签时触发。

触发后的执行逻辑：

1. 检出标签所指向的 `dev` 分支提交；
2. `git checkout --orphan release-temp` — 创建一个没有历史的新分支；
3. 读取 `release-manifest.json` 的 `files` 列表，`git add` 仅暂存运行时必需的文件；
4. 读取 `release-manifest.json` 的 `copies` 列表，将源文件复制到目标路径 (如 `docs/changelog.md` → `CHANGELOG.md`) 并暂存；
5. `git commit -m "release: v*"` — 提交只包含发布文件的快照；
6. `git branch -f main release-temp` — 用这个快照替换 `main` 分支；
7. `git push origin main --force` — 强制推送到远程。

由于使用了 `--orphan`，`main` 分支的每次发布都是一个独立的根提交，没有与 `dev` 共享的历史。这保证了 `main` 的纯净。

`preview` 分支复用完全相同的清单与快照机制，但由独立工作流 `sync-preview-on-dev-push.yml` 在 `dev` 推送时重建，详见下一章节。

## 预览分支

### 目的

开发新功能时，需要一个**干净**的插件包来测试：即只包含运行必需文件，而不含测试套件、文档源码、CI 配置等开发期文件。

若直接从 `dev` 分支安装，AstrBot 会把这些开发期文件一并下载到 `data/plugins/` 目录下，既冗余又容易干扰测试 (例如 `pytest` 配置、CI 工作流会随插件一起出现)。`preview` 分支的目标就是提供「当前开发状态 + 发布文件清单」的组合。

### 触发与更新逻辑

`sync-preview-on-dev-push.yml` 工作流在每次向 `dev` 分支推送时触发：

1. 检出 `dev` 分支的最新提交；
2. 与 `sync-main-on-tag.yml` 相同，按 `release-manifest.json` 构建只含发布文件的快照；
3. 计算快照的 tree 哈希，与远程 `preview` 分支的 tree 哈希比较；
4. 若两者**相同** (例如本次提交只改动了 `tests/`、`docs/`、`.github/` 等非发布文件)，则不产生任何推送，工作流以成功状态退出；
5. 若不同，则提交 `preview: <短哈希>` 并强制推送到远程 `preview` 分支。

因此 `preview` 只会在发布文件集合真正变化时才更新，测试代码或文档的提交不会制造无意义的快照。

### 与 `main` 分支的差异

| 维度 | `main` | `preview` |
|------|--------|-----------|
| 触发条件 | 推送 `v*` 标签 | 每次推送到 `dev` 分支 |
| 快照来源 | 标签所指向的 `dev` 提交 | `dev` 分支最新提交 |
| 提交信息 | `release: v*` | `preview: <短哈希>` |
| 更新频率 | 每次发布一次 | 每次发布文件变更一次 |
| 稳定性 | 稳定，可视为正式版本 | 易变，仅供测试 |

两者的文件清单同由 `release-manifest.json` 定义，因此**修改清单会同时影响二者**：改动在下次 `dev` 推送后反映到 `preview`，在下次推送标签后反映到 `main`。

### 获取预览包

**方式一：通过 AstrBot 插件市场界面安装 (推荐) **

在 AstrBot WebUI 的插件安装界面输入以下地址：

```
https://github.com/GitHubonline1396529/astrbot_plugin_dida_improved/tree/preview
```

AstrBot 会识别 `/tree/<分支名>` 形式并下载该分支的 ZIP 归档。安装后再次点击「更新」，AstrBot 会使用安装时记录的仓库地址与分支重新下载，从而拉取最新的预览快照。

**方式二：手动下载 ZIP**

```
https://github.com/GitHubonline1396529/astrbot_plugin_dida_improved/archive/refs/heads/preview.zip
```

解压后的目录名为 `astrbot_plugin_dida_improved-preview`，需要重命名为 `astrbot_plugin_dida_improved`，再放入 AstrBot 的 `data/plugins/` 目录。

**方式三：`git clone`**

```bash
git clone -b preview --depth 1 https://github.com/GitHubonline1396529/astrbot_plugin_dida_improved.git
```

!!! warning "`preview` 分支是易变的"
    `preview` 仅用于测试开发中的代码，其历史随时会被强制推送覆盖，因此不应在它之上进行开发，也不应将它作为拉取请求的目标分支。需要修改代码时，请切回 `dev` 分支。

## 发布流程

**1. 进入 dev 分支**：确保当前工作目录在 `dev` 分支上，所有后续操作都基于此分支进行。

```bash
git checkout dev
```

**2. 更新 `metadata.yaml` 中的版本号**：你需要手动编辑 `version` 字段，例如从 `v0.1.0` 改为 `v0.2.0`。

**3. 提交版本变更**：将版本号的修改提交到 `dev` 分支。

```bash
git add metadata.yaml
git commit -m "chore: bump version to v0.2.0"
```

**4. 打标签**：标签名**必须**以 `v` 开头，这是 GitHub Actions 工作流的触发条件。

```bash
git tag v0.2.0
```

**5. 推送标签 (触发 GitHub Actions 自动同步到 main) **

```bash
git push origin v0.2.0
```

推送标签后，GitHub Actions 工作流 `sync-main-on-tag.yml` 会自动执行，将发布文件同步到 `main` 分支。

**可选：同时推送 dev 分支的最新提交**

```bash
git push origin dev
```

如果希望远程 `dev` 分支也保持最新，可以一并推送。

推送标签后，可以在 GitHub 仓库的 Actions 页面查看 `sync release to main` 工作流的执行状态。执行成功后，`main` 分支将自动更新为只包含 13 个发布文件 (外加生成的 `CHANGELOG.md`) 的新快照。

## 常见问题

### 如果不小心对 `main` 执行了 `git push`？

由于没有分支保护限制，推送会成功，但 `main` 分支不应被手动修改。如果误推了，可以在远程删除 `main` 分支后重新推送标签触发 CI 重建：

```bash
git push origin --delete main
```

然后重新执行发布流程中的标签推送步骤。

### 如果本地不小心创建了 `main` 分支？

没有影响。`main` 仅存在于远程，且本地的 `main` 分支内容与远程不同。只需删除本地分支：`git branch -D main`。

### 为什么不在本地创建 `main` 分支？

避免误推。本地只有 `dev`，开发者没有机会执行 `git push origin main`。`main` 的维护完全交由 GitHub Actions 处理。

### 如果不小心对 `preview` 执行了 `git push`？

无需处理。`preview` 分支的更新始终使用强制推送，下一次向 `dev` 推送时，工作流会将它重建为正确内容。若要立即恢复，可在 GitHub 仓库的 Actions 页面找到 `sync preview branch` 的历史运行记录，使用 **Re-run all jobs** 重新执行。

### 为什么不在本地创建 `preview` 分支？

与 `main` 同理：`preview` 是构建产物，只存在于远程。在本地创建它既无必要，也容易造成误推与内容不一致。

### `preview` 分支何时首次出现？

首次创建需要先有一次 `dev` 分支推送 (即工作流文件提交并推送之后)。由于本仓库的默认分支为 `main`，而 `main` 不包含 `.github/` 目录，工作流在首次运行前不会出现在 Actions 页面的手动触发列表中；因此最初的创建依赖于一次 `dev` 推送，之后即可在 Actions 页面手动重新运行。
