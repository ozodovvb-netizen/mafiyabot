"""Aiogram FSM holatlari - foydalanuvchi va admin oqimlari uchun."""
from aiogram.fsm.state import State, StatesGroup


class PartnerStates(StatesGroup):
    waiting_target_id = State()


class DiamondTopupStates(StatesGroup):
    waiting_receipt = State()


class AdminUserSearch(StatesGroup):
    waiting_user_id = State()
    waiting_money_amount = State()
    waiting_diamond_amount = State()


class AdminShopItem(StatesGroup):
    waiting_name = State()
    waiting_protection_type = State()
    waiting_description = State()
    waiting_price_money = State()
    waiting_price_diamond = State()
    waiting_category = State()


class AdminHero(StatesGroup):
    waiting_name = State()
    waiting_abilities = State()
    waiting_protection_text = State()
    waiting_price_diamond = State()
    waiting_price_stars = State()


class AdminRole(StatesGroup):
    waiting_name = State()
    waiting_team = State()
    waiting_action_type = State()
    waiting_mode = State()
    waiting_description = State()
    waiting_max_per_game = State()
    waiting_is_boss = State()
    waiting_dual_action = State()
    waiting_succeeds = State()


class AdminGameMode(StatesGroup):
    waiting_name = State()
    waiting_min_players = State()
    waiting_max_players = State()


class AdminPremiumGroup(StatesGroup):
    waiting_country = State()
    waiting_name = State()
    waiting_link = State()
    waiting_rank = State()


class AdminMoneyPackage(StatesGroup):
    waiting_money_amount = State()
    waiting_diamond_price = State()


class AdminDiamondPackage(StatesGroup):
    waiting_price_sum = State()
    waiting_diamond_amount = State()


class AdminRewardSettings(StatesGroup):
    waiting_winner_money = State()
    waiting_winner_diamond = State()
    waiting_loser_money = State()
    waiting_loser_diamond = State()


class AdminAdminUsername(StatesGroup):
    waiting_username = State()


class AdminCardNumber(StatesGroup):
    waiting_card = State()


class AdminAddAdmin(StatesGroup):
    waiting_user_id = State()


class GroupGameLastWords(StatesGroup):
    waiting_words = State()
