# 安装

## 环境要求

- Python >= 3.11；
- [AstrBot](https://github.com/AstrBotDevs/AstrBot) >= 4.0.0。

## 安装步骤

目前我正在着手将这个插件发布到 Astrbot 的插件市场，如果发布成功就可以在 Astrbot 的插件页面直接下载安装。在此之前，可以先通过下列所示的安装方法安装本插件：

### 通过 Git 安装

1. 进入 AstrBot 的插件目录；

    ```bash
    cd path/to/astrbot/data/plugins
    ```

2. 执行如下的命令克隆仓库；

    ```bash
    git clone https://github.com/GitHubonline1396529/astrbot_plugin_dida_improved.git
    ```

3. 重启 AstrBot，或在 Web UI 中重载插件。

4. 在插件配置中至少应当填写您的 `access_token`。

!!! note "关于 Astrbot 的运行时目录所在的位置"
    需要注意的是，由于安装方式的不同，运行时目录可能略有区别。具体的路径请参阅 [Astrbot 官方文档中有关部署方法的部分](https://docs.astrbot.app/deploy/astrbot/package.html)。

### 手动安装

具体的操作流程如下：

1. 从本项目的仓库地址 [astrbot_plugin_dida_improved](https://github.com/GitHubonline1396529/astrbot_plugin_dida_improved) 下载插件的源码压缩包 (`main` 分支)；
2. 将插件目录解压后放置到 AstrBot 的运行时目录下的 `data/plugins/` 下；
3. 在 WebUI 中重载插件，或者直接重启 AstrBot；
4. 在插件配置中至少应当填写您的 `access_token`。

## 验证安装

在聊天中输入以下指令确认插件已正确加载：

```
/dida_ping
```

如果返回类似以下信息则表示安装成功：

```
Dida365 Improved Plugin loaded
- Access token configured: True
- API base URL: https://api.dida365.com/open/v1
- Timezone: Asia/Shanghai
```
