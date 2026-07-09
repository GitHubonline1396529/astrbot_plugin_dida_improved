# 配置

## 配置项

插件提供了如下的配置选项，其中 `access_token` 是一个必填项，如不填写，则项目将无法使用。

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `access_token` | string | (空) | Dida365 Open API Access Token，必填 |
| `api_base_url` | string | `https://api.dida365.com/open/v1` | API 基础地址 |
| `default_project` | string | (空) | 创建任务时的兜底项目 |
| `timezone` | string | `Asia/Shanghai` | 插件时区 |
| `request_timeout_seconds` | int | `15` | API 请求超时秒数 |
| `display_limit` | int | `50` | 列表每次最多显示的条目数，设为 0 则不截断 |

## 获取 Access Token

本指南参考了
[zhenyumi/astrbot_plugin_dida365](https://github.com/zhenyumi/astrbot_plugin_dida365) 的原版说明，原作者已写得非常认真而且详细了，而且每一步都有截图。这里真得感谢人家。你可以直接前往该仓库查看 (如果你去了的话，别忘了给人家的仓库点个小星星)。如果你不想跳转，下文也提供了一份完整的操作说明。

### 第 1 步：创建应用

打开 [Dida365 开发者平台](https://developer.dida365.com/manage) 并登录。当然，这需要你提前注册好你的 Dida 365 账号，可以使用邮箱注册。

接下来，点击"创建 App"，填写应用名称 (这里建议您填写 `Astrbot`)。创建完成后你会看到两个关键信息：

- **Client ID**;；
- **Client Secret**。

接着在应用配置中设置回调地址 (Callback URL)，例如：

```
http://localhost:8000/callback
```

!!! tips "设置回调地址"
    这个地址只需能够接收 OAuth 回调即可，它不必是一个真正运行的服务器——你只需要从浏览器地址栏中复制出 `code` 参数。

### 第 2 步：打开授权链接

在浏览器中访问以下地址 (替换 `你的_CLIENT_ID`)：

```
https://dida365.com/oauth/authorize?client_id=你的_CLIENT_ID&response_type=code&redirect_uri=http://localhost:8000/callback&scope=tasks:read%20tasks:write&state=123
```

用自己的 Dida365 账号登录并完成授权。这里请求了两个权限：

- `tasks:read` — 读取任务；
- `tasks:write` — 写入任务。

### 第 3 步：从回调地址中取出 code

授权成功后，浏览器会被重定向到你填写的回调地址，类似：

```
http://localhost:8000/callback?code=ABC123&state=123
```

从浏览器地址栏中复制出 `code` 参数的值 (上例中的 `ABC123`)。

!!! warning "code 有效期"
    这个 `code` 通常只能使用一次，过期后需要重新授权。

### 第 4 步：生成 Basic 认证字符串

将你的 `ClientID:ClientSecret` (中间用冒号连接) 进行 Base64 编码。

对于 **Windows** 平台的用户，你可以使用如下的 **PowerShell** 命令：

```powershell
$plain = "你的ClientID:你的ClientSecret"
$bytes = [System.Text.Encoding]::UTF8.GetBytes($plain)
[Convert]::ToBase64String($bytes)
```

而对于 **macOS** / **Linux** 的用户，你可以使用下面的 Bash 命令：

```bash
printf '%s' '你的ClientID:你的ClientSecret' | base64
```

输出的字符串就是后续请求中 `Authorization: Basic ...` 里填的内容。

### 第 5 步：用 code 换取 access_token

**PowerShell：**

```powershell
curl.exe -X POST "https://dida365.com/oauth/token" `
  -H "Authorization: Basic 你的Base64结果" `
  -H "Content-Type: application/x-www-form-urlencoded" `
  --data-urlencode "grant_type=authorization_code" `
  --data-urlencode "code=你的code" `
  --data-urlencode "redirect_uri=http://localhost:8000/callback"
```

!!! tips "你可以直接复制这里的命令"
    哦，对对对，我想起来了，Windows Terminal 复制黏贴多行终端文本的时候一直会出现粘贴困难的问题，文本末尾的换行符 `\n` 经常触发命令被直接执行。所以我这里帮你提前打好了一个 one line 的版本，你可以直接从这里复制过去粘贴执行。

    ```powershell
    curl.exe -X POST "https://dida365.com/oauth/token" -H "Authorization: Basic 你的Base64结果" -H "Content-Type: application/x-www-form-urlencoded" --data-urlencode "grant_type=authorization_code" --data-urlencode "code=你的code" --data-urlencode "redirect_uri=http://localhost:8000/callback"
    ```

**macOS / Linux：**

```bash
curl -X POST "https://dida365.com/oauth/token" \
  -H "Authorization: Basic 你的Base64结果" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "grant_type=authorization_code" \
  --data-urlencode "code=你的code" \
  --data-urlencode "redirect_uri=http://localhost:8000/callback"
```

### 第 6 步：获取结果

请求成功后，服务端会返回类似以下的 JSON：

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 15551999,
  "scope": "tasks:read tasks:write"
}
```

将 `access_token` 字段的值完整复制，填入插件配置的 `access_token` 项中。

!!! danger "安全提醒"
    - `Client Secret` 和 `access_token` 等同于你的账号密码，不要泄露给他人。
    - `redirect_uri` 必须和后台配置的回调地址完全一致。

### 第 7 步：验证

在聊天中发送 `/dida_ping` 确认插件已加载，再发送 `/dida_probe` 确认 Token 有效。

### Token 有效期与更新

- `access_token` 有效期通常约 **180 天**；
- 本插件不会自动刷新 Token，到期后需要重复上述步骤重新获取并手动更新配置；
- 如果 API 返回 401 或 403 错误，请优先检查 Token 是否已失效。
