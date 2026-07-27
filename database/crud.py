"""
Ma'lumotlar bazasi bilan ishlash uchun barcha yordamchi (CRUD) funksiyalar.
Har bir funksiya o'zi session ochadi va yopadi - handlerlarda to'g'ridan-to'g'ri
`await crud.get_user(...)` kabi chaqiriladi.
"""
from datetime import date, datetime
from sqlalchemy import select, update, delete, func
from sqlalchemy.exc import IntegrityError

from database.db import async_session
from database.models import (
    User, ShopItem, Hero, UserHero, Role, PremiumGroup, MoneyPackage,
    DiamondPackage, DiamondTopupRequest, PartnerRequest, BotSetting,
    AdminUser, GameSession, GamePlayer, RewardSettings, GroupSetting, GameMode,
    GenderEnum, ProtectionType, DiamondRequestStatus, GameStatus,
)


async def _safe_delete(model, row_id: int) -> str:
    """
    Berilgan qatorni o'chirishga urinadi. Agar bu qator boshqa jadvalda
    (masalan o'ynalgan o'yinlar tarixida) ishlatilgan bo'lsa va shu sabab
    bazadan butunlay o'chirib bo'lmasa (FK cheklovi xatoligi), uni butunlay
    o'chirish o'rniga "is_active=False" qilib nofaollashtiradi - shunda u
    foydalanuvchilarga hech qayerda ko'rinmaydi, lekin eski tarix buzilmaydi.

    Qaytaradi: "deleted" | "deactivated" | "not_found"
    """
    async with async_session() as s:
        obj = await s.get(model, row_id)
        if obj is None:
            return "not_found"
        try:
            await s.delete(obj)
            await s.commit()
            return "deleted"
        except IntegrityError:
            await s.rollback()

    # Butunlay o'chira olmadik (boshqa joyda ishlatilgan) -> nofaollashtiramiz
    async with async_session() as s:
        obj = await s.get(model, row_id)
        if obj is None:
            return "not_found"
        if hasattr(obj, "is_active"):
            obj.is_active = False
            await s.commit()
            return "deactivated"
        # is_active maydoni yo'q bo'lsa, iloji yo'q - xatolikni yuqoriga uzatamiz
        raise


# ---------------------------------------------------------------------------
# USER
# ---------------------------------------------------------------------------
async def get_user(user_id: int) -> User | None:
    async with async_session() as s:
        return await s.get(User, user_id)


async def get_or_create_user(user_id: int, username: str | None, first_name: str | None) -> tuple[User, bool]:
    async with async_session() as s:
        user = await s.get(User, user_id)
        created = False
        if user is None:
            user = User(id=user_id, username=username, first_name=first_name)
            s.add(user)
            created = True
        else:
            user.username = username
            user.first_name = first_name
        await s.commit()
        await s.refresh(user)
        return user, created


async def set_user_language(user_id: int, lang: str):
    async with async_session() as s:
        await s.execute(update(User).where(User.id == user_id).values(language=lang))
        await s.commit()


async def set_user_gender(user_id: int, gender: GenderEnum, increment_change: bool = False):
    async with async_session() as s:
        user = await s.get(User, user_id)
        user.gender = gender
        if increment_change:
            user.gender_change_count += 1
        await s.commit()


async def update_user_balance(user_id: int, money_delta: int = 0, diamond_delta: int = 0):
    async with async_session() as s:
        user = await s.get(User, user_id)
        user.money = max(0, user.money + money_delta)
        user.diamonds = max(0, user.diamonds + diamond_delta)
        await s.commit()
        return user


async def get_group_language(chat_id: int) -> str:
    async with async_session() as s:
        row = await s.get(GroupSetting, chat_id)
        return row.language if row else "uz"


async def set_group_language(chat_id: int, language: str):
    async with async_session() as s:
        row = await s.get(GroupSetting, chat_id)
        if row:
            row.language = language
        else:
            s.add(GroupSetting(chat_id=chat_id, language=language))
        await s.commit()


async def toggle_protection(user_id: int, protection_field: str):
    """protection_field masalan 'himoya_on', 'miltiq_on' va h.k."""
    async with async_session() as s:
        user = await s.get(User, user_id)
        current = getattr(user, protection_field)
        setattr(user, protection_field, not current)
        await s.commit()
        return not current


