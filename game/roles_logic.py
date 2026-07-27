"""O'yinchilarga rollarni tasodifiy taqsimlash logikasi."""
import random

from database.models import Role, RoleTeam


def assign_roles(player_ids: list[int], roles: list[Role], preassigned: dict[int, Role] | None = None) -> dict[int, Role]:
    """
    player_ids - o'yinga qo'shilgan foydalanuvchilar ro'yxati.
    roles - admin panelda sozlangan barcha faol rollar.
    preassigned - {user_id: Role} - do'kondan "Faol rol" sifatida oldindan sotib olib,
        shu o'yin uchun band qilingan rollar (agar bo'lsa). Bu o'yinchilarga ENG AVVAL
        o'sha rol beriladi, keyin qolganlarga oddiy tasodifiy taqsimot davom etadi.

    Qaytaradi: {user_id: Role}

    Mantiq:
      - Har bir maxsus rol (mafia/solo/peaceful maxsus) min_players_required shartiga mos bo'lsa
        va max_per_game chegarasida random tarzda taqsimlanadi.
      - Qolgan o'yinchilarga "oddiy" mafia yoki tinch aholi (agar maxsus rol yo'q bo'lsa) beriladi.
      - Mafiya soni umumiy o'yinchilarning ~1/4 qismi atrofida bo'ladi (agar admin buni
        aniq sozlamagan bo'lsa ham, o'yin muvozanatli bo'lishi uchun).
    """
    n = len(player_ids)
    shuffled_players = player_ids[:]
    random.shuffle(shuffled_players)

    assignment: dict[int, Role] = {}
    max_mafia = max(1, n // 4)
    mafia_assigned = 0

    # 1) Avval oldindan sotib olingan ("Faol rol") o'yinchilarni joylashtiramiz --
    # ularning sotib olgan roli KAFOLATLI beriladi, LEKIN faqat rol.max_per_game
    # chegarasi ichida. Bir nechta o'yinchi bitta rolni (masalan max_per_game=1
    # bo'lgan "Don") oldindan band qilgan bo'lishi mumkin - ular hammasi sotib
    # ola oladi, lekin bitta o'yinda faqat max_per_game tasi haqiqatan shu
    # rolni oladi (tasodifiy tanlanadi), qolganlari esa pastdagi oddiy
    # tasodifiy taqsimotga tushadi - shunda bitta o'yinda 2 ta Don paydo bo'lmaydi.
    used_slots: dict[int, int] = {}  # role.id -> shu o'yinda nechta joy band qilindi
    remaining_players: list[int] = []
    preassigned = preassigned or {}
    for uid in shuffled_players:
        role = preassigned.get(uid)
        if role and role.is_active and role.id and role.id > 0:
            cap = max(role.max_per_game, 1)
            if used_slots.get(role.id, 0) < cap:
                assignment[uid] = role
                used_slots[role.id] = used_slots.get(role.id, 0) + 1
                if role.team == RoleTeam.mafia:
                    mafia_assigned += 1
                continue
        remaining_players.append(uid)
    # Sotib olingan mafiya rollari balans chegarasidan (n//4) oshib ketsa ham, pulini
    # to'lagan o'yinchining roli olib qo'yilmaydi - shu sabab chegarani moslashtiramiz.
    max_mafia = max(max_mafia, mafia_assigned)

    idx = 0

    # MUHIM TUZATISH: oldin barcha rollar (kam sonli maxsus rollar HAM, ko'p sonli
    # to'ldiruvchi rollar HAM, masalan max_per_game=999 bo'lgan "Tinch aholi") bitta
    # ro'yxatga yig'ilib, ARALASH holda aralashtirilib, ketma-ket taqsimlanardi. Natijada
    # ko'p sonli to'ldiruvchi rol statistik jihatdan ustunlik qilib, Doktor/Komissar kabi
    # KAM sonli (odatda max_per_game=1) maxsus rollarga o'yinchi yetib bormay qolardi -
    # shu sabab deyarli hamma "Tinch aholi" bo'lib chiqardi. Endi: rollar avval
    # max_per_game bo'yicha O'SUVCHI tartibda (kam sonli, ya'ni "kamyob"/maxsus rollar
    # OLDIN) saralanadi, shu tartibda taqsimlanadi - shunda maxsus rollar KAFOLATLI
    # o'rin oladi, to'ldiruvchi rol esa faqat QOLGAN o'yinchilarni to'ldiradi.
    from itertools import groupby
    roles_by_rarity = sorted(roles, key=lambda r: max(r.max_per_game, 1))
    ordered_roles: list[Role] = []
    for _, group in groupby(roles_by_rarity, key=lambda r: max(r.max_per_game, 1)):
        group_list = list(group)
        random.shuffle(group_list)  # bir xil darajadagilar orasida adolatli tasodifiylik
        ordered_roles.extend(group_list)

    for role in ordered_roles:
        if role.min_players_required and n < role.min_players_required:
            continue
        already_used = used_slots.get(role.id, 0) if (role.id and role.id > 0) else 0
        slots = max(role.max_per_game, 1) - already_used
        for _ in range(max(slots, 0)):
            if idx >= len(remaining_players):
                break
            if role.team == RoleTeam.mafia and mafia_assigned >= max_mafia:
                break  # bu rol uchun mafiya limiti to'ldi - keyingi rolga o'tamiz
            assignment[remaining_players[idx]] = role
            if role.team == RoleTeam.mafia:
                mafia_assigned += 1
            idx += 1

    # Qolganlarga standart "Tinch aholi" rolini beramiz (agar mavjud bo'lmasa - soxta rol yaratamiz)
    fallback_peaceful = next((r for r in roles if r.team == RoleTeam.peaceful and r.night_action_type.value == "none"), None)
    for i in range(idx, len(remaining_players)):
        if fallback_peaceful:
            assignment[remaining_players[i]] = fallback_peaceful
        else:
            assignment[remaining_players[i]] = Role(
                id=-1, name="Tinch aholi", emoji="🕊", team=RoleTeam.peaceful,
                description="Oddiy tinch aholi vakili.", max_per_game=999,
            )

    return assignment


def count_teams(assignment: dict[int, Role], alive_ids: set[int]) -> dict[str, int]:
    counts = {"mafia": 0, "peaceful": 0, "solo": 0}
    for uid in alive_ids:
        role = assignment.get(uid)
        if role:
            counts[role.team.value] += 1
    return counts


def check_win_condition(assignment: dict[int, Role], alive_ids: set[int]) -> str | None:
    """G'olib jamoani qaytaradi ('mafia'/'peaceful') yoki hali tugamagan bo'lsa None."""
    counts = count_teams(assignment, alive_ids)
    if counts["mafia"] == 0:
        return "peaceful"
    if counts["mafia"] >= counts["peaceful"] + counts["solo"]:
        return "mafia"
    return None
