"""
Admin - O'yin rejimlari bo'limi.

Har bir rejim (masalan "classic", "zombi", "chaos") o'zining o'yinchilar soni oralig'iga
ega: o'yin boshlanganda, joriy o'yinchilar soniga qarab mos rejim avtomatik tanlanadi va
faqat o'sha rejimga tegishli qilib belgilangan rollar ishlatiladi (rollarga rejim
"Rollar" bo'limida rol qo'shishda beriladi).
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import crud
from keyboards.admin_kb import back_admin_kb, mode_roles_view_kb, game_mode_pick_kb
from states.states import AdminGameMode
from utils.helpers import is_user_admin

router = Router(name="game_modes_admin")


@router.callback_query(F.data == "adm:game_modes")
async def adm_modes_list(callback: CallbackQuery, state: FSMContext):
    if not await is_user_admin(callback.from_user.id):
        await callback.answer()
        return
    await state.clear()
    modes = await crud.get_game_modes(active_only=False)
    names = await crud.get_mode_names(active_only=False)

    builder = InlineKeyboardBuilder()
    for idx, name in enumerate(names):
        builder.button(text=f"🎭 {name} — rollarni ko'rish", callback_data=f"adm_mode:view:{idx}")
    for m in modes:
        builder.button(
            text=f"🗑 {m.name} ({m.min_players}-{m.max_players})",
            callback_data=f"adm_mode:del:{m.id}",
        )
    builder.button(text="➕ Rejim qo'shish", callback_data="adm_mode:add")
    builder.button(text="↩️ Orqaga", callback_data="adm:main")
    builder.adjust(1)

    text = (
        "🎲 <b>O'yin rejimlari</b>\n\n"
        "O'yin boshlanganda o'yinchilar soniga qarab shu rejimlardan biri avtomatik "
        "tanlanadi va faqat o'sha rejimga tegishli rollar ishlatiladi. "
        "Har bir rejimga qaysi rollar va nechta donadan kirishini \"rollarni ko'rish\" "
        "tugmasi orqali belgilashingiz mumkin.\n\n"
        "Hech qanday oraliqqa to'g'ri kelmasa - \"classic\" rejimi ishlatiladi.\n\n"
        + ("\n".join(f"• <b>{m.name}</b>: {m.min_players}-{m.max_players} kishi" for m in modes) or "— hozircha rejim yo'q —")
    )
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("adm_mode:view:"))
async def adm_mode_view_roles(callback: CallbackQuery):
    if not await is_user_admin(callback.from_user.id):
        await callback.answer()
        return
    idx = int(callback.data.split(":")[-1])
    await _render_mode_roles(callback, idx)
    await callback.answer()


async def _render_mode_roles(callback: CallbackQuery, idx: int):
    names = await crud.get_mode_names(active_only=False)
    if not (0 <= idx < len(names)):
        await callback.answer("❌ Bu rejim topilmadi.", show_alert=True)
        return
    mode_name = names[idx]

    roles_in_mode = await crud.get_roles_for_mode(mode_name, active_only=False)
    all_roles = await crud.get_roles(active_only=False)
    in_mode_ids = {r.id for r in roles_in_mode}
    assignable_roles = [r for r in all_roles if r.id not in in_mode_ids]

    roles_text = (
        "\n".join(f"• {r.emoji} {r.name} — {r.max_per_game} dona" for r in roles_in_mode)
        if roles_in_mode else "— hozircha bu rejimga hech qanday rol biriktirilmagan —"
    )
    await callback.message.edit_text(
        f"🎲 <b>{mode_name}</b> rejimiga tegishli rollar:\n\n{roles_text}\n\n"
        "Rolni bosib uning sonini yoki boshqa sozlamalarini o'zgartirishingiz mumkin. "
        "Boshqa rejimdagi rolni shu rejimga qo'shish uchun pastdagi \"➕\" tugmalaridan foydalaning "
        "(rol faqat BITTA rejimga tegishli bo'ladi, qo'shilganda eski rejimidan chiqadi):",
        reply_markup=mode_roles_view_kb(idx, roles_in_mode, assignable_roles),
    )


@router.callback_query(F.data.startswith("adm_mode:assign:"))
async def adm_mode_assign_role(callback: CallbackQuery):
    if not await is_user_admin(callback.from_user.id):
        await callback.answer()
        return
    _, _, idx_s, role_id_s = callback.data.split(":")
    idx, role_id = int(idx_s), int(role_id_s)
    names = await crud.get_mode_names(active_only=False)
    if not (0 <= idx < len(names)):
        await callback.answer("❌ Bu rejim topilmadi.", show_alert=True)
        return
    mode_name = names[idx]

    role = await crud.get_role(role_id)
    if not role:
        await callback.answer("❌ Bu rol topilmadi.", show_alert=True)
        return
    if await crud.role_name_exists_in_mode(role.name, mode_name, exclude_id=role_id):
        await callback.answer(
            f"⚠️ \"{role.name}\" nomli rol \"{mode_name}\" rejimida allaqachon mavjud.",
            show_alert=True,
        )
        return

    await crud.update_role(role_id, mode=mode_name)
    await _render_mode_roles(callback, idx)
    await callback.answer(f"✅ {role.name} endi \"{mode_name}\" rejimiga tegishli.")


@router.callback_query(F.data.startswith("adm_mode:role_del:"))
async def adm_mode_role_delete(callback: CallbackQuery):
    """Rejim ichidan, to'liq rol tahririga kirmasdan, rolni butunlay o'chiradi."""
    if not await is_user_admin(callback.from_user.id):
        await callback.answer()
        return
    _, _, idx_s, role_id_s = callback.data.split(":")
    idx, role_id = int(idx_s), int(role_id_s)
    role = await crud.get_role(role_id)
    role_name = role.name if role else "Rol"
    await crud.delete_role(role_id)
    await _render_mode_roles(callback, idx)
    await callback.answer(f"🗑 {role_name} o'chirildi")


@router.callback_query(F.data.startswith("adm_mode:role_move:"))
async def adm_mode_role_move_start(callback: CallbackQuery):
    """Rejim ichidan rolni boshqa rejimga o'tkazish uchun yangi rejimni tanlash."""
    if not await is_user_admin(callback.from_user.id):
        await callback.answer()
        return
    _, _, idx_s, role_id_s = callback.data.split(":")
    idx, role_id = int(idx_s), int(role_id_s)
    role = await crud.get_role(role_id)
    if not role:
        await callback.answer("❌ Bu rol topilmadi.", show_alert=True)
        return
    names = await crud.get_mode_names(active_only=False)
    await callback.message.edit_text(
        f"➡️ \"{role.name}\" rolini qaysi rejimga o'tkazmoqchisiz?",
        reply_markup=game_mode_pick_kb(
            names,
            f"adm_mode:role_move_pick:{idx}:{role_id}",
            back_target=f"adm_mode:view:{idx}",
        ),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("adm_mode:role_move_pick:"))
