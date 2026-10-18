"""签到卡片插件 — MaiBot 移植版。

迁移来源：astrbot_plugin_qiandao（作者 WMX20081122）。
命令：
    签到           生成精美签到卡片
    签到排行榜      累计签到排行榜
    连续签到排行榜  连续签到排行榜
    签到数据        查看聚合统计（仅操作员）
    签到重置        清空签到数据（仅操作员）

操作员由主程序 bot_config.toml 的 [plugin].permission 配置（如 "qq:123456789"）。
"""

from __future__ import annotations

import base64
import json
import random
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

import aiohttp

from maibot_sdk import Command, MaiBotPlugin

from . import config as cfg_mod
from .card import AVATAR_API, HITOKOTO_API, HITOKOTO_FALLBACKS, QiandaoCard


class QiandaoPlugin(MaiBotPlugin):
    config_model = cfg_mod.QiandaoConfig

    _db: Dict[str, Dict[str, Any]]
    _db_file: Path
    _card: QiandaoCard

    async def on_load(self) -> None:
        self._db = {}
        self._db_file = self._resolve_db_file()
        self._db_file.parent.mkdir(parents=True, exist_ok=True)
        self._load_db()

        self._card = QiandaoCard(self.config.card, str(Path(__file__).resolve().parent))
        self.ctx.logger.info("签到卡片插件已加载")

    def _resolve_db_file(self) -> Path:
        """数据写入运行时分配的统一数据目录；旧式插件目录数据自动迁移。"""
        legacy = Path(__file__).resolve().parent / "data" / "qiandao.json"
        data_dir = getattr(getattr(self.ctx, "paths", None), "data_dir", None)
        if not data_dir:
            return legacy
        target = Path(data_dir) / "qiandao.json"
        if not target.exists() and legacy.exists():
            try:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(legacy.read_bytes())
            except OSError:
                return legacy
        return target

    async def on_unload(self) -> None:
        self._save_db()

    async def on_config_update(self, scope: str, config_data: Dict[str, Any], version: str) -> None:
        del config_data
        if scope == "self":
            self._card = QiandaoCard(self.config.card, str(Path(__file__).resolve().parent))
            self.ctx.logger.info("签到卡片插件配置已更新(%s)", version)

    # ---- 命令 ----

    @Command("签到", description="生成精美签到卡片", pattern=r"^签到\s*$")
    async def cmd_qiandao(self, stream_id: str = "", **kwargs: Any) -> tuple:
        if not self._plugin_enabled():
            return True, None, False
        user_id = self._extract_user_id(kwargs)
        if not user_id:
            await self._reply(stream_id, "无法获取发送者 QQ，请重试。")
            return True, None, False

        nickname = await self._get_nickname(user_id, str(kwargs.get("platform") or ""))
        if not nickname:
            nickname = "用户"

        today = date.today().isoformat()
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        user_data = self._db.get(user_id, {})
        last_date = user_data.get("last_date", "")

        if last_date != today:
            days = user_data.get("days", 0) + 1
            streak = user_data.get("streak", 0)
            if last_date == yesterday:
                streak += 1
            else:
                streak = 1
            self._db[user_id] = {
                "last_date": today,
                "days": days,
                "streak": streak,
                "nickname": nickname,
            }
            self._save_db()

        days = self._db.get(user_id, {}).get("days", 0)
        streak = self._db.get(user_id, {}).get("streak", 0)

        avatar_bytes = await self._download_avatar(user_id)
        if not avatar_bytes:
            await self._reply(stream_id, f"累计签到 {days} 天，连续签到 {streak} 天\n（头像下载失败）")
            return True, None, False

        hitokoto = await self._fetch_hitokoto()

        try:
            img_bytes = self._card.create(avatar_bytes, days, hitokoto, nickname)
        except Exception as exc:
            self.ctx.logger.warning(f"签到生成图片失败: {exc}")
            await self._reply(stream_id, f"累计签到 {days} 天，连续签到 {streak} 天\n（图片生成失败）")
            return True, None, False

        await self._send_image(img_bytes, stream_id)
        return True, None, False

    @Command("签到排行榜", description="累计签到排行榜", pattern=r"^签到排行榜\s*$")
    async def cmd_rank_total(self, stream_id: str = "", **kwargs: Any) -> tuple:
        del kwargs
        if not self._plugin_enabled():
            return True, None, False
        if not self._db:
            await self._reply(stream_id, "暂无签到记录，快来签到吧！")
            return True, None, False
        sorted_users = sorted(self._db.items(), key=lambda x: x[1].get("days", 0), reverse=True)[:15]
        lines = ["🏆 累计签到排行榜", ""]
        medals = ["🥇", "🥈", "🥉"]
        for i, (uid, data) in enumerate(sorted_users, 1):
            days = data.get("days", 0)
            nick = data.get("nickname", "未知")
            prefix = medals[i - 1] if i <= 3 else f"  {i}."
            lines.append(f"{prefix} {nick}: {days}天")
        await self._reply(stream_id, "\n".join(lines))
        return True, None, False

    @Command("连续签到排行榜", description="连续签到排行榜", pattern=r"^连续签到排行榜\s*$")
    async def cmd_rank_streak(self, stream_id: str = "", **kwargs: Any) -> tuple:
        del kwargs
        if not self._plugin_enabled():
            return True, None, False
        if not self._db:
            await self._reply(stream_id, "暂无签到记录，快来签到吧！")
            return True, None, False
        sorted_users = sorted(self._db.items(), key=lambda x: x[1].get("streak", 0), reverse=True)[:15]
        lines = ["🔥 连续签到排行榜", ""]
        medals = ["🥇", "🥈", "🥉"]
        for i, (uid, data) in enumerate(sorted_users, 1):
            streak = data.get("streak", 0)
            nick = data.get("nickname", "未知")
            prefix = medals[i - 1] if i <= 3 else f"  {i}."
            lines.append(f"{prefix} {nick}: {streak}天")
        await self._reply(stream_id, "\n".join(lines))
        return True, None, False

    @Command("签到数据", description="查看签到统计（仅操作员）", pattern=r"^签到数据\s*$", permission="operator")
    async def cmd_data(self, stream_id: str = "", **kwargs: Any) -> tuple:
        del kwargs
        if not self._plugin_enabled():
            return True, None, False
        user_count = len(self._db)
        total_days = sum(int(data.get("days", 0) or 0) for data in self._db.values())
        max_streak = max((int(data.get("streak", 0) or 0) for data in self._db.values()), default=0)
        today = date.today().isoformat()
        today_count = sum(1 for data in self._db.values() if data.get("last_date") == today)
        lines = [
            "=== 签到统计 ===",
            f"用户数: {user_count}",
            f"累计签到总天数: {total_days}",
            f"今日已签到: {today_count}",
            f"最长连续签到: {max_streak} 天",
        ]
        await self._reply(stream_id, "\n".join(lines))
        return True, None, False

    @Command("签到重置", description="清空签到数据（仅操作员）", pattern=r"^签到重置\s*$", permission="operator")
    async def cmd_reset(self, stream_id: str = "", **kwargs: Any) -> tuple:
        if not self._plugin_enabled():
            return True, None, False
        old_count = len(self._db)
        self._db.clear()
        try:
            if self._db_file.exists():
                self._db_file.unlink()
        except Exception as exc:
            self.ctx.logger.warning(f"删除签到文件失败: {exc}")
        self._save_db()
        self.ctx.logger.warning(f"[签到] 操作员重置数据，清除 {old_count} 位用户")
        await self._reply(stream_id, f"✅ 已重置！清除了 {old_count} 位用户的记录。")
        return True, None, False

    # ---- 工具 ----

    def _plugin_enabled(self) -> bool:
        try:
            return bool(self.config.plugin.enabled)
        except Exception:
            return True

    @staticmethod
    def _extract_user_id(kwargs: Dict[str, Any]) -> Optional[str]:
        """取发送者 ID：优先命令参数里的 ``user_id``，再回退 ``message`` 报文。"""
        user_id = kwargs.get("user_id")
        if user_id:
            return str(user_id).strip()
        message = kwargs.get("message")
        if isinstance(message, dict):
            info = message.get("message_info") or {}
            user_info = info.get("user_info") if isinstance(info, dict) else None
            if isinstance(user_info, dict) and user_info.get("user_id"):
                return str(user_info["user_id"]).strip()
        return None

    async def _reply(self, stream_id: str, text: str) -> None:
        if not stream_id or not text:
            return
        try:
            await self.ctx.send.text(text, stream_id)
        except Exception as exc:
            self.ctx.logger.warning(f"回复消息失败: {exc}")

    async def _send_image(self, img_bytes: bytes, stream_id: str) -> None:
        if not stream_id:
            return
        try:
            img_b64 = base64.b64encode(img_bytes).decode("utf-8")
            await self.ctx.send.image(img_b64, stream_id)
        except Exception as exc:
            self.ctx.logger.warning(f"发送签到图片失败: {exc}")

    async def _call_napcat(self, action_name: str, params: Dict[str, Any]) -> Any:
        try:
            return await self.ctx.api.call("adapter.napcat.action.call", action_name=action_name, params=params)
        except Exception as exc:
            self.ctx.logger.debug(f"调用 NapCat 动作 {action_name} 失败: {exc}")
            return None

    async def _get_nickname(self, user_id: str, platform: str = "") -> str:
        nickname = await self._get_person_nickname(platform, user_id)
        if nickname:
            return nickname
        return await self._get_napcat_nickname(user_id)

    async def _get_person_nickname(self, platform: str, user_id: str) -> str:
        """优先从主程序人物库读取昵称。"""
        if not platform:
            return ""
        try:
            person_id = await self.ctx.person.get_id(platform, user_id)
            if not isinstance(person_id, str) or not person_id:
                return ""
            nickname = await self.ctx.person.get_value(person_id, "nickname")
            return nickname.strip() if isinstance(nickname, str) else ""
        except Exception as exc:
            self.ctx.logger.debug(f"[签到] 读取人物昵称失败: {exc}")
            return ""

    async def _get_napcat_nickname(self, user_id: str) -> str:
        info = await self._call_napcat(
            "get_stranger_info",
            {"user_id": int(user_id) if user_id.isdigit() else user_id, "no_cache": True},
        )
        info_data = info.get("data", info) if isinstance(info, dict) else {}
        if isinstance(info_data, dict):
            return str(info_data.get("nickname") or "").strip()
        return ""

    async def _download_avatar(self, qq: str) -> Optional[bytes]:
        url = AVATAR_API.format(qq=qq)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=15) as resp:
                    if resp.status == 200:
                        return await resp.read()
        except Exception as exc:
            self.ctx.logger.debug(f"[签到] 下载头像失败: {exc}")
        return None

    async def _fetch_hitokoto(self) -> str:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(HITOKOTO_API, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        h = data.get("hitokoto", "")
                        who = data.get("from_who", "")
                        src = data.get("from", "")
                        if who:
                            return f"「{h}」 —— {who}《{src}》"
                        elif src:
                            return f"「{h}」 —— 《{src}》"
                        return f"「{h}」"
        except Exception:
            pass
        return random.choice(HITOKOTO_FALLBACKS)

    # ---- 持久化 ----

    def _load_db(self) -> None:
        if self._db_file.exists():
            try:
                with open(self._db_file, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                if isinstance(raw, dict):
                    self._db = {str(k): dict(v) for k, v in raw.items() if isinstance(v, dict)}
                    return
            except Exception as exc:
                self.ctx.logger.warning(f"[签到] 加载数据库失败: {exc}")
        self._db = {}

    def _save_db(self) -> None:
        try:
            with open(self._db_file, "w", encoding="utf-8") as f:
                json.dump(self._db, f, ensure_ascii=False, indent=2)
        except Exception as exc:
            self.ctx.logger.warning(f"[签到] 保存数据库失败: {exc}")


def create_plugin() -> QiandaoPlugin:
    return QiandaoPlugin()