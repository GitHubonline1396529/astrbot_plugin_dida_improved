# 常见问题

## reminders 字段导致 500 错误

通过 API 更新任务时，不要包含 `reminders` 字段，否则服务端返回 HTTP 500。如需设置提醒，请在滴答清单 App 中手动操作。

## 收集箱任务 projectId

收集箱任务的 `projectId` 为虚拟 ID（如 `inbox1014302018`），不可用于其他 API 端点。

## Access Token 过期

如果 `/dida_probe` 返回认证相关错误，说明 Access Token 可能已过期。请前往 [Dida365 Developer](https://developer.dida365.com) 重新获取 Token 并更新插件配置。

## 找不到项目或任务

确认：

1. Access Token 对应的账号下确实有项目/任务
2. 项目未被归档或删除
3. 网络环境可以正常访问 `api.dida365.com`