async def add_protection_qty(user_id: int, protection: ProtectionType, qty: int = 1):
    field = f"{protection.value}_qty"
    async with async_session() as s:
        user = await s.get(User, user_id)
        setattr(user, field, getattr(user, field) + qty)
        await s.commit()


async def consume_protection(user_id: int, protection: ProtectionType) -> bool:
    """O'yin davomida himoyani ishlatish - agar ON va qty > 0 bo'lsa, 1 ta ayiradi va True qaytaradi."""
    field_qty = f"{protection.value}_qty"
    field_on = f"{protection.value}_on"
    async with async_session() as s:
        user = await s.get(User, user_id)
        if not user:
            return False
        if getattr(user, field_on) and getattr(user, field_qty) > 0:
            setattr(user, field_qty, getattr(user, field_qty) - 1)
            await s.commit()
            return True
        return False


async def can_use_free_random_money(user_id: int, daily_limit: int) -> tuple[bool, int]:
    async with async_session() as s:
        user = await s.get(User, user_id)
        today = date.today()
        if user.free_random_money_date != today:
            return True, daily_limit
        remaining = daily_limit - user.free_random_money_used_today
        return remaining > 0, remaining


async def use_free_random_money(user_id: int, amount: int):
    async with async_session() as s:
        user = await s.get(User, user_id)
        today = date.today()
        if user.free_random_money_date != today:
            user.free_random_money_date = today
            user.free_random_money_used_today = 0
        user.free_random_money_used_today += 1
        user.money += amount
        await s.commit()


async def search_user_by_id(user_id: int) -> User | None:
    return await get_user(user_id)


async def get_all_user_ids() -> list[int]:
    async with async_session() as s:
        res = await s.execute(select(User.id))
        return [r[0] for r in res.all()]


async def get_stats_overview() -> dict:
    async with async_session() as s:
        total_users = (await s.execute(select(func.count(User.id)))).scalar()
        total_money = (await s.execute(select(func.sum(User.money)))).scalar() or 0
        total_diamonds = (await s.execute(select(func.sum(User.diamonds)))).scalar() or 0
        total_games = (await s.execute(select(func.sum(User.total_games)))).scalar() or 0
        return {
            "total_users": total_users,
            "total_money": total_money,
            "total_diamonds": total_diamonds,
            "total_games": total_games,
        }


# ---------------------------------------------------------------------------
# SHOP (Do'kon / Himoyalar)
# ---------------------------------------------------------------------------
async def get_shop_items(category: str | None = None, active_only: bool = True) -> list[ShopItem]:
    async with async_session() as s:
        q = select(ShopItem)
        if category:
            q = q.where(ShopItem.category == category)
        if active_only:
            q = q.where(ShopItem.is_active == True)  # noqa: E712
        res = await s.execute(q)
        return list(res.scalars().all())


async def get_shop_item(item_id: int) -> ShopItem | None:
    async with async_session() as s:
        return await s.get(ShopItem, item_id)


async def create_shop_item(**kwargs) -> ShopItem:
    async with async_session() as s:
        item = ShopItem(**kwargs)
        s.add(item)
        await s.commit()
        await s.refresh(item)
        return item


async def delete_shop_item(item_id: int) -> str:
    return await _safe_delete(ShopItem, item_id)


async def purchase_shop_item(user_id: int, item: ShopItem, pay_with: str = "money") -> bool:
    """pay_with: 'money' yoki 'diamond'. Foydalanuvchi hisobidan yechib, qty ni oshiradi."""
    async with async_session() as s:
        user = await s.get(User, user_id)
        price = item.price_money if pay_with == "money" else item.price_diamond
        balance = user.money if pay_with == "money" else user.diamonds
        if balance < price:
            return False
        if pay_with == "money":
            user.money -= price
        else:
            user.diamonds -= price
        field = f"{item.protection_type.value}_qty"
        setattr(user, field, getattr(user, field) + 1)
        await s.commit()
        return True


# ---------------------------------------------------------------------------
# HEROES (Geroylar)
# ---------------------------------------------------------------------------
async def get_heroes(active_only: bool = True) -> list[Hero]:
    async with async_session() as s:
        q = select(Hero)
        if active_only:
            q = q.where(Hero.is_active == True)  # noqa: E712
        res = await s.execute(q)
        return list(res.scalars().all())


async def get_hero(hero_id: int) -> Hero | None:
    async with async_session() as s:
        return await s.get(Hero, hero_id)


