# 发布流程

## 背景

AstrBot 内置的插件下载机制直接从 GitHub 仓库的默认分支下载源码 (ZIP 归档)，而不使用 GitHub Releases 的发布包。这意味着默认分支上的 **所有文件** 都会被包含在下载包中，无论它们是否对插件运行有用。

与此同时，本项目中存在大量仅在开发阶段需要的文件，包括但不限于：

- 文档源码（`docs/` 目录、`mkdocs.yml`）
- 测试套件（`tests/` 目录）
- 开发依赖声明（`requirements-dev.txt`、`pyproject.toml`）
- CI/CD 工作流（`.github/` 目录）
- 仅用于 `pytest` 包导入的 `__init__.py`
- AI 辅助开发参考（`AGENTS.md`）

这些文件不应出现在 `main` 分支的下载包中（因为它们对插件运行无意义），但应当完整出现在 `dev` 分支的下载包中——协作者需要它们来完成开发工作流。

## 分支策略

为解决上述问题，我们采用双分支策略管理代码：

远程 GitHub 仓库：

- `main`：发布分支（仅包含 12 个运行时必需文件）；
- `dev`：开发分支（包含全部源文件，包括测试、文档等）。

本地开发环境下，`dev` 为唯一本地分支，包括：

- `feat/xxx` ——特性分支；
- `fix/xxx` ——修复分支；
- ……

日常开发在 `dev` 上进行；`main` 分支不创建于本地，仅由 GitHub Actions 在发布时自动同步。这里的命名策略与直觉相反：

- **`main`** 实际上是发布分支，只放插件运行所必需的最小文件集合。
- **`dev`** 实际上是开发的主分支，所有工作都在此进行。

之所以如此命名，是因为 AstrBot 的插件下载机制读取的是 GitHub 仓库的默认分支。将 `main` 设为默认分支，并让它只包含发布文件，可以确保用户下载的永远是干净的插件包。

### 发布文件清单

以下 12 个文件是插件运行的必要条件，也是 `main` 分支的全部内容：

| 文件 | 用途 |
|------|------|
| `main.py` | 插件入口：命令处理器和 LLM 工具注册 |
| `client.py` | Dida365 Open API HTTP 客户端 |
| `service.py` | 业务逻辑层 |
| `models.py` | 数据模型 |
| `exceptions.py` | 自定义异常层次 |
| `time_utils.py` | 时区工具 |
| `_conf_schema.json` | 插件配置 Schema（WebUI 自动渲染） |
| `metadata.yaml` | 插件元数据 |
| `requirements.txt` | 运行时依赖 |
| `README.md` | 使用说明 |
| `LICENSE` | AGPL v3 许可证 |
| `.gitignore` | Git 忽略规则（保持模板原样） |

## 技术实现

### 第一层防护：`.gitattributes`

`dev` 分支使用 `.gitattributes` 排除两项内容：

```gitattributes
.gitattributes    export-ignore
.env              export-ignore
```

- **`.gitattributes` 自身**：标准做法，不在下载包中携带导出规则文件。
- **`.env`**：包含 Dida365 Access Token 等凭据。此文件在 `.gitignore` 中已有排除，`export-ignore` 作为双重保险；仅用于集成测试，日常开发和用户运行都不需要。

其余所有文件（文档源码 `docs/`、测试套件 `tests/`、CI 配置 `.github/` 等）均**保留在下载包中**，以确保协作者下载 `dev` 分支后可以立即开展完整的开发工作流。

之所以这样做，是因为 `dev` 与 `main` 的设计目标不同：`main` 面向最终用户（只需最小运行文件），`dev` 面向协作者（需要完整的开发环境）。

### 第二层防护：GitHub Actions 自动同步

真正的发布流程由 `sync-main-on-tag.yml` 工作流自动完成。该工作流在推送到 `dev` 分支的 `v*` 标签时触发。

触发后的执行逻辑：

1. 检出标签所指向的 `dev` 分支提交
2. `git checkout --orphan release-temp` — 创建一个没有历史的新分支
3. `git add` 上述 12 个发布文件 — 仅暂存运行时必需的文件
4. `git commit -m "release: v*"` — 提交只包含发布文件的快照
5. `git branch -f main release-temp` — 用这个快照替换 `main` 分支
6. `git push origin main --force` — 强制推送到远程

由于使用了 `--orphan`，`main` 分支的每次发布都是一个独立的根提交，没有与 `dev` 共享的历史。这保证了 `main` 的纯净。

推送时使用 Personal Access Token（`RELEASE_TOKEN` Secret）绕过 GitHub 分支保护规则，确保只有 GitHub Actions 可以写入 `main`。

### 远程仓库防护

为防止意外推送 `main` 分支，在 GitHub 仓库设置中配置了分支保护规则：

- 分支名：`main`；
- "Restrict who can push to matching branches" — 已启用；
- 仅允许 GitHub Actions（通过 PAT）推送。

因此，执行 `git push origin main` 会被 GitHub 直接拒绝。

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

**5. 推送标签（触发 GitHub Actions 自动同步到 main）**

```bash
git push origin v0.2.0
```

推送标签后，GitHub Actions 工作流 `sync-main-on-tag.yml` 会自动执行，将发布文件同步到 `main` 分支。

**可选：同时推送 dev 分支的最新提交**

```bash
git push origin dev
```

如果希望远程 `dev` 分支也保持最新，可以一并推送。

推送标签后，可以在 GitHub 仓库的 Actions 页面查看 `sync release to main` 工作流的执行状态。执行成功后，`main` 分支将自动更新为只包含 12 个发布文件的新快照。

## 常见问题

### 如果不小心对 `main` 执行了 `git push`？

GitHub 的分支保护规则会直接拒绝推送：`remote: error: GH006: Protected branch update failed for refs/heads/main.`

### 如果本地不小心创建了 `main` 分支？

没有影响。`main` 仅存在于远程，且本地的 `main` 分支内容与远程不同。只需删除本地分支：`git branch -D main`。

### `RELEASE_TOKEN` 是什么？

是一个 GitHub Fine-grained Personal Access Token，具有对仓库 `Contents: Write` 权限。它被存储在仓库的 Secrets 中（名称为 `RELEASE_TOKEN`），供 GitHub Actions 在推送 `main` 时认证使用。

### 为什么不在本地创建 `main` 分支？

避免误推。本地只有 `dev`，开发者没有机会执行 `git push origin main`。`main` 的维护完全交由 GitHub Actions 处理。
