<div align="center">

# 🗓️ 签到卡片

**一句「签到」，生成属于你的每日卡片**

[![MaiBot](https://img.shields.io/badge/MaiBot-1.0.0%2B-00a66a?style=flat-square)](https://github.com/Mai-with-u/MaiBot)
[![SDK](https://img.shields.io/badge/SDK-2.x-2f5fff?style=flat-square)](https://github.com/Mai-with-u/MaiBot)
[![Version](https://img.shields.io/badge/version-1.0.0-orange?style=flat-square)](#)
[![License](https://img.shields.io/badge/license-MIT-blue?style=flat-square)](LICENSE)

<img src="docs/card-preview.png" width="380" alt="签到卡片预览" />

</div>

---

## ✨ 功能特性

- 🎴 **一键出图**：下载用户头像 → 高斯模糊铺底 → 圆形头像 → 昵称 / 天数 / 一言 / 日期
- 📅 **累计 + 连续**：记录累计签到天数与连续签到天数，断签自动重置连续天数
- 📚 **一言文案**：接入 hitokoto 接口，失败时回退到内置句子，不会因为断网画不出图
- 🏆 **双排行榜**：累计签到榜、连续签到榜，前三名奖牌展示
- 🎨 **高度可调**：画布尺寸、头像比例、模糊半径、遮罩浓度、文字颜色、字号全部可配
- 🔤 **字体自动探测**：优先插件 `fonts/` 目录，其次系统字体（雅黑 / 黑体 / 文泉驿 / Noto / 苹方）
- 💾 **数据安全**：签到数据写入 MaiBot 运行时数据目录，更新插件不丢档

## 💬 使用指令

| 指令 | 说明 | 权限 |
| --- | --- | --- |
| `签到` | 生成今日签到卡片 | 所有人 |
| `签到排行榜` | 累计签到天数排行榜（Top 15） | 所有人 |
| `连续签到排行榜` | 连续签到天数排行榜（Top 15） | 所有人 |
| `签到数据` | 查看数据库路径、用户数与记录明细 | 所有人 |
| `签到重置` | 清空全部签到数据 | 仅管理员 |

## 🚀 快速安装

### 1. 放置插件

```text
MaiBot/plugins/WMX20081122_maibot-qiandao/
├── _manifest.json
├── plugin.py
├── config.py
├── card.py
└── config.toml        ← 复制 config.example.toml 而来
```

也可以直接在 **WebUI 插件市场** 搜索「签到卡片」一键安装。

### 2. 安装依赖

```bash
pip install aiohttp pillow
```

### 3. 配置管理员

复制 `config.example.toml` 为 `config.toml`，至少填上管理员 QQ（用于重置数据）：

```toml
[admin]
admin_qqs = ["你的QQ号"]
```

### 4. 重载插件

保存后重载插件，群里发送 `签到` 即可。

## ⚙️ 配置说明

### 卡片外观

| 配置项 | 默认值 | 说明 |
| --- | --- | --- |
| `card.canvas_width` / `canvas_height` | `900` / `1200` | 画布尺寸（等比缩放） |
| `card.avatar_ratio` | `0.78` | 头像宽度占画布比例 |
| `card.avatar_top_margin` | `40` | 头像距顶部像素 |
| `card.avatar_border_width` | `10` | 头像白色边框宽度 |
| `card.bg_blur_radius` | `40` | 背景高斯模糊半径 |
| `card.bg_overlay_alpha` | `140` | 背景暗化遮罩透明度（0-255） |
| `card.text_color` | `#FFFFFF` | 文字颜色 |
| `card.text_shadow` | `true` | 是否绘制文字阴影 |
| `card.show_date` | `true` | 是否显示底部日期 |
| `card.font_size_days` | `76` | 天数字号 |
| `card.font_size_hitokoto` | `40` | 一言字号 |
| `card.font_size_date` | `32` | 昵称 / 日期字号 |
| `card.font_path` | 空 | 自定义字体路径，留空自动探测 |

### 其他

| 配置项 | 默认值 | 说明 |
| --- | --- | --- |
| `plugin.enabled` | `true` | 插件总开关 |
| `admin.admin_qqs` | `[]` | 管理员 QQ 列表，仅这些人可用「签到重置」 |

## 🔤 使用自定义字体

把 `.ttf` / `.ttc` / `.otf` 放进插件的 `fonts/` 目录（默认不随仓库分发字体文件，避免字体授权问题），重启或重载插件即自动生效；也可以在 `card.font_path` 里填字体的绝对路径。

## ❓ 常见问题

<details>
<summary>卡片里中文显示成方块？</summary>

说明没找到可用中文字体。把中文字体丢进插件 `fonts/` 目录，或在 `card.font_path` 指定字体文件路径。

</details>

<details>
<summary>提示「头像下载失败」？</summary>

卡片背景依赖用户头像（`qlogo` 接口）。检查服务器能否访问外网；偶发失败重发一次通常就好。

</details>

<details>
<summary>签到数据存在哪里？</summary>

MaiBot 运行时分配给插件的数据目录下的 `qiandao.json`。旧版本写在插件目录 `data/` 里的数据会自动迁移。

</details>

<details>
<summary>如何清空全部签到数据？</summary>

管理员发送 `签到重置`，或直接删除数据目录下的 `qiandao.json` 后重载插件。

</details>

## 🧱 环境要求

- MaiBot ≥ 1.0.0，插件 SDK 2.x
- 适配器插件 [`maibot-team.snowluma-adapter`](https://github.com/Mai-with-u/MaiBot-SnowLuma-Adapter)（用于取用户昵称）
- Python 依赖：`aiohttp`、`Pillow`

## 🙏 致谢

移植自作者本人的 AstrBot 插件 [astrbot_plugin_qiandao](https://github.com/WMX20081122/astrbot_plugin_qiandao)，卡片绘制逻辑保持不变，运行时改为适配 MaiBot SDK 2.x。

## 📄 许可证

[MIT](LICENSE) © 2026 WMX20081122

<div align="center">

如果这个插件帮到了你，欢迎点一个 ⭐ Star

</div>
