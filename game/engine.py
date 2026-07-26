"""
O'yin dvigateli (Game Engine).

Har bir guruh (chat_id) uchun xotirada (in-memory) bitta `GameEngine` obyekti ishlaydi.
Bu klass butun o'yin siklini boshqaradi: ro'yxatdan o'tish -> tun -> kun -> ovoz berish ->
osish/oxirgi so'z -> g'alaba shartini tekshirish -> o'yin tugashi va mukofotlash.

ESLATMA: Bu - to'liq ishlaydigan, lekin soddalashtirilgan versiya. Admin panelda qo'shilgan
har bir custom rol "team" (mafia/tinch/yakka) va "night_action_type" orqali umumiy
mexanikaga ulanadi. Agar action_type="custom" bo'lsa, rol faqat hikoya/rol-play uchun
ishlatiladi va avtomatik tunda harakat qilmaydi (lekin g'alaba hisobida jamoasi hisobga olinadi).
"""
import asyncio
import random
from datetime import datetime

from aiogram import Bot
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import (
    NIGHT_SECONDS, DAY_DISCUSSION_SECONDS, VOTING_SECONDS, LAST_WORDS_SECONDS,
    REGISTRATION_SECONDS, MIN_PLAYERS,
)
from database import crud
from database.models import NightActionType, RoleTeam
from locales.texts import t
from game.roles_logic import assign_roles, check_win_condition

# Har bir chat uchun faol o'yin (chat_id -> GameEngine)
ACTIVE_GAMES: dict[int, "GameEngine"] = {}


class PlayerState:
    def __init__(self, user_id: int, name: str):
        self.user_id = user_id
        self.name = name
        self.role = None
        self.alive = True
        self.last_active = datetime.utcnow()
        self.protected_tonight = False


