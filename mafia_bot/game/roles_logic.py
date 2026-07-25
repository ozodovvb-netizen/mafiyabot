"""O'yinchilarga rollarni tasodifiy taqsimlash logikasi."""
import random

from database.models import Role, RoleTeam


def assign_roles(player_ids: list[int], roles: list[Role]) -> dict[int, Role]:
    """
    player_ids - o'yinga qo'shilgan foydalanuvchilar ro'yxati.
    roles - admin panelda sozlangan barcha faol rollar.

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
    available_roles: list[Role] = []

    for role in roles:
        if role.min_players_required and n < role.min_players_required:
            continue
        for _ in range(max(role.max_per_game, 1)):
            available_roles.append(role)

    random.shuffle(available_roles)

    # Mafiya soni umumiy o'yinchilarning taxminan 1/4 qismidan oshmasin (muvozanat uchun)
    max_mafia = max(1, n // 4)
    mafia_assigned = 0

    idx = 0
    for role in available_roles:
        if idx >= n:
            break
        if role.team == RoleTeam.mafia:
            if mafia_assigned >= max_mafia:
                continue
            mafia_assigned += 1
        assignment[shuffled_players[idx]] = role
        idx += 1

    # Qolganlarga standart "Tinch aholi" rolini beramiz (agar mavjud bo'lmasa - soxta rol yaratamiz)
    fallback_peaceful = next((r for r in roles if r.team == RoleTeam.peaceful and r.night_action_type.value == "none"), None)
    for i in range(idx, n):
        if fallback_peaceful:
            assignment[shuffled_players[i]] = fallback_peaceful
        else:
            assignment[shuffled_players[i]] = Role(
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