async def create_hero(**kwargs) -> Hero:
    async with async_session() as s:
        hero = Hero(**kwargs)
        s.add(hero)
        await s.commit()
        await s.refresh(hero)
        return hero


async def delete_hero(hero_id: int) -> str:
    # Bu geroyni "faol geroy" qilib tanlagan foydalanuvchilar bo'lsa, avval
    # ularni bo'shatib qo'yamiz (aks holda FK xatoligi chiqadi).
    async with async_session() as s:
        await s.execute(
            update(User).where(User.active_hero_id == hero_id).values(active_hero_id=None)
        )
        await s.commit()
    # Agar kimdir bu geroyni sotib olgan bo'lsa (user_heroes jadvalida), butunlay
    # o'chirib bo'lmaydi - shu holda nofaollashtirilib qo'yiladi (_safe_delete ichida).
    return await _safe_delete(Hero, hero_id)


async def get_user_heroes(user_id: int) -> list[Hero]:
    async with async_session() as s:
        res = await s.execute(
            select(Hero).join(UserHero, UserHero.hero_id == Hero.id).where(UserHero.user_id == user_id)
        )
        return list(res.scalars().all())


async def user_owns_hero(user_id: int, hero_id: int) -> bool:
    async with async_session() as s:
        res = await s.execute(
            select(UserHero).where(UserHero.user_id == user_id, UserHero.hero_id == hero_id)
        )
        return res.scalar_one_or_none() is not None


async def buy_hero(user_id: int, hero: Hero, pay_with: str = "diamond") -> bool:
    async with async_session() as s:
        user = await s.get(User, user_id)
        price = hero.price_diamond if pay_with == "diamond" else hero.price_stars
        if pay_with == "diamond":
            if user.diamonds < price:
                return False
            user.diamonds -= price
        s.add(UserHero(user_id=user_id, hero_id=hero.id))
        await s.commit()
        return True


async def set_active_hero(user_id: int, hero_id: int | None):
    async with async_session() as s:
        user = await s.get(User, user_id)
        user.active_hero_id = hero_id
        await s.commit()


# ---------------------------------------------------------------------------
# ROLES (Rollar)
# ---------------------------------------------------------------------------
async def get_roles(active_only: bool = True, mode: str | None = None) -> list[Role]:
    async with async_session() as s:
        q = select(Role).order_by(Role.priority)
        if active_only:
            q = q.where(Role.is_active == True)  # noqa: E712
        if mode:
            # func.lower() bilan solishtiramiz -- aks holda admin rol qo'shganda mode
            # matnini (masalan "Classic" o'rniga "classic") biroz boshqacha yozsa, bu rol
            # HECH QACHON o'yinga tanlanmay, sababsiz "hamma tinch aholi" bo'lib chiqishi mumkin.
            q = q.where(func.lower(Role.mode) == mode.strip().lower())
        res = await s.execute(q)
        return list(res.scalars().all())


async def get_role(role_id: int) -> Role | None:
    async with async_session() as s:
        return await s.get(Role, role_id)


async def get_purchasable_roles() -> list[Role]:
    """Do'kondan sotib olish mumkin bo'lgan (price_diamond > 0) faol rollar ro'yxati."""
    async with async_session() as s:
        res = await s.execute(
            select(Role).where(Role.is_active == True, Role.price_diamond > 0).order_by(Role.priority)  # noqa: E712
        )
        return list(res.scalars().all())


async def reserve_role(user_id: int, role_id: int) -> str:
    """Foydalanuvchi rolni olmosga sotib olib, KEYINGI o'yin uchun band qiladi.
    Bir nechta foydalanuvchi bir xil rolni sotib olishi/band qilishi mumkin
    (masalan hammasi "Don"ni tanlashi mumkin) — bu yerda cheklanmaydi. Amalda
    kim o'sha o'yinda shu roldan foydalanishi (max_per_game chegarasi) o'yin
    boshlanganda, game/roles_logic.py -> assign_roles() ichida hal qilinadi:
    bitta o'yinda faqat max_per_game tagacha kishi o'z band qilgan rolini
    oladi, qolganlari esa oddiy tasodifiy taqsimotga tushadi.
    Qaytaradi: "ok" | "not_found" | "not_purchasable" | "insufficient" | "already_reserved" """
    async with async_session() as s:
        role = await s.get(Role, role_id)
        if not role or not role.is_active:
            return "not_found"
        if role.price_diamond <= 0:
            return "not_purchasable"
        user = await s.get(User, user_id)
        if not user:
            return "insufficient"
        if user.reserved_role_id == role.id:
            # Foydalanuvchi bu rolni allaqachon band qilgan — qayta bosilsa ham
            # ikkinchi marta olmos yechilmasligi kerak.
            return "already_reserved"
        if user.diamonds < role.price_diamond:
            return "insufficient"
        user.diamonds -= role.price_diamond
        user.reserved_role_id = role.id
        await s.commit()
        return "ok"


