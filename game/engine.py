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

import config
from config import (
    NIGHT_SECONDS, DAY_DISCUSSION_SECONDS, VOTING_SECONDS, LAST_WORDS_SECONDS,
    REGISTRATION_SECONDS, MIN_PLAYERS,
)
from database import crud
from database.models import NightActionType, RoleTeam, ProtectionType
from locales.texts import t
from game.roles_logic import assign_roles, check_win_condition
from utils.helpers import mention

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
        self.acted_this_cycle = True  # birinchi tunda hali sikl boshlanmagan, shuning uchun True


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
        self.mode = "avtomatik"
        self.registration_open = True
        self.registration_message_id: int | None = None
        self.group_link: str | None = None
        self.stopped = False
        self.nomination_open = False
        self.nominations: dict[int, int] = {}  # voter_id -> nominee_id
        self.vote_message_id: int | None = None
        self.phase: str = "registration"  # registration | night | day | finished

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

    async def registration_welcome_text(self) -> str:
        """/game buyrug'i yuborilgan zahoti (hali hech kim real ravishda qo'shilmasdan) chiqadigan banner."""
        return t("game_registration_banner", self.lang, mode=self.mode)

    async def registration_message_text(self) -> str:
        from utils.helpers import mention
        names = "\n".join(f"{i+1}. {mention(p.user_id, p.name)}" for i, p in enumerate(self.players.values())) or "—"
        count = len(self.players)
        return t(
            "group_registration_open", self.lang,
            min_players=MIN_PLAYERS, players_list=names, count=count,
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
    async def start_game(self, force: bool = False):
        if not force and len(self.players) < MIN_PLAYERS:
            await self.bot.send_message(self.chat_id, t("not_enough_players", self.lang))
            await crud.update_game_status(self.session_id, __import__("database.models", fromlist=["GameStatus"]).GameStatus.cancelled)
            ACTIVE_GAMES.pop(self.chat_id, None)
            return
        if len(self.players) < 2:
            await self.bot.send_message(self.chat_id, "❌ O'yinni boshlash uchun kamida 2 ta o'yinchi kerak.")
            await crud.update_game_status(self.session_id, __import__("database.models", fromlist=["GameStatus"]).GameStatus.cancelled)
            ACTIVE_GAMES.pop(self.chat_id, None)
            return

        self.mode = await crud.get_mode_for_player_count(len(self.players))
        roles = await crud.get_roles(mode=self.mode)
        if not roles:
            roles = await crud.get_roles()  # rejimga mos rol topilmasa - hammasidan foydalanamiz
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

        await self.bot.send_message(
            self.chat_id, t("game_started", self.lang, mode=getattr(self, "mode", "classic"))
        )

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
        self.phase = "night"
        if self.day_number > 1:
            await self._kick_inactive_players()
            if self.stopped:
                return
            winner = check_win_condition(
                {uid: p.role for uid, p in self.players.items()}, self.alive_ids()
            )
            if winner:
                await self.finish_game(winner)
                return
        for p in self.alive_players():
            p.acted_this_cycle = False
        self.night_actions.clear()
        night_text = t("night_started", self.lang, night_number=self.day_number)
        await self._send_phase_media("night.mp4", "night.png", night_text)

        # Harakat qiluvchi rollarga DM orqali nishon tanlash so'raladi
        actionable = [
            p for p in self.alive_players()
            if p.role and p.role.night_action_type != NightActionType.none
        ]
        for p in actionable:
            await self._send_night_action_prompt(p)

        await asyncio.sleep(NIGHT_SECONDS)
        if self.stopped:
            return
        await self._announce_night_flavor()
        await self._resolve_night_actions()

    async def _kick_inactive_players(self):
        """O'tgan to'liq tun+kun siklida hech qanday harakat qilmagan (tungi harakat ham,
        kunduzgi ovoz ham bermagan) o'yinchilarni o'yindan chetlatadi."""
        to_kick = [p for p in self.alive_players() if not p.acted_this_cycle]
        for p in to_kick:
            p.alive = False
            try:
                await self.bot.send_message(
                    self.chat_id, t("afk_kicked", self.lang, name=mention(p.user_id, p.name))
                )
            except Exception:
                pass

    async def _send_phase_media(self, video_name: str, photo_name: str, caption: str):
        """Video (mp4) yuborishga urinadi, bo'lmasa rasm, u ham bo'lmasa oddiy matn yuboradi."""
        import os
        from aiogram.types import FSInputFile
        base = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
        video_path = os.path.join(base, video_name)
        photo_path = os.path.join(base, photo_name)
        try:
            if os.path.exists(video_path):
                await self.bot.send_video(self.chat_id, FSInputFile(video_path), caption=caption)
                return
        except Exception:
            pass
        try:
            if os.path.exists(photo_path):
                await self.bot.send_photo(self.chat_id, FSInputFile(photo_path), caption=caption)
                return
        except Exception:
            pass
        await self.bot.send_message(self.chat_id, caption)

    # Ma'lum rollar uchun (skrinshotlardagiga o'xshash) individual tungi harakat matnlari.
    # Kalit - rol nomi (kichik harflarda). Admin panelda xohlagan nom bilan rol qo'shishi mumkinligi
    # sababli, bu yerda topilmagan har qanday rol uchun harakat turiga qarab tasodifiy variant tanlanadi.
    ROLE_NIGHT_FLAVOR = {
        "don": "😏 Don o'ljasini tanladi.",
        "mafia": "🔫 Mafiya o'z o'ljasini tanladi.",
        "qotil": "🔪 Qotil pichog'ini charxladi...",
        "komissar katani": "🕵🏼 Komissar katani jinoyatchilarni qidirishda davom etmoqda!",
        "doktor": "💊 Doktor kimningdir uyiga shoshildi.",
        "serjant": "🛡 Serjant o'z postini tark etmadi.",
        "janob": "🎩 Janob soyada kuzatmoqda...",
        "daydi": "🧙‍♂️ Daydi kimnikagidir shisha olish uchun ketdi!",
        "malika": "💃 Malika kimnidir huzuriga chaqirdi.",
        "advokat": "⚖️ Advokat ish qog'ozlarini titkilamoqda.",
        "sehrgar": "🔮 Sehrgar kimnidir uxlatdi...",
        "yollanma qotil": "🥷 Yollanma qotil buyurtmasini bajarishga tayyorlanmoqda.",
        "sotqin": "🐍 Sotqin sirlarni sotmoqda...",
        "aferist": "🃏 Aferist birovni chalg'itmoqda.",
        "g'azabkor": "😡 G'azabkor g'azabini bosolmayapti...",
        "jurnalist": "📰 Jurnalist yangi maqola uchun ma'lumot yig'moqda.",
        "robin gud": "🏹 Robin Gud kimnidir himoya qilishga qaror qildi.",
        "ayg'oqchi": "🔎 Ayg'oqchi kuzatuvda.",
        "qaroqchi": "🗡 Qaroqchi kimningdir cho'ntagini titkilamoqda.",
        "zombi": "🧟 Zombi kimningdir hidini oldi...",
        "hamshira": "👩‍⚕️ Hamshira navbatchilikda.",
        "labarant": "🧪 Labarant probirkalarni tekshirmoqda.",
        "tulki": "🦊 Tulki iziga tushmoqda.",
        "xakker": "💻 Xakker tarmoqqa kirmoqda...",
    }
    ROLE_NIGHT_FLAVOR_BY_ACTION = {
        NightActionType.kill: [
            "🔪 {role} o'z o'ljasini tanladi...",
            "🔪 {role} qorong'ulikda kimnidir poylamoqda...",
        ],
        NightActionType.heal: [
            "🩺 {role} kimningdir mehmoniga keldi...",
            "🩺 {role} shifobaxsh choralar ko'rmoqda...",
        ],
        NightActionType.protect: [
            "🛡 {role} qo'riqlash uchun joy oldi...",
        ],
        NightActionType.check: [
            "🔍 {role} birovni tekshirmoqda...",
            "🔍 {role} shubhalilarni kuzatmoqda...",
        ],
        NightActionType.block: [
            "🌙 {role} kimningdir yo'lini to'smoqda...",
        ],
        NightActionType.revive: [
            "✨ {role} qandaydir sehr bilan band...",
        ],
        NightActionType.custom: [
            "🌙 {role} tunda o'z ishi bilan band edi...",
            "🌙 {role} kimningdir oldiga bordi...",
        ],
    }

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

            custom = self.ROLE_NIGHT_FLAVOR.get(actor.role.name.strip().lower())
            if custom:
                lines.append(custom)
                continue

            action = actor.role.night_action_type
            variants = self.ROLE_NIGHT_FLAVOR_BY_ACTION.get(action)
            if variants:
                template = random.choice(variants)
                lines.append(template.format(role=f"{actor.role.emoji} {actor.role.name}"))

        if lines:
            for line in lines:
                await self.bot.send_message(self.chat_id, line)
                await asyncio.sleep(1.2)

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
        actor = self.players.get(actor_id)
        if actor:
            actor.acted_this_cycle = True

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
        killed_back_attackers = []
        for target_id in kill_targets:
            if target_id in heal_targets:
                continue
            target = self.players.get(target_id)
            if not target or not target.alive:
                continue

            # Do'kondan sotib olingan himoyalar ketma-ketlikda tekshiriladi -- birinchi
            # ishlab turgani (qty>0 va yoqilgan bo'lsa) hujumdan qutqarib qoladi.
            saved_by = None
            for p_type in (
                ProtectionType.qotildan_himoya, ProtectionType.doridan_himoya,
                ProtectionType.qahramon_himoyasi,
            ):
                if await crud.consume_protection(target_id, p_type):
                    saved_by = p_type
                    break

            if saved_by:
                try:
                    await self.bot.send_message(
                        target_id,
                        t("protection_saved_you", self.lang, protection=t(f"protection_name_{saved_by.value}", self.lang)),
                    )
                except Exception:
                    pass
                continue

            # "Miltiq" - hujum qilinganda o'zini otib, hujumchini fosh qilib o'ldiradi
            if await crud.consume_protection(target_id, ProtectionType.miltiq):
                attacker_id = self._find_kill_attacker(target_id)
                if attacker_id:
                    attacker = self.players.get(attacker_id)
                    if attacker and attacker.alive:
                        attacker.alive = False
                        killed_back_attackers.append((target, attacker))
                try:
                    await self.bot.send_message(target_id, t("protection_gun_saved_you", self.lang))
                except Exception:
                    pass
                continue

            target.alive = False
            died.append(target)

        for victim, attacker in killed_back_attackers:
            await self.bot.send_message(
                self.chat_id,
                t(
                    "gun_killed_attacker", self.lang,
                    victim=mention(victim.user_id, victim.name),
                    attacker=mention(attacker.user_id, attacker.name),
                    attacker_role=f"{attacker.role.emoji} {attacker.role.name}" if attacker.role else "",
                ),
            )
            await self._handle_elimination_last_words(attacker, killed_at_night=True)

        # Komissar/tekshiruvchilarga natija yuboriladi (hujjat/sirpanishdan himoya natijani
        # yashiradi yoki soxtalashtiradi)
        for checker_id, target_id in checked_info:
            target = self.players.get(target_id)
            if not target or not target.role:
                continue
            try:
                if await crud.consume_protection(target_id, ProtectionType.sirpanishdan_himoya):
                    await self.bot.send_message(
                        checker_id,
                        f"🔍 Tekshiruv natijasi: {target.name} — {t('investigation_hidden', self.lang)}",
                    )
                    continue
                if await crud.consume_protection(target_id, ProtectionType.hujjat):
                    fake_team = random.choice([tm for tm in ("peaceful", "mafia", "solo") if tm != target.role.team.value])
                    await self.bot.send_message(
                        checker_id,
                        f"🔍 Tekshiruv natijasi: {target.name} — {fake_team.upper()} jamoasidan.",
                    )
                    continue
                await self.bot.send_message(
                    checker_id,
                    f"🔍 Tekshiruv natijasi: {target.name} — {target.role.team.value.upper()} jamoasidan.",
                )
            except Exception:
                pass

        if died:
            await self.bot.send_message(self.chat_id, await self._build_night_deaths_text(died))
            for d in died:
                await self._handle_elimination_last_words(d, killed_at_night=True)
        else:
            await self.bot.send_message(self.chat_id, t("trust_message", self.lang))

    def _find_kill_attacker(self, target_id: int) -> int | None:
        """Shu tunda `target_id` ga qarshi 'kill' harakati qilgan birinchi actor_id ni topadi."""
        for actor_id, tid in self.night_actions.items():
            if tid != target_id:
                continue
            actor = self.players.get(actor_id)
            if actor and actor.role and actor.role.night_action_type == NightActionType.kill:
                return actor_id
        return None

    async def _build_night_deaths_text(self, died: list) -> str:
        """Har bir tunda o'lgan o'yinchi uchun rol nomini va (agar bo'lsa) o'sha kecha unga
        boshqa (o'ldiruvchi bo'lmagan) rol tashrif buyurganini oshkor qiladigan matn tuzadi."""
        from utils.helpers import mention
        lines = [t("night_deaths_title", self.lang)]
        for d in died:
            masked = await crud.consume_protection(d.user_id, ProtectionType.maska)
            role_label = "" if masked else (f"{d.role.emoji} {d.role.name}" if d.role else "")
            line = t("night_death_line", self.lang, role=role_label, name=mention(d.user_id, d.name))

            visitor_id = None
            for actor_id, target_id in self.night_actions.items():
                if target_id != d.user_id or actor_id == d.user_id:
                    continue
                actor = self.players.get(actor_id)
                if not actor or not actor.role or actor.role.night_action_type == NightActionType.kill:
                    continue
                visitor_id = actor_id
                break

            if visitor_id:
                visitor = self.players[visitor_id]
                visitor_label = f"{visitor.role.emoji} {visitor.role.name}" if visitor.role else "??"
                line += " " + t("night_death_visitor", self.lang, visitor_role=visitor_label)
            lines.append(line)
        return "\n".join(lines)

    # -------------------------------------------------------------------
    # KUN (muhokama + nominatsiya + ovoz berish)
    # -------------------------------------------------------------------
    async def run_day_phase(self):
        self.phase = "day"
        day_text = t("day_started", self.lang, day_number=self.day_number)
        await self._send_phase_media("day.mp4", "day.png", day_text)
        await self.bot.send_message(self.chat_id, self._day_roster_and_teams_text())
        await asyncio.sleep(min(DAY_DISCUSSION_SECONDS, 5))  # muhokama vaqti (qisqartirilgan demo)
        if self.stopped:
            return

        if len(self.alive_players()) <= 1:
            return

        nominee = await self._run_nomination_phase()
        if self.stopped:
            return
        if not nominee or not nominee.alive:
            self.current_nominee = None
            return

        self.current_nominee = nominee.user_id

        self.votes.clear()
        builder = InlineKeyboardBuilder()
        builder.button(text="👍 0", callback_data=f"vote_like:{self.chat_id}")
        builder.button(text="👎 0", callback_data=f"vote_dislike:{self.chat_id}")
        builder.adjust(2)

        go_to_bot_kb = InlineKeyboardBuilder()
        go_to_bot_kb.button(text="🤖 Botga o'tish", url=f"https://t.me/{config.BOT_USERNAME}")
        keyboard = builder.as_markup()
        keyboard.inline_keyboard += go_to_bot_kb.as_markup().inline_keyboard

        vote_msg = await self.bot.send_message(
            self.chat_id,
            f"⚖️ {mention(nominee.user_id, nominee.name)} nomzod bo'ldi!\n" + t("voting_started", self.lang, seconds=VOTING_SECONDS),
            reply_markup=keyboard,
        )
        self.vote_message_id = vote_msg.message_id

        await asyncio.sleep(VOTING_SECONDS)
        if self.stopped:
            return

        likes = sum(1 for v in self.votes.values() if v == "like")
        dislikes = sum(1 for v in self.votes.values() if v == "dislike")
        self.vote_message_id = None

        if likes == dislikes:
            await self.bot.send_message(self.chat_id, t("vote_tie", self.lang, likes=likes, dislikes=dislikes))
        else:
            await self.bot.send_message(self.chat_id, t("vote_result", self.lang, likes=likes, dislikes=dislikes))

        if likes > dislikes:
            if await crud.consume_protection(nominee.user_id, ProtectionType.osishdan_himoya):
                await self.bot.send_message(
                    self.chat_id,
                    t("protection_hanging_saved", self.lang, name=mention(nominee.user_id, nominee.name)),
                )
            else:
                nominee.alive = False
                if await crud.consume_protection(nominee.user_id, ProtectionType.maska):
                    await self.bot.send_message(
                        self.chat_id,
                        t("player_hanged_masked", self.lang, name=mention(nominee.user_id, nominee.name)),
                    )
                else:
                    await self.bot.send_message(
                        self.chat_id,
                        t("player_hanged", self.lang, name=mention(nominee.user_id, nominee.name), role_emoji=nominee.role.emoji, role_name=nominee.role.name),
                    )
                await self._handle_elimination_last_words(nominee, killed_at_night=False)

        self.current_nominee = None

    def _day_roster_and_teams_text(self) -> str:
        from utils.helpers import mention
        alive = self.alive_players()
        numbered = "\n".join(f"{i+1}. {mention(p.user_id, p.name)}" for i, p in enumerate(alive))

        team_labels = {"peaceful": "Tinchlar", "mafia": "Mafiyalar", "solo": "Yakkalar"}
        grouped: dict[str, list] = {}
        for p in alive:
            key = p.role.team.value if p.role else "peaceful"
            grouped.setdefault(key, []).append(p)

        team_blocks = []
        for key in ("peaceful", "mafia", "solo"):
            members = grouped.get(key)
            if not members:
                continue
            names = ", ".join(f"{p.role.emoji} {mention(p.user_id, p.name)}" for p in members)
            team_blocks.append(f"<b>{team_labels[key]} - {len(members)}:</b>\n{names}")

        return (
            f"👥 <b>O'yinchilar ro'yxati</b>\n━━━━━━━━━━━━━━\n{numbered}\n\n"
            + "\n\n".join(team_blocks)
            + f"\n\n📊 Jami: <b>{len(alive)}</b> ta o'yinchi\n\n"
            + "☀️ Kunduzgi munozara vaqti. O'yinchilar o'z fikrlarini bildirishlari mumkin."
        )

    async def _run_nomination_phase(self) -> PlayerState | None:
        """Har bir tirik o'yinchi botdagi shaxsiy chatda kimga ovoz berishini tanlaydi."""
        alive = self.alive_players()
        if len(alive) < 2:
            return None

        self.nominations.clear()
        self.nomination_open = True

        for voter in alive:
            builder = InlineKeyboardBuilder()
            for target in alive:
                if target.user_id == voter.user_id:
                    continue
                builder.button(text=target.name, callback_data=f"nominate:{self.chat_id}:{target.user_id}")
            builder.adjust(1)
            try:
                await self.bot.send_message(
                    voter.user_id,
                    "🗳 Bu kunda kimga ovoz berasiz?",
                    reply_markup=builder.as_markup(),
                )
            except Exception:
                pass

        await self.bot.send_message(
            self.chat_id,
            f"🗳 Ovoz berish boshlandi! Har bir o'yinchi botdagi shaxsiy xabarga javob bersin. "
            f"({VOTING_SECONDS} soniya)",
        )

        await asyncio.sleep(VOTING_SECONDS)
        self.nomination_open = False

        if not self.nominations:
            await self.bot.send_message(self.chat_id, "🤐 Hech kim ovoz bermadi. Bugun hech kim jazolanmadi.")
            return None

        tally: dict[int, int] = {}
        for nominee_id in self.nominations.values():
            tally[nominee_id] = tally.get(nominee_id, 0) + 1
        max_votes = max(tally.values())

        if max_votes < 2 and len(tally) > 1:
            # hamma turli odamga ovoz berdi -- kelisha olishmadi
            await self.bot.send_message(
                self.chat_id,
                "🤷 <b>Ovoz berish yakunlandi:</b>\n"
                "Axoli kelisha olmadi... Kelisha olmaslik oqibatida xech kim osilmadi...",
            )
            return None

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
        voter = self.players.get(voter_id)
        if voter:
            voter.acted_this_cycle = True
        return True

    def register_vote(self, voter_id: int, choice: str):
        if voter_id not in self.alive_ids():
            return False
        self.votes[voter_id] = choice
        voter = self.players.get(voter_id)
        if voter:
            voter.acted_this_cycle = True
        return True

    async def refresh_vote_counts(self):
        """Like/dislike tugmalaridagi sonlarni jonli yangilaydi."""
        if not self.vote_message_id:
            return
        likes = sum(1 for v in self.votes.values() if v == "like")
        dislikes = sum(1 for v in self.votes.values() if v == "dislike")
        builder = InlineKeyboardBuilder()
        builder.button(text=f"👍 {likes}", callback_data=f"vote_like:{self.chat_id}")
        builder.button(text=f"👎 {dislikes}", callback_data=f"vote_dislike:{self.chat_id}")
        builder.adjust(2)
        try:
            await self.bot.edit_message_reply_markup(
                chat_id=self.chat_id, message_id=self.vote_message_id, reply_markup=builder.as_markup()
            )
        except Exception:
            pass

    # -------------------------------------------------------------------
    # OXIRGI SO'Z (endi guruhda emas — o'yinchining botdagi shaxsiy chatida yoziladi)
    # -------------------------------------------------------------------
    async def _handle_elimination_last_words(self, player: PlayerState, killed_at_night: bool):
        from handlers.group.registration import LAST_WORDS_LISTENERS
        from utils.helpers import mention

        dm_sent = True
        try:
            await self.bot.send_message(
                player.user_id,
                t("last_words_prompt_dm", self.lang, seconds=LAST_WORDS_SECONDS),
            )
        except Exception:
            dm_sent = False

        await self.bot.send_message(
            self.chat_id, t("last_words_wait_group", self.lang, name=mention(player.user_id, player.name))
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
            self.chat_id, t("last_words_announced", self.lang, name=mention(player.user_id, player.name), words=words)
        )

    # -------------------------------------------------------------------
    # O'YIN TUGASHI
    # -------------------------------------------------------------------
    async def finish_game(self, winner_team: str):
        self.phase = "finished"
        self.stopped = True
        await crud.finish_game(self.session_id)

        winners = [p for p in self.players.values() if p.role and p.role.team.value == winner_team]
        others = [p for p in self.players.values() if p not in winners]

        winners_text = "\n".join(f"{i+1}. {mention(p.user_id, p.name)} — {p.role.emoji} {p.role.name}" for i, p in enumerate(winners))
        others_text = "\n".join(f"{i+1}. {mention(p.user_id, p.name)} — {p.role.emoji} {p.role.name}" for i, p in enumerate(others))

        news_channel = await crud.get_setting("news_channel", "@AgencyMafiaa")

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
