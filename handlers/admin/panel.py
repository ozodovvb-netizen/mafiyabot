"""
/admin komandasi - admin panelga kirish nuqtasi.
Barcha admin CRUD bo'limlari shu paneldan tarmoqlanadi.
"""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from database import crud
from keyboards.admin_kb import admin_main_kb, back_admin_kb
from utils.helpers import is_user_admin

router = Router(name="admin_panel")


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not await is_user_admin(message.from_user.id):
        return
    await message.answer("🛠 <b>Admin panel</b>", reply_markup=admin_main_kb())


@router.callback_query(F.data == "adm:main")
async def adm_main(callback: CallbackQuery):
    if not await is_user_admin(callback.from_user.id):
        await callback.answer()
        return
    await callback.message.edit_text("🛠 <b>Admin panel</b>", reply_markup=admin_main_kb())
    await callback.answer()


@router.callback_query(F.data == "adm:stats")
async def adm_stats(callback: CallbackQuery):
    if not await is_user_admin(callback.from_user.id):
        await callback.answer()
        return
    stats = await crud.get_stats_overview()
    text = (
        "📊 <b>Umumiy statistika</b>\n\n"
        f"👤 Foydalanuvchilar soni: {stats['total_users']}\n"
        f"💵 Umumiy pul (barcha foydalanuvchilarda): {stats['total_money']}\n"
        f"💎 Umumiy olmos: {stats['total_diamonds']}\n"
        f"🎮 Jami o'ynalgan o'yinlar: {stats['total_games']}"
    )
    await callback.message.edit_text(text, reply_markup=back_admin_kb())
    await callback.answer()