async def count_role_reservations(role_id: int) -> int:
    """Hozirda ushbu rolni "Faol rol" sifatida band qilib turgan foydalanuvchilar soni
    (faqat ma'lumot sifatida ko'rsatish uchun - sotib olishni cheklamaydi)."""
    async with async_session() as s:
        res = await s.execute(
            select(func.count()).select_from(User).where(User.reserved_role_id == role_id)
        )
        return res.scalar() or 0


async def clear_reserved_role(user_id: int):
    async with async_session() as s:
        user = await s.get(User, user_id)
        if user:
            user.reserved_role_id = None
            await s.commit()


async def get_reserved_roles(user_ids: list[int]) -> dict[int, Role]:
    """Berilgan o'yinchilardan qaysilari "Faol rol" band qilganini {user_id: Role} qilib qaytaradi."""
    if not user_ids:
        return {}
    async with async_session() as s:
        res = await s.execute(select(User).where(User.id.in_(user_ids), User.reserved_role_id.isnot(None)))
        users = res.scalars().all()
        result: dict[int, Role] = {}
        for u in users:
            role = await s.get(Role, u.reserved_role_id)
            if role and role.is_active:
                result[u.id] = role
        return result


async def create_role(**kwargs) -> Role:
    async with async_session() as s:
        role = Role(**kwargs)
        s.add(role)
        await s.commit()
        await s.refresh(role)
        return role


async def update_role(role_id: int, **kwargs) -> Role | None:
    async with async_session() as s:
        role = await s.get(Role, role_id)
        if not role:
            return None
        for key, value in kwargs.items():
            setattr(role, key, value)
        await s.commit()
        await s.refresh(role)
        return role


async def delete_role(role_id: int) -> str:
    async with async_session() as s:
        # Eski o'yinlarda shu rol bilan o'ynagan qatorlar bo'lsa, ularni
        # bo'shatib qo'yamiz (aks holda FK xatoligi bilan o'chirilmay qoladi).
        await s.execute(
            update(GamePlayer).where(GamePlayer.role_id == role_id).values(role_id=None)
        )
        # Boshqa rollar shu rolni "meros" sifatida ko'rsatgan bo'lsa, ularni ham tozalaymiz.
        await s.execute(
            update(Role).where(Role.succeeds_role_id == role_id).values(succeeds_role_id=None)
        )
        await s.execute(delete(Role).where(Role.id == role_id))
        await s.commit()
    return "deleted"


# ---------------------------------------------------------------------------
# O'YIN REJIMLARI
# ---------------------------------------------------------------------------
async def get_game_modes(active_only: bool = True) -> list[GameMode]:
    async with async_session() as s:
        q = select(GameMode).order_by(GameMode.min_players)
        if active_only:
            q = q.where(GameMode.is_active == True)  # noqa: E712
        res = await s.execute(q)
        return list(res.scalars().all())


async def create_game_mode(**kwargs) -> GameMode:
    async with async_session() as s:
        gm = GameMode(**kwargs)
        s.add(gm)
        await s.commit()
        await s.refresh(gm)
        return gm


async def delete_game_mode(mode_id: int) -> str:
    return await _safe_delete(GameMode, mode_id)


async def get_mode_for_player_count(count: int) -> str:
    """Berilgan o'yinchilar soniga mos rejimni topadi. Topilmasa "classic" ga qaytadi."""
    modes = await get_game_modes(active_only=True)
    for m in modes:
        if m.min_players <= count <= m.max_players:
            return m.name
    return "classic"


# ---------------------------------------------------------------------------
# PREMIUM GURUHLAR
# ---------------------------------------------------------------------------
async def get_premium_groups(country_code: str, active_only: bool = True) -> list[PremiumGroup]:
    async with async_session() as s:
        q = select(PremiumGroup).where(PremiumGroup.country_code == country_code)
        if active_only:
            q = q.where(PremiumGroup.is_active == True)  # noqa: E712
        q = q.order_by(PremiumGroup.diamond_rank.desc())
        res = await s.execute(q)
        return list(res.scalars().all())


