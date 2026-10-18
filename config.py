"""签到卡片插件 — 配置模型。"""

from __future__ import annotations

from typing import ClassVar, List

from maibot_sdk import Field, PluginConfigBase


class PluginSection(PluginConfigBase):
    __ui_label__: ClassVar[str] = "插件开关"
    __ui_order__: ClassVar[int] = 0

    enabled: bool = Field(
        default=True,
        description="是否启用本插件。",
        json_schema_extra={
            "hint": "插件总开关，关闭后不再响应签到命令。",
            "label": "启用插件",
            "order": 0,
        },
    )
    config_version: str = Field(
        default="1.0.0",
        json_schema_extra={"disabled": True, "hidden": True, "label": "配置版本", "order": 99},
    )


class AdminSection(PluginConfigBase):
    __ui_label__: ClassVar[str] = "管理员"
    __ui_order__: ClassVar[int] = 1

    admin_qqs: List[str] = Field(
        default_factory=list,
        description="管理员 QQ 号列表。",
        json_schema_extra={
            "hint": "只有这些 QQ 能用「签到重置」命令。",
            "label": "管理员 QQ",
            "order": 0,
            "placeholder": "请输入 QQ 号",
        },
    )


class CardSection(PluginConfigBase):
    __ui_label__: ClassVar[str] = "签到卡片"
    __ui_order__: ClassVar[int] = 2

    canvas_width: int = Field(
        default=900, ge=300, le=2000,
        json_schema_extra={"hint": "卡片画布宽度（像素）。", "label": "画布宽度", "order": 0, "step": 10},
    )
    canvas_height: int = Field(
        default=1200, ge=400, le=2600,
        json_schema_extra={"hint": "卡片画布高度（像素）。", "label": "画布高度", "order": 1, "step": 10},
    )
    avatar_ratio: float = Field(
        default=0.78,
        json_schema_extra={"hint": "头像占画布宽度的比例。", "label": "头像比例", "order": 2, "step": 0.01},
    )
    avatar_top_margin: int = Field(
        default=40,
        json_schema_extra={"hint": "头像距顶部间距（像素）。", "label": "头像顶部间距", "order": 3, "step": 1},
    )
    avatar_border_width: int = Field(
        default=10, ge=0,
        json_schema_extra={"hint": "头像白色边框宽度（像素）。", "label": "头像边框", "order": 4, "step": 1},
    )
    bg_blur_radius: int = Field(
        default=40, ge=0,
        json_schema_extra={"hint": "背景高斯模糊半径。", "label": "背景模糊", "order": 5, "step": 1},
    )
    bg_overlay_alpha: int = Field(
        default=140, ge=0, le=255,
        json_schema_extra={"hint": "背景暗化遮罩透明度。", "label": "背景遮罩", "order": 6, "step": 1},
    )
    text_color: str = Field(
        default="#FFFFFF",
        json_schema_extra={"hint": "文字颜色（十六进制）。", "label": "文字颜色", "order": 7, "placeholder": "#FFFFFF"},
    )
    text_shadow: bool = Field(
        default=True,
        json_schema_extra={"hint": "是否绘制文字阴影。", "label": "文字阴影", "order": 8},
    )
    show_date: bool = Field(
        default=True,
        json_schema_extra={"hint": "是否在卡片底部显示日期。", "label": "显示日期", "order": 9},
    )
    font_size_days: int = Field(
        default=76, ge=12,
        json_schema_extra={"hint": "签到天数文字字号。", "label": "天数字号", "order": 10, "step": 1},
    )
    font_size_hitokoto: int = Field(
        default=40, ge=12,
        json_schema_extra={"hint": "一言文字字号。", "label": "一言字号", "order": 11, "step": 1},
    )
    font_size_date: int = Field(
        default=32, ge=10,
        json_schema_extra={"hint": "日期文字字号。", "label": "日期字号", "order": 12, "step": 1},
    )
    font_path: str = Field(
        default="",
        description="自定义字体文件路径（.ttf/.ttc/.otf）。",
        json_schema_extra={
            "hint": "留空则依次尝试插件 fonts/ 目录字体与系统字体。",
            "label": "字体路径",
            "order": 13,
            "placeholder": "fonts/xxx.ttf",
        },
    )


class QiandaoConfig(PluginConfigBase):
    plugin: PluginSection = Field(default_factory=PluginSection)
    admin: AdminSection = Field(default_factory=AdminSection)
    card: CardSection = Field(default_factory=CardSection)