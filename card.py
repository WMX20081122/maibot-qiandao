"""签到卡片图片绘制逻辑（迁移自 astrbot_plugin_qiandao，作者 WMX20081122）。

仅包含与平台无关的纯 GIL 图片渲染，由 plugin.py 调用。
at 绘制能力完全不依赖 astrbot/MaiBot。
"""

from __future__ import annotations

import io
import logging
import os
import random
from datetime import datetime
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFilter, ImageFont

logger = logging.getLogger("plugin.maibot_qiandao.card")

SYSTEM_FONT_CANDIDATES = [
    "C:/Windows/Fonts/msyh.ttc",  # Windows 微软雅黑
    "C:/Windows/Fonts/simhei.ttf",  # Windows 黑体
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",  # Linux 文泉驿
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",  # Linux Noto
    "/System/Library/Fonts/PingFang.ttc",  # macOS 苹方
]

HITOKOTO_API = "https://v1.hitokoto.cn/?encode=json&charset=utf-8"
AVATAR_API = "https://q4.qlogo.cn/headimg_dl?dst_uin={qq}&spec=640"

HITOKOTO_FALLBACKS = [
    "生活不止眼前的苟且，还有诗和远方。",
    "星光不问赶路人，时光不负有心人。",
    "愿你出走半生，归来仍是少年。",
    "凡是过往，皆为序章。",
    "愿你被这个世界温柔以待。",
]