async def create_premium_group(**kwargs) -> PremiumGroup:
    async with async_session() as s:
        pg = PremiumGroup(**kwargs)
        s.add(pg)
        await s.commit()
        await s.refresh(pg)
        return pg


async def delete_premium_group(pg_id: int) -> str:
    return await _safe_delete(PremiumGroup, pg_id)


# ---------------------------------------------------------------------------
# PUL / OLMOS PAKETLARI
# ---------------------------------------------------------------------------
async def get_money_packages(active_only: bool = True) -> list[MoneyPackage]:
    async with async_session() as s:
        q = select(MoneyPackage)
        if active_only:
            q = q.where(MoneyPackage.is_active == True)  # noqa: E712
        res = await s.execute(q)
        return list(res.scalars().all())


async def create_money_package(**kwargs) -> MoneyPackage:
    async with async_session() as s:
        p = MoneyPackage(**kwargs)
        s.add(p)
        await s.commit()
        await s.refresh(p)
        return p


async def delete_money_package(pkg_id: int) -> str:
    return await _safe_delete(MoneyPackage, pkg_id)


async def get_diamond_packages(active_only: bool = True) -> list[DiamondPackage]:
    async with async_session() as s:
        q = select(DiamondPackage)
        if active_only:
            q = q.where(DiamondPackage.is_active == True)  # noqa: E712
        res = await s.execute(q)
        return list(res.scalars().all())


async def create_diamond_package(**kwargs) -> DiamondPackage:
    async with async_session() as s:
        p = DiamondPackage(**kwargs)
        s.add(p)
        await s.commit()
        await s.refresh(p)
        return p


async def delete_diamond_package(pkg_id: int) -> str:
    return await _safe_delete(DiamondPackage, pkg_id)


async def create_diamond_topup_request(user_id: int, package_id: int, receipt_file_id: str) -> DiamondTopupRequest:
    async with async_session() as s:
        req = DiamondTopupRequest(user_id=user_id, package_id=package_id, receipt_file_id=receipt_file_id)
        s.add(req)
        await s.commit()
        await s.refresh(req)
        return req


async def get_diamond_request(req_id: int) -> DiamondTopupRequest | None:
    async with async_session() as s:
        return await s.get(DiamondTopupRequest, req_id)


async def review_diamond_request(req_id: int, approve: bool, admin_id: int) -> DiamondTopupRequest | None:
    async with async_session() as s:
        req = await s.get(DiamondTopupRequest, req_id)
        if not req or req.status != DiamondRequestStatus.pending:
            return None
        req.status = DiamondRequestStatus.approved if approve else DiamondRequestStatus.rejected
        req.reviewed_by = admin_id
        req.reviewed_at = datetime.utcnow()
        if approve:
            pkg = await s.get(DiamondPackage, req.package_id)
            user = await s.get(User, req.user_id)
            user.diamonds += pkg.diamond_amount
        await s.commit()
        await s.refresh(req)
        return req


# ---------------------------------------------------------------------------
# PARA (JUFTLIK)
# ---------------------------------------------------------------------------
async def create_partner_request(from_id: int, to_id: int) -> PartnerRequest:
    async with async_session() as s:
        req = PartnerRequest(from_user_id=from_id, to_user_id=to_id)
        s.add(req)
        await s.commit()
        await s.refresh(req)
        return req


async def resolve_partner_request(req_id: int, accept: bool) -> PartnerRequest | None:
    async with async_session() as s:
        req = await s.get(PartnerRequest, req_id)
        if not req:
            return None
        req.status = "accepted" if accept else "declined"
        if accept:
            u1 = await s.get(User, req.from_user_id)
            u2 = await s.get(User, req.to_user_id)
            u1.partner_id = u2.id
            u2.partner_id = u1.id
        await s.commit()
        await s.refresh(req)
        return req


async def find_random_partner_candidate(user_id: int, opposite_gender: GenderEnum) -> User | None:
    """Berilgan jinsga qarama-qarshi, hali jufti yo'q, tasodifiy foydalanuvchi topadi."""
    async with async_session() as s:
        res = await s.execute(
            select(User)
            .where(
                User.gender == opposite_gender,
                User.partner_id.is_(None),
                User.id != user_id,
                User.is_banned == False,  # noqa: E712
            )
            .order_by(func.random())
            .limit(1)
        )
        return res.scalar_one_or_none()


