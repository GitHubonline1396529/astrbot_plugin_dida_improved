# 管理员指令

所有指令需以管理员身份执行。

## 指令列表

本项目提供了如下的两个测试用指令，以确保项目处于正常工作的状态：

| 指令 | 说明 | 使用示例 |
|------|------|----------|
| `/dida_ping` | 检查插件加载状态和配置 | `/dida_ping` |
| `/dida_probe` | 执行一次只读 API 探测 | `/dida_probe` |

## 指令详解

### `/dida_ping`

检查插件的基本加载状态，确认配置是否有效。

**返回示例：**

```
Dida365 Improved Plugin loaded
- Access token configured: True
- API base URL: https://api.dida365.com/open/v1
- Timezone: Asia/Shanghai
```

### `/dida_probe`

执行一次只读 API 探测，验证 Dida365 API 的可达性和凭证有效性。

**返回示例：**

```
Dida365 API read probe successful.
- Project count: 3
- Sample projects: 工作, 学习, 生活
```