class QiandaoCard:
    """生成签到卡片图片。"""

    def __init__(self, card_config, plugin_dir: str) -> None:
        # card_config: 兼容 dict，键名遵循原插件 config（canvas_*, avatar_*, font_size_*...）
        self._cfg = card_config
        self._plugin_dir = Path(plugin_dir)
        self._font_path: Optional[str] = None
        self._init_fonts()

    # ---- 字体 ----

    def _scan_plugin_fonts(self):
        fonts_dir = self._plugin_dir / "fonts"
        found = []
        if fonts_dir.exists():
            for ext in ["*.ttf", "*.ttc", "*.otf"]:
                found.extend(fonts_dir.glob(ext))
        return sorted(found)

    def _scan_system_fonts(self):
        return [Path(fp) for fp in SYSTEM_FONT_CANDIDATES if os.path.exists(fp)]

    def _get_font_path(self):
        # 1. 插件内置字体
        plugin_fonts = self._scan_plugin_fonts()
        if plugin_fonts:
            return plugin_fonts[0]
        # 2. 用户配置
        cfg = (getattr(self._cfg, "font_path", "") or "").strip()
        if cfg and os.path.exists(cfg):
            return Path(cfg)
        # 3. 系统自动检测
        sys_fonts = self._scan_system_fonts()
        if sys_fonts:
            return sys_fonts[0]
        logger.error("未找到任何可用字体，文字可能显示为方块")
        return None

    def _init_fonts(self):
        font_path = self._get_font_path()
        self._font_path = str(font_path) if font_path else None

    def _get(self, key, default):
        return getattr(self._cfg, key, None) if self._cfg is not None else None or default

    def create(self, avatar_bytes: bytes, days: int, hitokoto: str, nickname: str) -> bytes:
        """生成签到卡片 PNG，返回字节流。"""
        W = int(self._get("canvas_width", 900))
        H = int(self._get("canvas_height", 1200))

        scale_w = W / 900.0
        scale_h = H / 1200.0
        scale = min(scale_w, scale_h)

        avatar_ratio = float(self._get("avatar_ratio", 0.78))
        top_margin = int(int(self._get("avatar_top_margin", 40)) * scale_h)
        border_width = max(2, int(int(self._get("avatar_border_width", 10)) * scale))
        blur_radius = int(self._get("bg_blur_radius", 40))
        overlay_alpha = int(self._get("bg_overlay_alpha", 140))
        text_color_hex = str(self._get("text_color", "#FFFFFF")).strip() or "#FFFFFF"
        text_shadow = bool(self._get("text_shadow", True))
        show_date = bool(self._get("show_date", True))

        size_days = max(16, int(int(self._get("font_size_days", 76)) * scale))
        size_hitokoto = max(12, int(int(self._get("font_size_hitokoto", 40)) * scale))
        size_date = max(10, int(int(self._get("font_size_date", 32)) * scale))

        # 字体对象
        font_large, font_medium, font_small = self._load_fonts(
            (size_days, size_hitokoto, size_date)
        )

        text_color = self._hex_to_rgba(text_color_hex, 255)
        text_color_dim = self._hex_to_rgba(text_color_hex, 230)
        text_color_faint = self._hex_to_rgba(text_color_hex, 180)

        # 1. 背景：头像放大 + 高斯模糊 + 暗化遮罩
        avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
        bg = avatar.copy().resize((W, H), Image.LANCZOS)
        bg = bg.filter(ImageFilter.GaussianBlur(radius=blur_radius))
        overlay = Image.new("RGBA", (W, H), (0, 0, 0, overlay_alpha))
        bg = Image.alpha_composite(bg.convert("RGBA"), overlay)

        # 2. 圆形头像（带白色边框）
        avatar_size = int(W * avatar_ratio)
        avatar_img = avatar.resize((avatar_size, avatar_size), Image.LANCZOS)
        mask = Image.new("L", (avatar_size, avatar_size), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, avatar_size, avatar_size), fill=255)
        circle_avatar = Image.new("RGBA", (avatar_size, avatar_size), (0, 0, 0, 0))
        circle_avatar.paste(avatar_img, (0, 0), mask)

        bordered = Image.new(
            "RGBA",
            (avatar_size + border_width * 2, avatar_size + border_width * 2),
            (0, 0, 0, 0),
        )
        border_draw = ImageDraw.Draw(bordered)
        border_draw.ellipse(
            (0, 0, avatar_size + border_width * 2, avatar_size + border_width * 2),
            fill=(255, 255, 255, 255),
        )
        bordered.paste(circle_avatar, (border_width, border_width), circle_avatar)

        avatar_x = (W - bordered.width) // 2
        avatar_y = top_margin
        bg.paste(bordered, (avatar_x, avatar_y), bordered)

        # 3. 绘制文字
        draw = ImageDraw.Draw(bg)
        text_start_y = avatar_y + bordered.height + int(56 * scale)

        if nickname:
            name_bbox = draw.textbbox((0, 0), nickname, font=font_small)
            name_x = (W - (name_bbox[2] - name_bbox[0])) // 2
            if text_shadow:
                draw.text((name_x + 1, text_start_y + 1), nickname, font=font_small, fill=(0, 0, 0, 128))
            draw.text((name_x, text_start_y), nickname, font=font_small, fill=text_color_dim)
            text_start_y += size_date + int(24 * scale)

        days_text = f"累计签到 {days} 天"
        bbox = draw.textbbox((0, 0), days_text, font=font_large)
        text_w = bbox[2] - bbox[0]
        text_x = (W - text_w) // 2
        if text_shadow:
            draw.text((text_x + 2, text_start_y + 2), days_text, font=font_large, fill=(0, 0, 0, 128))
        draw.text((text_x, text_start_y), days_text, font=font_large, fill=text_color)
        text_start_y += size_days + int(20 * scale)

        max_text_width = int(W * 0.85)
        hitokoto_lines = self._wrap_text(draw, hitokoto, font_medium, max_text_width)
        if len(hitokoto_lines) > 3:
            new_size = max(12, int(size_hitokoto * 0.8))
            try:
                font_medium = ImageFont.truetype(self._font_path, new_size)
            except Exception:
                pass
            hitokoto_lines = self._wrap_text(draw, hitokoto, font_medium, max_text_width)

        for line in hitokoto_lines:
            bbox = draw.textbbox((0, 0), line, font=font_medium)
            text_w = bbox[2] - bbox[0]
            text_x = (W - text_w) // 2
            if text_shadow:
                draw.text((text_x + 1, text_start_y + 1), line, font=font_medium, fill=(0, 0, 0, 128))
            draw.text((text_x, text_start_y), line, font=font_medium, fill=text_color_dim)
            text_start_y += size_hitokoto + int(10 * scale)

        if show_date:
            date_text = datetime.now().strftime("%Y年%m月%d日")
            bbox = draw.textbbox((0, 0), date_text, font=font_small)
            text_w = bbox[2] - bbox[0]
            text_x = (W - text_w) // 2
            date_y = H - int(80 * scale_h)
            draw.text((text_x, date_y), date_text, font=font_small, fill=text_color_faint)

        final = bg.convert("RGB")
        buf = io.BytesIO()
        final.save(buf, format="PNG", quality=95)
        return buf.getvalue()

    def _load_fonts(self, sizes):
        out = []
        for size in sizes:
            try:
                if self._font_path:
                    out.append(ImageFont.truetype(self._font_path, size))
                else:
                    out.append(ImageFont.load_default())
            except Exception:
                out.append(ImageFont.load_default())
        return out

    @staticmethod
    def _hex_to_rgba(hex_color, alpha=255):
        hex_color = hex_color.lstrip("#")
        if len(hex_color) == 3:
            hex_color = "".join([c * 2 for c in hex_color])
        return (
            int(hex_color[0:2], 16),
            int(hex_color[2:4], 16),
            int(hex_color[4:6], 16),
            alpha,
        )

    @staticmethod
    def _wrap_text(draw, text, font, max_width):
        lines = []
        current_line = ""
        for char in text:
            test_line = current_line + char
            bbox = draw.textbbox((0, 0), test_line, font=font)
            w = bbox[2] - bbox[0]
            if w > max_width and current_line:
                lines.append(current_line)
                current_line = char
            else:
                current_line = test_line
        if current_line:
            lines.append(current_line)
        if not lines:
            lines = [text]
        return lines