async def adm_mode_role_move_save(callback: CallbackQuery):
    """Tanlangan yangi rejimga rolni o'tkazadi va o'sha (yangi) rejim ro'yxatini ko'rsatadi."""
    if not await is_user_admin(callback.from_user.id):
        await callback.answer()
        return
    _, _, old_idx_s, role_id_s, new_idx_s = callback.data.split(":")
    old_idx, role_id, new_idx = int(old_idx_s), int(role_id_s), int(new_idx_s)
    names = await crud.get_mode_names(active_only=False)
    if not (0 <= new_idx < len(names)):
        await callback.answer("❌ Bu rejim topilmadi.", show_alert=True)
        return
    new_mode_name = names[new_idx]

    role = await crud.get_role(role_id)
    if not role:
        await callback.answer("❌ Bu rol topilmadi.", show_alert=True)
        return
    if await crud.role_name_exists_in_mode(role.name, new_mode_name, exclude_id=role_id):
        await callback.answer(
            f"⚠️ \"{role.name}\" nomli rol \"{new_mode_name}\" rejimida allaqachon mavjud.",
            show_alert=True,
        )
        return

    await crud.update_role(role_id, mode=new_mode_name)
    await _render_mode_roles(callback, new_idx)
    await callback.answer(f"✅ {role.name} \"{new_mode_name}\" rejimiga o'tkazildi.")


@router.callback_query(F.data.startswith("adm_mode:del:"))
async def adm_mode_delete(callback: CallbackQuery, state: FSMContext):
    if not await is_user_admin(callback.from_user.id):
        await callback.answer()
        return
    mode_id = int(callback.data.split(":")[-1])
    await crud.delete_game_mode(mode_id)
    await callback.answer("🗑 O'chirildi")
    await adm_modes_list(callback, state)


@router.callback_query(F.data == "adm_mode:add")
async def adm_mode_add_start(callback: CallbackQuery, state: FSMContext):
    if not await is_user_admin(callback.from_user.id):
        await callback.answer()
        return
    await state.set_state(AdminGameMode.waiting_name)
    await callback.message.edit_text(
        "📝 Yangi rejim nomini kiriting (masalan: classic, zombi, chaos):",
        reply_markup=back_admin_kb("adm:game_modes"),
    )
    await callback.answer()


@router.message(AdminGameMode.waiting_name)
async def adm_mode_name(message: Message, state: FSMContext):
    if not await is_user_admin(message.from_user.id):
        return
    await state.update_data(name=message.text.strip().lower())
    await state.set_state(AdminGameMode.waiting_min_players)
    await message.answer(
        "👥 Bu rejim uchun eng kam o'yinchi soni nechta?",
        reply_markup=back_admin_kb("adm:game_modes"),
    )


@router.message(AdminGameMode.waiting_min_players)
async def adm_mode_min(message: Message, state: FSMContext):
    if not await is_user_admin(message.from_user.id):
        return
    if not message.text.strip().isdigit():
        await message.answer("❌ Faqat raqam yuboring.", reply_markup=back_admin_kb("adm:game_modes"))
        return
    await state.update_data(min_players=int(message.text.strip()))
    await state.set_state(AdminGameMode.waiting_max_players)
    await message.answer(
        "👥 Bu rejim uchun eng ko'p o'yinchi soni nechta?",
        reply_markup=back_admin_kb("adm:game_modes"),
    )


@router.message(AdminGameMode.waiting_max_players)
async def adm_mode_max(message: Message, state: FSMContext):
    if not await is_user_admin(message.from_user.id):
        return
    if not message.text.strip().isdigit():
        await message.answer("❌ Faqat raqam yuboring.", reply_markup=back_admin_kb("adm:game_modes"))
        return
    data = await state.get_data()
    await crud.create_game_mode(
        name=data["name"],
        min_players=data["min_players"],
        max_players=int(message.text.strip()),
    )
    await state.clear()
    await message.answer("✅ Rejim qo'shildi! Endi 'Rollar' bo'limida rol qo'shganda bu rejimni tanlashingiz mumkin.", reply_markup=back_admin_kb())