class GameEngine:
    def __init__(self, bot: Bot, chat_id: int, session_id: int, host_id: int):
        self.bot = bot
        self.chat_id = chat_id
        self.session_id = session_id
        self.host_id = host_id
        self.players: dict[int, PlayerState] = {}
        self.day_number = 0
        self.night_actions: dict[int, int] = {}   # actor_id -> target_id
        self.votes: dict[int, str] = {}            # voter_id -> "like"/"dislike"
        self.current_nominee: int | None = None
        self.lang = "uz"
        self.registration_open = True
        self.registration_message_id: int | None = None
        self.group_link: str | None = None
        self.stopped = False
        self.nomination_open = False
        self.nominations: dict[int, int] = {}  # voter_id -> nominee_id

    # -------------------------------------------------------------------
    # RO'YXATDAN O'TISH
    # -------------------------------------------------------------------
    def add_player(self, user_id: int, name: str) -> bool:
        if user_id in self.players:
            return False
        self.players[user_id] = PlayerState(user_id, name)
        return True

    def alive_players(self) -> list[PlayerState]:
        return [p for p in self.players.values() if p.alive]

    def alive_ids(self) -> set[int]:
        return {p.user_id for p in self.alive_players()}

    async def registration_message_text(self) -> str:
        names = "\n".join(f"{i+1}. {p.name}" for i, p in enumerate(self.players.values()))
        return t(
            "group_registration_open", self.lang,
            min_players=MIN_PLAYERS, players_list=names or "-", count=len(self.players)
        )

    async def refresh_registration_message(self):
        """Mavjud (qadalgan) ro'yxatdan o'tish xabarini yangi o'yinchilar ro'yxati bilan tahrirlaydi."""
        if not self.registration_message_id:
            return
        builder = InlineKeyboardBuilder()
        import config
        builder.button(
            text="🎮 Qo'shilish",
            url=f"https://t.me/{config.BOT_USERNAME}?start=join_{self.session_id}",
        )
        text = await self.registration_message_text()
        try:
            await self.bot.edit_message_text(
                text, chat_id=self.chat_id, message_id=self.registration_message_id,
                reply_markup=builder.as_markup(),
            )
        except Exception:
            pass

    # -------------------------------------------------------------------
    # O'YINNI BOSHLASH
    # -------------------------------------------------------------------
    async def start_game(self):
        if len(self.players) < MIN_PLAYERS:
            await self.bot.send_message(self.chat_id, t("not_enough_players", self.lang))
            await crud.update_game_status(self.session_id, __import__("database.models", fromlist=["GameStatus"]).GameStatus.cancelled)
            ACTIVE_GAMES.pop(self.chat_id, None)
            return

        roles = await crud.get_roles()
        if not roles:
            await self.bot.send_message(self.chat_id, "❌ Hozircha rollar sozlanmagan. Admin /admin orqali rol qo'shishi kerak.")
            ACTIVE_GAMES.pop(self.chat_id, None)
            return

        assignment = assign_roles(list(self.players.keys()), roles)
        for uid, role in assignment.items():
            self.players[uid].role = role
            db_role_id = role.id if role.id and role.id > 0 else None
            # DB ga saqlab qo'yamiz (statistikalar uchun)
            try:
                await self._save_player_role(uid, db_role_id)
            except Exception:
                pass

        await self.bot.send_message(self.chat_id, t("game_started", self.lang, mode="mega"))

        # Har bir o'yinchiga o'z rolini DM orqali yuboramiz
        for p in self.players.values():
            try:
                await self.bot.send_message(
                    p.user_id,
                    f"🎭 Sizning rolingiz: <b>{p.role.emoji} {p.role.name}</b>\n\n{p.role.description}",
                )
            except Exception:
                pass  # foydalanuvchi botni bloklagan bo'lishi mumkin

        await self.run_game_loop()

    async def _save_player_role(self, user_id: int, role_id: int | None):
        from database.db import async_session
        from database.models import GamePlayer
        from sqlalchemy import select, update
        async with async_session() as s:
            res = await s.execute(
                select(GamePlayer).where(GamePlayer.session_id == self.session_id, GamePlayer.user_id == user_id)
            )
            gp = res.scalar_one_or_none()
            if gp:
                gp.role_id = role_id
                await s.commit()

    # -------------------------------------------------------------------
    # ASOSIY TSIKL
    # -------------------------------------------------------------------
    async def run_game_loop(self):
        while True:
            if self.stopped:
                return
            self.day_number += 1
            await self.run_night_phase()
            if self.stopped:
                return

            winner = check_win_condition(
                {uid: p.role for uid, p in self.players.items()}, self.alive_ids()
            )
            if winner:
                await self.finish_game(winner)
                return

            await self.run_day_phase()
            if self.stopped:
                return

            winner = check_win_condition(
                {uid: p.role for uid, p in self.players.items()}, self.alive_ids()
            )
            if winner:
                await self.finish_game(winner)
                return

    # -------------------------------------------------------------------
    # TUN
    # -------------------------------------------------------------------
    async def run_night_phase(self):
        self.night_actions.clear()
        night_text = t("night_started", self.lang, night_number=self.day_number)
        try:
            import os
            from aiogram.types import FSInputFile
            asset_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "night.png")
            photo = FSInputFile(asset_path)
            await self.bot.send_photo(self.chat_id, photo, caption=night_text)
        except Exception:
            await self.bot.send_message(self.chat_id, night_text)

        # Harakat qiluvchi rollarga DM orqali nishon tanlash so'raladi
        actionable = [
            p for p in self.alive_players()
            if p.role and p.role.night_action_type != NightActionType.none
            and p.role.night_action_type != NightActionType.custom
        ]
        for p in actionable:
            await self._send_night_action_prompt(p)

        await asyncio.sleep(NIGHT_SECONDS)
        if self.stopped:
            return
        await self._announce_night_flavor()
        await self._resolve_night_actions()

    async def _announce_night_flavor(self):
        """Kimni nishonga olganini oshkor qilmasdan, qaysi rollar harakat qilganini guruhga bildiradi."""
        seen_roles = set()
        lines = []
        for actor_id in self.night_actions.keys():
            actor = self.players.get(actor_id)
            if not actor or not actor.role:
                continue
            key = actor.role.id or actor.role.name
            if key in seen_roles:
                continue
            seen_roles.add(key)
            action = actor.role.night_action_type
            if action == NightActionType.kill:
                lines.append(f"🔪 {actor.role.emoji} {actor.role.name} o'z o'ljasini tanladi...")
            elif action in (NightActionType.heal, NightActionType.protect):
                lines.append(f"🩺 {actor.role.emoji} {actor.role.name} kimningdir mehmoniga keldi...")
            elif action == NightActionType.check:
                lines.append(f"🔍 {actor.role.emoji} {actor.role.name} birovni tekshirmoqda...")
        if lines:
            await self.bot.send_message(self.chat_id, "\n".join(lines))

    async def _send_night_action_prompt(self, actor: PlayerState):
        builder = InlineKeyboardBuilder()
        for target in self.alive_players():
            if target.user_id == actor.user_id and actor.role.night_action_type == NightActionType.kill:
                continue  # o'zini o'ldira olmaydi (oddiy qoida)
            builder.button(text=target.name, callback_data=f"night_act:{self.chat_id}:{target.user_id}")
        builder.adjust(1)
        try:
            await self.bot.send_message(
                actor.user_id,
                f"🌙 {actor.role.emoji} {actor.role.name}: kimga harakat qilasiz?",
                reply_markup=builder.as_markup(),
            )
        except Exception:
            pass

    def register_night_action(self, actor_id: int, target_id: int):
        self.night_actions[actor_id] = target_id

    async def _resolve_night_actions(self):
        # Kim o'ldirilmoqchi ekanini aniqlaymiz
        kill_targets: list[int] = []
        heal_targets: set[int] = set()
        checked_info: list[tuple[int, int]] = []  # (checker_id, target_id)

        for actor_id, target_id in self.night_actions.items():
            actor = self.players.get(actor_id)
            if not actor or not actor.role:
                continue
            action = actor.role.night_action_type
            if action == NightActionType.kill:
                kill_targets.append(target_id)
            elif action == NightActionType.heal or action == NightActionType.protect:
                heal_targets.add(target_id)
            elif action == NightActionType.check:
                checked_info.append((actor_id, target_id))

        died = []
        for target_id in kill_targets:
            if target_id in heal_targets:
                continue
            target = self.players.get(target_id)
            if not target or not target.alive:
                continue
            # Himoya tekshiruvi (Do'kondan sotib olingan "qotildan himoya")
            protected = await crud.consume_protection(target_id, __import__("database.models", fromlist=["ProtectionType"]).ProtectionType.qotildan_himoya)
            if protected:
                continue
            target.alive = False
            died.append(target)

        # Komissar/tekshiruvchilarga natija yuboriladi
        for checker_id, target_id in checked_info:
            target = self.players.get(target_id)
            if target and target.role:
                try:
                    await self.bot.send_message(
                        checker_id,
                        f"🔍 Tekshiruv natijasi: {target.name} — {target.role.team.value.upper()} jamoasidan.",
                    )
                except Exception:
                    pass

        if died:
            await self.bot.send_message(self.chat_id, t("night_kill_announced", self.lang))
            for d in died:
                await self._handle_elimination_last_words(d, killed_at_night=True)
        else:
            await self.bot.send_message(self.chat_id, t("trust_message", self.lang))

    # -------------------------------------------------------------------
    # KUN (muhokama + nominatsiya + ovoz berish)
    # -------------------------------------------------------------------
    async def run_day_phase(self):
        await self.bot.send_message(self.chat_id, t("day_started", self.lang, day_number=self.day_number))
        await asyncio.sleep(min(DAY_DISCUSSION_SECONDS, 5))  # muhokama vaqti (qisqartirilgan demo)
        if self.stopped:
            return

        if len(self.alive_players()) <= 1:
            return

        nominee = await self._run_nomination_phase()
        if self.stopped:
            return
        if not nominee or not nominee.alive:
            await self.bot.send_message(self.chat_id, "🤐 Bugun hech kim nomzod sifatida ko'rsatilmadi.")
            self.current_nominee = None
            return

        self.current_nominee = nominee.user_id

        builder = InlineKeyboardBuilder()
        builder.button(text="👍", callback_data=f"vote_like:{self.chat_id}")
        builder.button(text="👎", callback_data=f"vote_dislike:{self.chat_id}")
        builder.adjust(2)

        await self.bot.send_message(
            self.chat_id,
            f"⚖️ {nominee.name} nomzod bo'ldi!\n" + t("voting_started", self.lang, seconds=VOTING_SECONDS),
            reply_markup=builder.as_markup(),
        )

        self.votes.clear()
        await asyncio.sleep(VOTING_SECONDS)
        if self.stopped:
            return

        likes = sum(1 for v in self.votes.values() if v == "like")
        dislikes = sum(1 for v in self.votes.values() if v == "dislike")
        await self.bot.send_message(self.chat_id, t("vote_result", self.lang, likes=likes, dislikes=dislikes))

        if likes > dislikes:
            nominee.alive = False
            await self.bot.send_message(
                self.chat_id,
                t("player_hanged", self.lang, name=nominee.name, role_emoji=nominee.role.emoji, role_name=nominee.role.name),
            )
            await self._handle_elimination_last_words(nominee, killed_at_night=False)

        self.current_nominee = None

    async def _run_nomination_phase(self) -> PlayerState | None:
        """Hamma tirik o'yinchi o'zi xohlagan boshqa o'yinchini nomzod qilib ko'rsatishi mumkin."""
        alive = self.alive_players()
        if len(alive) < 2:
            return None

        self.nominations.clear()
        self.nomination_open = True

        builder = InlineKeyboardBuilder()
        for p in alive:
            builder.button(text=p.name, callback_data=f"nominate:{self.chat_id}:{p.user_id}")
        builder.adjust(2)

        await self.bot.send_message(
            self.chat_id,
            f"🗳 Kimni shubha ostiga qo'yasiz? Nomzod tanlang! ({VOTING_SECONDS} soniya)",
            reply_markup=builder.as_markup(),
        )

        await asyncio.sleep(VOTING_SECONDS)
        self.nomination_open = False

        if not self.nominations:
            return None

        tally: dict[int, int] = {}
        for nominee_id in self.nominations.values():
            tally[nominee_id] = tally.get(nominee_id, 0) + 1
        max_votes = max(tally.values())
        top_candidates = [uid for uid, c in tally.items() if c == max_votes]
        winner_id = random.choice(top_candidates)
        return self.players.get(winner_id)

    def register_nomination(self, voter_id: int, nominee_id: int):
        if not self.nomination_open:
            return False
        if voter_id not in self.alive_ids():
            return False
        if nominee_id not in self.alive_ids():
            return False
        self.nominations[voter_id] = nominee_id
        return True

    def register_vote(self, voter_id: int, choice: str):
        if voter_id not in self.alive_ids():
            return False
        self.votes[voter_id] = choice
        return True

    # -------------------------------------------------------------------
    # OXIRGI SO'Z (endi guruhda emas — o'yinchining botdagi shaxsiy chatida yoziladi)
    # -------------------------------------------------------------------
    async def _handle_elimination_last_words(self, player: PlayerState, killed_at_night: bool):
        from handlers.group.registration import LAST_WORDS_LISTENERS

        dm_sent = True
        try:
            await self.bot.send_message(
                player.user_id,
                t("last_words_prompt_dm", self.lang, seconds=LAST_WORDS_SECONDS),
            )
        except Exception:
            dm_sent = False

        await self.bot.send_message(
            self.chat_id, t("last_words_wait_group", self.lang, name=player.name)
        )

        words = "..."
        if dm_sent:
            future = asyncio.get_event_loop().create_future()
            LAST_WORDS_LISTENERS[player.user_id] = future
            try:
                words = await asyncio.wait_for(future, timeout=LAST_WORDS_SECONDS)
            except asyncio.TimeoutError:
                words = "..."
            finally:
                LAST_WORDS_LISTENERS.pop(player.user_id, None)

        await self.bot.send_message(
            self.chat_id, t("last_words_announced", self.lang, name=player.name, words=words)
        )

    # -------------------------------------------------------------------
    # O'YIN TUGASHI
    # -------------------------------------------------------------------
    async def finish_game(self, winner_team: str):
        await crud.finish_game(self.session_id)

        winners = [p for p in self.players.values() if p.role and p.role.team.value == winner_team]
        others = [p for p in self.players.values() if p not in winners]

        winners_text = "\n".join(f"{i+1}. {p.name} — {p.role.emoji} {p.role.name}" for i, p in enumerate(winners))
        others_text = "\n".join(f"{i+1}. {p.name} — {p.role.emoji} {p.role.name}" for i, p in enumerate(others))

        news_channel = await crud.get_setting("news_channel", "@SherifMafiaNews")

        text = (
            f"{t('game_over_title', self.lang)}\n\n"
            f"{t('winners_title', self.lang)}\n{winners_text or '-'}\n\n"
            f"{t('other_players_title', self.lang)}\n{others_text or '-'}\n\n"
            f"{t('reward_notice', self.lang, news_channel=news_channel)}"
        )
        await self.bot.send_message(self.chat_id, text)

        # Har bir o'yinchiga shaxsiy natija va mukofot
        winner_ids = {p.user_id for p in winners}
        for p in self.players.values():
            won = p.user_id in winner_ids
            user = await crud.apply_game_result(p.user_id, won)
            try:
                await self.bot.send_message(
                    p.user_id,
                    t("personal_result_won", user.language, money=user.money, diamonds=user.diamonds),
                )
            except Exception:
                pass

        ACTIVE_GAMES.pop(self.chat_id, None)