# ---------------------------------------------------------------------------
# ADMIN / SOZLAMALAR
# ---------------------------------------------------------------------------
async def is_admin(user_id: int, super_admins: list[int]) -> bool:
    if user_id in super_admins:
        return True
    async with async_session() as s:
        res = await s.get(AdminUser, user_id)
        return res is not None


async def add_admin(user_id: int, added_by: int):
    async with async_session() as s:
        existing = await s.get(AdminUser, user_id)
        if not existing:
            s.add(AdminUser(user_id=user_id, added_by=added_by))
            await s.commit()


async def remove_admin(user_id: int):
    async with async_session() as s:
        await s.execute(delete(AdminUser).where(AdminUser.user_id == user_id))
        await s.commit()


async def get_setting(key: str, default: str | None = None) -> str | None:
    async with async_session() as s:
        row = await s.get(BotSetting, key)
        return row.value if row else default


async def set_setting(key: str, value: str):
    async with async_session() as s:
        row = await s.get(BotSetting, key)
        if row:
            row.value = value
        else:
            s.add(BotSetting(key=key, value=value))
        await s.commit()


async def get_reward_settings() -> RewardSettings:
    async with async_session() as s:
        row = await s.get(RewardSettings, 1)
        if not row:
            row = RewardSettings(id=1)
            s.add(row)
            await s.commit()
            await s.refresh(row)
        return row


async def update_reward_settings(**kwargs):
    async with async_session() as s:
        row = await s.get(RewardSettings, 1)
        if not row:
            row = RewardSettings(id=1)
            s.add(row)
        for k, v in kwargs.items():
            setattr(row, k, v)
        await s.commit()


async def get_top_users_by_money(limit: int = 10) -> list[User]:
    async with async_session() as s:
        res = await s.execute(select(User).order_by(User.money.desc()).limit(limit))
        return list(res.scalars().all())


async def get_top_users_by_diamonds(limit: int = 10) -> list[User]:
    async with async_session() as s:
        res = await s.execute(select(User).order_by(User.diamonds.desc()).limit(limit))
        return list(res.scalars().all())


# ---------------------------------------------------------------------------
# O'YIN SESSIYASI
# ---------------------------------------------------------------------------
async def create_game_session(chat_id: int, created_by: int) -> GameSession:
    async with async_session() as s:
        session_obj = GameSession(chat_id=chat_id, created_by=created_by)
        s.add(session_obj)
        await s.commit()
        await s.refresh(session_obj)
        return session_obj


async def add_game_player(session_id: int, user_id: int, display_name: str) -> GamePlayer | None:
    async with async_session() as s:
        existing = await s.execute(
            select(GamePlayer).where(GamePlayer.session_id == session_id, GamePlayer.user_id == user_id)
        )
        if existing.scalar_one_or_none():
            return None
        gp = GamePlayer(session_id=session_id, user_id=user_id, display_name=display_name)
        s.add(gp)
        await s.commit()
        await s.refresh(gp)
        return gp


async def get_game_players(session_id: int) -> list[GamePlayer]:
    async with async_session() as s:
        res = await s.execute(select(GamePlayer).where(GamePlayer.session_id == session_id))
        return list(res.scalars().all())


async def update_game_status(session_id: int, status: GameStatus):
    async with async_session() as s:
        await s.execute(update(GameSession).where(GameSession.id == session_id).values(status=status))
        await s.commit()


async def finish_game(session_id: int):
    async with async_session() as s:
        await s.execute(
            update(GameSession)
            .where(GameSession.id == session_id)
            .values(status=GameStatus.finished, ended_at=datetime.utcnow())
        )
        await s.commit()


async def apply_game_result(user_id: int, won: bool):
    """O'yin tugagach - statistika va mukofot berish."""
    reward = await get_reward_settings()
    async with async_session() as s:
        user = await s.get(User, user_id)
        user.total_games += 1
        if won:
            user.wins += 1
            user.money += reward.winner_money
            user.diamonds += reward.winner_diamond
        else:
            user.money += reward.loser_money
            user.diamonds += reward.loser_diamond
        await s.commit()
        return user
