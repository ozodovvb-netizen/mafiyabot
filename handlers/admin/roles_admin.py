"""Admin - Rollar bo'limi: rol qo'shish/o'chirish, jamoa va tungi harakat turini belgilash."""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from database import crud
from database.models import RoleTeam, NightActionType
from keyboards.admin_kb import (
    back_admin_kb, role_team_select_kb, role_action_select_kb,
    role_list_view_kb, role_view_kb, role_team_edit_kb, role_action_edit_kb,
    game_mode_pick_kb, role_money_target_kb,
)
from states.states import AdminRole, AdminRoleEdit
from utils.helpers import is_user_admin

router = Router(name="roles_admin")


@router.callback_query(F.data == "adm:roles")
async def adm_roles_list(callback: CallbackQuery, state: FSMContext):
    if not await is_user_admin(callback.from_user.id):
        await callback.answer()
        return
    await state.clear()
    roles = await crud.get_roles(active_only=False)
    await callback.message.edit_text(
        "🎭 <b>Rollar</b>\n\nTahrirlash/o'chirish uchun bosing, yangi qo'shish uchun pastdagi tugma:",
        reply_markup=role_list_view_kb(roles),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("adm_role:view:"))
async def adm_role_view(callback: CallbackQuery):
    if not await is_user_admin(callback.from_user.id):
        await callback.answer()
        return
    role_id = int(callback.data.split(":")[-1])
    role = await crud.get_role(role_id)
    if not role:
        await callback.answer("❌ Topilmadi.", show_alert=True)
        return
    text = (
        f"{role.emoji} <b>{role.name}</b>\n\n{role.description}\n\n"
        "Quyidagi tugmalar orqali har bir sozlamani alohida o'zgartirishingiz mumkin:"
    )
    await callback.message.edit_text(text, reply_markup=role_view_kb(role))
    await callback.answer()


@router.callback_query(F.data.startswith("role_edit_toggle:"))
async def adm_role_edit_toggle(callback: CallbackQuery):
    if not await is_user_admin(callback.from_user.id):
        await callback.answer()
        return
    _, role_id_s, field = callback.data.split(":")
    role_id = int(role_id_s)
    role = await crud.get_role(role_id)
    if not role:
        await callback.answer("❌ Topilmadi.", show_alert=True)
        return
    role = await crud.update_role(role_id, **{field: not getattr(role, field)})
    if not role:
        await callback.answer("❌ Bu rol allaqachon o'chirilgan.", show_alert=True)
        return
    await callback.message.edit_text(
        f"{role.emoji} <b>{role.name}</b>\n\n{role.description}\n\n"
        "Quyidagi tugmalar orqali har bir sozlamani alohida o'zgartirishingiz mumkin:",
        reply_markup=role_view_kb(role),
    )
    await callback.answer("✅ Yangilandi")


@router.callback_query(F.data.startswith("role_edit_team_open:"))
async def adm_role_edit_team_open(callback: CallbackQuery):
    if not await is_user_admin(callback.from_user.id):
        await callback.answer()
        return
    role_id = int(callback.data.split(":")[-1])
    await callback.message.edit_text("⚔️ Yangi jamoani tanlang:", reply_markup=role_team_edit_kb(role_id))
    await callback.answer()


@router.callback_query(F.data.startswith("role_edit_team_set:"))
async def adm_role_edit_team_set(callback: CallbackQuery):
    if not await is_user_admin(callback.from_user.id):
        await callback.answer()
        return
    _, role_id_s, team = callback.data.split(":")
    role = await crud.update_role(int(role_id_s), team=RoleTeam(team))
    if not role:
        await callback.answer("❌ Bu rol allaqachon o'chirilgan.", show_alert=True)
        return
    await callback.message.edit_text(
        f"{role.emoji} <b>{role.name}</b>\n\n{role.description}\n\n"
        "Quyidagi tugmalar orqali har bir sozlamani alohida o'zgartirishingiz mumkin:",
        reply_markup=role_view_kb(role),
    )
    await callback.answer("✅ Jamoa yangilandi")


@router.callback_query(F.data.startswith("role_edit_action_open:"))
async def adm_role_edit_action_open(callback: CallbackQuery):
    if not await is_user_admin(callback.from_user.id):
        await callback.answer()
        return
    role_id = int(callback.data.split(":")[-1])
    await callback.message.edit_text("🌙 Yangi tungi harakat turini tanlang:", reply_markup=role_action_edit_kb(role_id))
    await callback.answer()


@router.callback_query(F.data.startswith("role_edit_action_set:"))
async def adm_role_edit_action_set(callback: CallbackQuery):
    if not await is_user_admin(callback.from_user.id):
        await callback.answer()
        return
    _, role_id_s, action = callback.data.split(":")
    role = await crud.update_role(int(role_id_s), night_action_type=NightActionType(action))
    if not role:
        await callback.answer("❌ Bu rol allaqachon o'chirilgan.", show_alert=True)
        return
    await callback.message.edit_text(
        f"{role.emoji} <b>{role.name}</b>\n\n{role.description}\n\n"
        "Quyidagi tugmalar orqali har bir sozlamani alohida o'zgartirishingiz mumkin:",
        reply_markup=role_view_kb(role),
    )
    await callback.answer("✅ Harakat turi yangilandi")


@router.callback_query(F.data.startswith("role_edit_max:"))
async def adm_role_edit_max_start(callback: CallbackQuery, state: FSMContext):
    if not await is_user_admin(callback.from_user.id):
        await callback.answer()
        return
    role_id = int(callback.data.split(":")[-1])
    await state.update_data(role_id=role_id)
    await state.set_state(AdminRoleEdit.waiting_max)
    await callback.message.edit_text(
        "🔢 Bitta o'yinda bu roldan nechta bo'lishini yozing (masalan: 1):",
        reply_markup=back_admin_kb(f"adm_role:view:{role_id}"),
    )
    await callback.answer()


@router.message(AdminRoleEdit.waiting_max)
async def adm_role_edit_max_save(message: Message, state: FSMContext):
    if not await is_user_admin(message.from_user.id):
        await state.clear()
        return
    data = await state.get_data()
    if not message.text.strip().isdigit():
        await message.answer("❌ Faqat raqam yuboring.", reply_markup=back_admin_kb(f"adm_role:view:{data.get('role_id', '')}"))
        return
    role = await crud.update_role(data["role_id"], max_per_game=int(message.text.strip()))
    await state.clear()
    if not role:
        await message.answer("❌ Bu rol allaqachon o'chirilgan.", reply_markup=back_admin_kb("adm:roles"))
        return
    await message.answer(
        f"{role.emoji} <b>{role.name}</b>\n\n{role.description}\n\n"
        "Quyidagi tugmalar orqali har bir sozlamani alohida o'zgartirishingiz mumkin:",
        reply_markup=role_view_kb(role),
    )


@router.callback_query(F.data.startswith("role_edit_price:"))
async def adm_role_edit_price_start(callback: CallbackQuery, state: FSMContext):
    if not await is_user_admin(callback.from_user.id):
        await callback.answer()
        return
    role_id = int(callback.data.split(":")[-1])
    await state.update_data(role_id=role_id)
    await state.set_state(AdminRoleEdit.waiting_price)
    await callback.message.edit_text(
        "💎 Do'kondan sotib olish narxini olmosda yozing (0 = sotilmaydi):",
        reply_markup=back_admin_kb(f"adm_role:view:{role_id}"),
    )
    await callback.answer()


@router.message(AdminRoleEdit.waiting_price)
async def adm_role_edit_price_save(message: Message, state: FSMContext):
    if not await is_user_admin(message.from_user.id):
        await state.clear()
        return
    data = await state.get_data()
    if not message.text.strip().isdigit():
        await message.answer("❌ Faqat raqam yuboring (0 = sotilmaydi).", reply_markup=back_admin_kb(f"adm_role:view:{data.get('role_id', '')}"))
        return
    role = await crud.update_role(data["role_id"], price_diamond=int(message.text.strip()))
    await state.clear()
    if not role:
        await message.answer("❌ Bu rol allaqachon o'chirilgan.", reply_markup=back_admin_kb("adm:roles"))
        return
    await message.answer(
        f"{role.emoji} <b>{role.name}</b>\n\n{role.description}\n\n"
        "Quyidagi tugmalar orqali har bir sozlamani alohida o'zgartirishingiz mumkin:",
        reply_markup=role_view_kb(role),
    )


@router.callback_query(F.data.startswith("role_edit_vote_weight:"))
async def adm_role_edit_vote_weight_start(callback: CallbackQuery, state: FSMContext):
    if not await is_user_admin(callback.from_user.id):
        await callback.answer()
        return
    role_id = int(callback.data.split(":")[-1])
    await state.update_data(role_id=role_id)
    await state.set_state(AdminRoleEdit.waiting_vote_weight)
    await callback.message.edit_text(
        "🗳 Kunduzgi ovoz berishda bu rol egasining OVOZI necha marta hisoblanishi kerak? "
        "(masalan oddiy uchun 1, \"2x ovoz\" uchun 2):",
        reply_markup=back_admin_kb(f"adm_role:view:{role_id}"),
    )
    await callback.answer()


@router.message(AdminRoleEdit.waiting_vote_weight)
async def adm_role_edit_vote_weight_save(message: Message, state: FSMContext):
    if not await is_user_admin(message.from_user.id):
        await state.clear()
        return
    data = await state.get_data()
    if not message.text.strip().isdigit() or int(message.text.strip()) < 1:
        await message.answer("❌ Faqat 1 yoki undan katta raqam yuboring.", reply_markup=back_admin_kb(f"adm_role:view:{data.get('role_id', '')}"))
        return
    role = await crud.update_role(data["role_id"], day_vote_weight=int(message.text.strip()))
    await state.clear()
    if not role:
        await message.answer("❌ Bu rol allaqachon o'chirilgan.", reply_markup=back_admin_kb("adm:roles"))
        return
    await message.answer(
        f"{role.emoji} <b>{role.name}</b>\n\n{role.description}\n\n"
        "Quyidagi tugmalar orqali har bir sozlamani alohida o'zgartirishingiz mumkin:",
        reply_markup=role_view_kb(role),
    )


@router.callback_query(F.data.startswith("role_edit_money_open:"))
async def adm_role_edit_money_open(callback: CallbackQuery):
    if not await is_user_admin(callback.from_user.id):
        await callback.answer()
        return
    _, role_id_s, phase = callback.data.split(":")
    label = "Tungi (tun tugaganda)" if phase == "night" else "Kunduzgi (kun boshlanganda)"
    await callback.message.edit_text(
        f"💰 {label} pul effekti turini tanlang:",
        reply_markup=role_money_target_kb(int(role_id_s), phase),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("role_edit_money_set:"))
async def adm_role_edit_money_set(callback: CallbackQuery, state: FSMContext):
    if not await is_user_admin(callback.from_user.id):
        await callback.answer()
        return
    _, role_id_s, phase, target = callback.data.split(":")
    role_id = int(role_id_s)
    if target == "none":
        role = await crud.update_role(role_id, **{f"{phase}_money_target": None, f"{phase}_money_amount": 0})
        if not role:
            await callback.answer("❌ Bu rol allaqachon o'chirilgan.", show_alert=True)
            return
        await callback.message.edit_text(
            f"{role.emoji} <b>{role.name}</b>\n\n{role.description}\n\n"
            "Quyidagi tugmalar orqali har bir sozlamani alohida o'zgartirishingiz mumkin:",
            reply_markup=role_view_kb(role),
        )
        await callback.answer("✅ Yangilandi")
        return

    await state.update_data(role_id=role_id, phase=phase, target=target)
    await state.set_state(
        AdminRoleEdit.waiting_night_money_amount if phase == "night" else AdminRoleEdit.waiting_day_money_amount
    )
    who = "o'ziga" if target == "self" else "HAR BIR tirik o'yinchiga"
    await callback.message.edit_text(
        f"💵 Necha dollar {who} berilsin? (masalan: 50):",
        reply_markup=back_admin_kb(f"adm_role:view:{role_id}"),
    )
    await callback.answer()


@router.message(AdminRoleEdit.waiting_night_money_amount)
@router.message(AdminRoleEdit.waiting_day_money_amount)
async def adm_role_edit_money_amount_save(message: Message, state: FSMContext):
    if not await is_user_admin(message.from_user.id):
        await state.clear()
        return
    data = await state.get_data()
    if not message.text.strip().isdigit() or int(message.text.strip()) <= 0:
        await message.answer("❌ Faqat 0 dan katta raqam yuboring.", reply_markup=back_admin_kb(f"adm_role:view:{data.get('role_id', '')}"))
        return
    phase = data["phase"]
    role = await crud.update_role(
        data["role_id"],
        **{f"{phase}_money_target": data["target"], f"{phase}_money_amount": int(message.text.strip())},
    )
    await state.clear()
    if not role:
        await message.answer("❌ Bu rol allaqachon o'chirilgan.", reply_markup=back_admin_kb("adm:roles"))
        return
    await message.answer(
        f"{role.emoji} <b>{role.name}</b>\n\n{role.description}\n\n"
        "Quyidagi tugmalar orqali har bir sozlamani alohida o'zgartirishingiz mumkin:",
        reply_markup=role_view_kb(role),
    )


@router.callback_query(F.data.startswith("role_edit_mode:"))
async def adm_role_edit_mode_start(callback: CallbackQuery, state: FSMContext):
    if not await is_user_admin(callback.from_user.id):
        await callback.answer()
        return
    role_id = int(callback.data.split(":")[-1])
    await state.update_data(role_id=role_id)
    await state.set_state(AdminRoleEdit.waiting_mode)
    names = await crud.get_mode_names()
    await callback.message.edit_text(
        "🎲 Yangi rejimni tanlang:",
        reply_markup=game_mode_pick_kb(names, "role_edit_mode_pick", back_target=f"adm_role:view:{role_id}"),
    )
    await callback.answer()


@router.callback_query(AdminRoleEdit.waiting_mode, F.data.startswith("role_edit_mode_pick:"))
async def adm_role_edit_mode_save(callback: CallbackQuery, state: FSMContext):
    if not await is_user_admin(callback.from_user.id):
        await callback.answer()
        await state.clear()
        return
    idx = int(callback.data.split(":")[-1])
    names = await crud.get_mode_names()
    mode = names[idx] if 0 <= idx < len(names) else "classic"
    data = await state.get_data()
    role_id = data["role_id"]

    existing = await crud.get_role(role_id)
    if existing and await crud.role_name_exists_in_mode(existing.name, mode, exclude_id=role_id):
        await state.clear()
        await callback.message.edit_text(
            f"⚠️ \"{existing.name}\" nomli rol \"{mode}\" rejimida allaqachon mavjud. "
            "Rejimni o'zgartirib bo'lmaydi, chunki bitta o'yinda bir xil rol ikki marta "
            "chiqib qolishi mumkin.",
            reply_markup=role_view_kb(existing),
        )
        await callback.answer()
        return

    role = await crud.update_role(role_id, mode=mode)
    await state.clear()
    if not role:
        await callback.message.edit_text("❌ Bu rol allaqachon o'chirilgan.", reply_markup=back_admin_kb("adm:roles"))
        await callback.answer()
        return
    await callback.message.edit_text(
        f"{role.emoji} <b>{role.name}</b>\n\n{role.description}\n\n"
        "Quyidagi tugmalar orqali har bir sozlamani alohida o'zgartirishingiz mumkin:",
        reply_markup=role_view_kb(role),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("role_edit_desc:"))
async def adm_role_edit_desc_start(callback: CallbackQuery, state: FSMContext):
    if not await is_user_admin(callback.from_user.id):
        await callback.answer()
        return
    role_id = int(callback.data.split(":")[-1])
    await state.update_data(role_id=role_id)
    await state.set_state(AdminRoleEdit.waiting_desc)
    await callback.message.edit_text(
        "✍️ Yangi tavsifni yozing (foydalanuvchi /roles bosganda ko'radi):",
        reply_markup=back_admin_kb(f"adm_role:view:{role_id}"),
    )
    await callback.answer()


@router.message(AdminRoleEdit.waiting_desc)
async def adm_role_edit_desc_save(message: Message, state: FSMContext):
    if not await is_user_admin(message.from_user.id):
        await state.clear()
        return
    data = await state.get_data()
    role = await crud.update_role(data["role_id"], description=message.text.strip())
    await state.clear()
    if not role:
        await message.answer("❌ Bu rol allaqachon o'chirilgan.", reply_markup=back_admin_kb("adm:roles"))
        return
    await message.answer(
        f"{role.emoji} <b>{role.name}</b>\n\n{role.description}\n\n"
        "Quyidagi tugmalar orqali har bir sozlamani alohida o'zgartirishingiz mumkin:",
        reply_markup=role_view_kb(role),
    )


@router.callback_query(F.data.startswith("role_edit_succ_open:"))
async def adm_role_edit_succ_open(callback: CallbackQuery):
    if not await is_user_admin(callback.from_user.id):
        await callback.answer()
        return
    role_id = int(callback.data.split(":")[-1])
    roles = await crud.get_roles(active_only=False)
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="➖ Hech kimning o'rnini bosmaydi", callback_data=f"role_edit_succ_set:{role_id}:0")
    for r in roles:
        if r.id == role_id:
            continue
        builder.button(text=f"{r.emoji} {r.name}", callback_data=f"role_edit_succ_set:{role_id}:{r.id}")
    builder.button(text="↩️ Bekor qilish", callback_data=f"adm_role:view:{role_id}")
    builder.adjust(1)
    await callback.message.edit_text(
        "🔁 Bu rol egasi tirik bo'lib, quyidagi rollardan biri o'lsa, uning o'rnini bosib, "
        "o'sha rolga aylanadimi?",
        reply_markup=builder.as_markup(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("role_edit_succ_set:"))
async def adm_role_edit_succ_set(callback: CallbackQuery):
    if not await is_user_admin(callback.from_user.id):
        await callback.answer()
        return
    _, role_id_s, succ_id_s = callback.data.split(":")
    role = await crud.update_role(int(role_id_s), succeeds_role_id=(int(succ_id_s) or None))
    if not role:
        await callback.answer("❌ Bu rol allaqachon o'chirilgan.", show_alert=True)
        return
    await callback.message.edit_text(
        f"{role.emoji} <b>{role.name}</b>\n\n{role.description}\n\n"
        "Quyidagi tugmalar orqali har bir sozlamani alohida o'zgartirishingiz mumkin:",
        reply_markup=role_view_kb(role),
    )
    await callback.answer("✅ Yangilandi")


@router.callback_query(F.data.startswith("adm_role:del:"))
async def adm_role_delete(callback: CallbackQuery):
    if not await is_user_admin(callback.from_user.id):
        await callback.answer()
        return
    role_id = int(callback.data.split(":")[-1])
    await crud.delete_role(role_id)
    roles = await crud.get_roles(active_only=False)
    await callback.message.edit_text(
        "🎭 <b>Rollar</b>\n\nTahrirlash/o'chirish uchun bosing, yangi qo'shish uchun pastdagi tugma:",
        reply_markup=role_list_view_kb(roles),
    )
    await callback.answer("🗑 O'chirildi")


@router.callback_query(F.data == "adm_role:add")
async def adm_role_add_start(callback: CallbackQuery, state: FSMContext):
    if not await is_user_admin(callback.from_user.id):
        await callback.answer()
        return
    await state.set_state(AdminRole.waiting_name)
    await callback.message.edit_text(
        "📝 Rol nomini kiriting (masalan: Shergar, Advokat, Jurnalist...):",
        reply_markup=back_admin_kb("adm:roles"),
    )
    await callback.answer()


@router.message(AdminRole.waiting_name)
async def adm_role_name(message: Message, state: FSMContext):
    if not await is_user_admin(message.from_user.id):
        await state.clear()
        return
    await state.update_data(name=message.text.strip())
    await state.set_state(AdminRole.waiting_team)
    await message.answer("⚔️ Bu rol qaysi jamoaga tegishli?", reply_markup=role_team_select_kb())


@router.callback_query(AdminRole.waiting_team, F.data.startswith("role_team:"))
async def adm_role_team(callback: CallbackQuery, state: FSMContext):
    if not await is_user_admin(callback.from_user.id):
        await callback.answer()
        await state.clear()
        return
    team = callback.data.split(":", 1)[1]
    await state.update_data(team=team)
    await state.set_state(AdminRole.waiting_action_type)
    await callback.message.edit_text(
        "🌙 Bu rol tunda qanday harakat qiladi? (agar avtomatik mexanika kerak bo'lmasa "
        "'Faqat matn' ni tanlang - rol faqat hikoya/rol-play maqsadida bo'ladi)",
        reply_markup=role_action_select_kb(),
    )
    await callback.answer()


@router.callback_query(AdminRole.waiting_action_type, F.data.startswith("role_action:"))
async def adm_role_action(callback: CallbackQuery, state: FSMContext):
    if not await is_user_admin(callback.from_user.id):
        await callback.answer()
        await state.clear()
        return
    action = callback.data.split(":", 1)[1]
    await state.update_data(action=action)
    await state.set_state(AdminRole.waiting_mode)

    names = await crud.get_mode_names()
    await callback.message.edit_text(
        "🎲 Bu rol qaysi o'yin rejimiga tegishli? Tugma orqali tanlang:",
        reply_markup=game_mode_pick_kb(names, "role_mode_pick"),
    )
    await callback.answer()


@router.callback_query(AdminRole.waiting_mode, F.data.startswith("role_mode_pick:"))
async def adm_role_mode(callback: CallbackQuery, state: FSMContext):
    if not await is_user_admin(callback.from_user.id):
        await callback.answer()
        await state.clear()
        return
    idx = int(callback.data.split(":")[-1])
    names = await crud.get_mode_names()
    mode = names[idx] if 0 <= idx < len(names) else "classic"
    await state.update_data(mode=mode)
    await state.set_state(AdminRole.waiting_description)
    await callback.message.edit_text(
        "✍️ Rol tavsifini yozing (bu matn foydalanuvchi /roles bosganda ko'radigan tavsif bo'ladi - "
        "'bu rol nima qila oladi'):",
        reply_markup=back_admin_kb("adm:roles"),
    )
    await callback.answer()


@router.message(AdminRole.waiting_description)
async def adm_role_description(message: Message, state: FSMContext):
    if not await is_user_admin(message.from_user.id):
        await state.clear()
        return
    await state.update_data(description=message.text.strip())
    await state.set_state(AdminRole.waiting_max_per_game)
    await message.answer(
        "🔢 Bitta o'yinda bu roldan nechta bo'lishi mumkin? (masalan: 1):",
        reply_markup=back_admin_kb("adm:roles"),
    )


@router.message(AdminRole.waiting_max_per_game)
async def adm_role_max(message: Message, state: FSMContext):
    if not await is_user_admin(message.from_user.id):
        await state.clear()
        return
    if not message.text.strip().isdigit():
        await message.answer("❌ Faqat raqam yuboring.", reply_markup=back_admin_kb("adm:roles"))
        return
    await state.update_data(max_per_game=int(message.text.strip()))
    await state.set_state(AdminRole.waiting_is_boss)

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Ha", callback_data="role_boss:1")
    builder.button(text="❌ Yo'q", callback_data="role_boss:0")
    builder.button(text="↩️ Bekor qilish", callback_data="adm:roles")
    builder.adjust(2, 1)
    await message.answer(
        "👑 Bu rol o'z JAMOASI uchun \"boshliq\"mi? (Masalan Don - mafiyalar turlicha "
        "nishon tansa ham, OXIRGI qaror shu rolga tegishli bo'ladi):",
        reply_markup=builder.as_markup(),
    )


@router.callback_query(AdminRole.waiting_is_boss, F.data.startswith("role_boss:"))
async def adm_role_boss(callback: CallbackQuery, state: FSMContext):
    if not await is_user_admin(callback.from_user.id):
        await callback.answer()
        await state.clear()
        return
    await state.update_data(is_team_boss=callback.data.endswith(":1"))
    await state.set_state(AdminRole.waiting_independent)

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Ha", callback_data="role_indep:1")
    builder.button(text="❌ Yo'q", callback_data="role_indep:0")
    builder.button(text="↩️ Bekor qilish", callback_data="adm:roles")
    builder.adjust(2, 1)
    await callback.message.edit_text(
        "🗡 Bu rol o'z nishonini MUSTAQIL tanlab, o'ldiradimi? (Masalan Qotil - mafiya "
        "jamoasida hisoblansa ham, boshliq/Don qaroriga bog'liq emas, o'zi tanlagan "
        "odamni o'zi o'ldiradi):",
        reply_markup=builder.as_markup(),
    )
    await callback.answer()


@router.callback_query(AdminRole.waiting_independent, F.data.startswith("role_indep:"))
async def adm_role_independent(callback: CallbackQuery, state: FSMContext):
    if not await is_user_admin(callback.from_user.id):
        await callback.answer()
        await state.clear()
        return
    await state.update_data(acts_independently=callback.data.endswith(":1"))
    await state.set_state(AdminRole.waiting_dual_action)

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Ha", callback_data="role_dual:1")
    builder.button(text="❌ Yo'q", callback_data="role_dual:0")
    builder.button(text="↩️ Bekor qilish", callback_data="adm:roles")
    builder.adjust(2, 1)
    await callback.message.edit_text(
        "🔀 Bu rol har kecha \"Tekshirish\" yoki \"Otish\" dan birini o'zi tanlab harakat "
        "qiladimi? (Masalan Komissar - xohlasa tekshiradi, xohlasa o'ldiradi):",
        reply_markup=builder.as_markup(),
    )
    await callback.answer()


@router.callback_query(AdminRole.waiting_dual_action, F.data.startswith("role_dual:"))
async def adm_role_dual(callback: CallbackQuery, state: FSMContext):
    if not await is_user_admin(callback.from_user.id):
        await callback.answer()
        await state.clear()
        return
    await state.update_data(dual_check_or_kill=callback.data.endswith(":1"))
    await state.set_state(AdminRole.waiting_wins_lynched)

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Ha", callback_data="role_wl:1")
    builder.button(text="❌ Yo'q", callback_data="role_wl:0")
    builder.button(text="↩️ Bekor qilish", callback_data="adm:roles")
    builder.adjust(2, 1)
    await callback.message.edit_text(
        "🃏 Bu rol FAQAT kunduzi ovoz berish orqali OSILSA (lynch qilinsa) g'olib "
        "hisoblanadimi (masalan Masxaraboz/Jester - jamoasi yoki tirik qolishiga "
        "bog'liq emas, faqat osilsa yutadi, aks holda yutqazadi)? Odatda bu turdagi "
        "rol tunda hech narsa qilolmaydi (\"Tungi harakat\" bosqichida \"Yo'q\" tanlang):",
        reply_markup=builder.as_markup(),
    )
    await callback.answer()


@router.callback_query(AdminRole.waiting_wins_lynched, F.data.startswith("role_wl:"))
async def adm_role_wins_lynched(callback: CallbackQuery, state: FSMContext):
    if not await is_user_admin(callback.from_user.id):
        await callback.answer()
        await state.clear()
        return
    await state.update_data(wins_when_lynched=callback.data.endswith(":1"))
    await state.set_state(AdminRole.waiting_succeeds)

    roles = await crud.get_roles(active_only=False)
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="➖ Hech kimning o'rnini bosmaydi", callback_data="role_succ:0")
    for r in roles:
        builder.button(text=f"{r.emoji} {r.name}", callback_data=f"role_succ:{r.id}")
    builder.button(text="↩️ Bekor qilish", callback_data="adm:roles")
    builder.adjust(1)
    await callback.message.edit_text(
        "🔁 Bu rol egasi tirik bo'lib, quyidagi rollardan biri o'lsa, uning o'rnini "
        "bosib, o'sha rolga aylanadimi? (masalan Serjant -> Komissar o'lsa Komissarga "
        "aylanadi). Agar bunday bo'lmasa - birinchi tugmani bosing:",
        reply_markup=builder.as_markup(),
    )
    await callback.answer()


@router.callback_query(AdminRole.waiting_succeeds, F.data.startswith("role_succ:"))
async def adm_role_succeeds(callback: CallbackQuery, state: FSMContext):
    if not await is_user_admin(callback.from_user.id):
        await callback.answer()
        await state.clear()
        return
    succ_id = int(callback.data.split(":")[-1])
    await state.update_data(succeeds_role_id=succ_id or None)
    await state.set_state(AdminRole.waiting_vote_weight)
    await callback.message.edit_text(
        "🗳 Kunduzgi ovoz berishda (kimni osish kerakligiga ovoz berishda) bu rol "
        "egasining OVOZI necha marta hisoblansin? Oddiy uchun 1 yozing, \"2x ovoz\" "
        "uchun 2 yozing:",
        reply_markup=back_admin_kb("adm:roles"),
    )
    await callback.answer()


@router.message(AdminRole.waiting_vote_weight)
async def adm_role_vote_weight(message: Message, state: FSMContext):
    if not await is_user_admin(message.from_user.id):
        await state.clear()
        return
    if not message.text.strip().isdigit() or int(message.text.strip()) < 1:
        await message.answer("❌ Faqat 1 yoki undan katta raqam yuboring.", reply_markup=back_admin_kb("adm:roles"))
        return
    await state.update_data(day_vote_weight=int(message.text.strip()))
    await state.set_state(AdminRole.waiting_night_money_target)
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="➖ Effekt yo'q", callback_data="role_new_money:night:none")
    builder.button(text="🙋 O'ziga (pul ishlab topadi)", callback_data="role_new_money:night:self")
    builder.button(text="👥 Hammaga (pul tarqatadi)", callback_data="role_new_money:night:all")
    builder.button(text="↩️ Bekor qilish", callback_data="adm:roles")
    builder.adjust(1)
    await message.answer(
        "🌙💰 Bu rol TUN tugagach avtomatik pul effektiga egami?", reply_markup=builder.as_markup()
    )


@router.callback_query(AdminRole.waiting_night_money_target, F.data.startswith("role_new_money:night:"))
async def adm_role_night_money_target(callback: CallbackQuery, state: FSMContext):
    if not await is_user_admin(callback.from_user.id):
        await callback.answer()
        await state.clear()
        return
    target = callback.data.split(":")[-1]
    if target == "none":
        await state.update_data(night_money_target=None, night_money_amount=0)
        await _adm_role_ask_day_money(callback.message, state)
    else:
        await state.update_data(night_money_target=target)
        await state.set_state(AdminRole.waiting_night_money_amount)
        who = "o'ziga" if target == "self" else "HAR BIR tirik o'yinchiga"
        await callback.message.edit_text(
            f"💵 Har tundan keyin {who} necha dollar berilsin? (masalan: 50):",
            reply_markup=back_admin_kb("adm:roles"),
        )
    await callback.answer()


@router.message(AdminRole.waiting_night_money_amount)
async def adm_role_night_money_amount(message: Message, state: FSMContext):
    if not await is_user_admin(message.from_user.id):
        await state.clear()
        return
    if not message.text.strip().isdigit() or int(message.text.strip()) <= 0:
        await message.answer("❌ Faqat 0 dan katta raqam yuboring.", reply_markup=back_admin_kb("adm:roles"))
        return
    await state.update_data(night_money_amount=int(message.text.strip()))
    await _adm_role_ask_day_money(message, state)


async def _adm_role_ask_day_money(message: Message, state: FSMContext):
    await state.set_state(AdminRole.waiting_day_money_target)
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="➖ Effekt yo'q", callback_data="role_new_money:day:none")
    builder.button(text="🙋 O'ziga (pul ishlab topadi)", callback_data="role_new_money:day:self")
    builder.button(text="👥 Hammaga (pul tarqatadi)", callback_data="role_new_money:day:all")
    builder.button(text="↩️ Bekor qilish", callback_data="adm:roles")
    builder.adjust(1)
    await message.answer(
        "☀️💰 Bu rol KUN boshlanganda avtomatik pul effektiga egami?", reply_markup=builder.as_markup()
    )


@router.callback_query(AdminRole.waiting_day_money_target, F.data.startswith("role_new_money:day:"))
async def adm_role_day_money_target(callback: CallbackQuery, state: FSMContext):
    if not await is_user_admin(callback.from_user.id):
        await callback.answer()
        await state.clear()
        return
    target = callback.data.split(":")[-1]
    if target == "none":
        await state.update_data(day_money_target=None, day_money_amount=0)
        await state.set_state(AdminRole.waiting_price)
        await callback.message.edit_text(
            "💎 Bu rolni foydalanuvchilar do'kondan (\"Faol rol\") sotib olib, KEYINGI o'yinda "
            "aynan shu rolda o'ynashlari mumkinmi? Narxini olmosda yozing (0 = sotilmaydi, "
            "faqat tasodifiy taqsimotda tushadi):",
            reply_markup=back_admin_kb("adm:roles"),
        )
    else:
        await state.update_data(day_money_target=target)
        await state.set_state(AdminRole.waiting_day_money_amount)
        who = "o'ziga" if target == "self" else "HAR BIR tirik o'yinchiga"
        await callback.message.edit_text(
            f"💵 Har kun boshida {who} necha dollar berilsin? (masalan: 50):",
            reply_markup=back_admin_kb("adm:roles"),
        )
    await callback.answer()


@router.message(AdminRole.waiting_day_money_amount)
async def adm_role_day_money_amount(message: Message, state: FSMContext):
    if not await is_user_admin(message.from_user.id):
        await state.clear()
        return
    if not message.text.strip().isdigit() or int(message.text.strip()) <= 0:
        await message.answer("❌ Faqat 0 dan katta raqam yuboring.", reply_markup=back_admin_kb("adm:roles"))
        return
    await state.update_data(day_money_amount=int(message.text.strip()))
    await state.set_state(AdminRole.waiting_price)
    await message.answer(
        "💎 Bu rolni foydalanuvchilar do'kondan (\"Faol rol\") sotib olib, KEYINGI o'yinda "
        "aynan shu rolda o'ynashlari mumkinmi? Narxini olmosda yozing (0 = sotilmaydi, "
        "faqat tasodifiy taqsimotda tushadi):",
        reply_markup=back_admin_kb("adm:roles"),
    )


@router.message(AdminRole.waiting_price)
async def adm_role_price(message: Message, state: FSMContext):
    if not await is_user_admin(message.from_user.id):
        await state.clear()
        return
    if not message.text.strip().isdigit():
        await message.answer("❌ Faqat raqam yuboring (0 = sotilmaydi).", reply_markup=back_admin_kb("adm:roles"))
        return
    data = await state.get_data()
    role_name = data["name"]
    role_mode = data.get("mode", "classic")

    # Bir xil rejimda bir xil nomli rol allaqachon bormi -- tekshiramiz. Aks holda
    # bitta o'yinda bir xil rol (masalan "Don") ikki marta chiqib qolishi mumkin.
    if await crud.role_name_exists_in_mode(role_name, role_mode):
        await state.clear()
        roles = await crud.get_roles(active_only=False)
        await message.answer(
            f"⚠️ \"{role_name}\" nomli rol \"{role_mode}\" rejimida allaqachon mavjud. "
            "Bir xil rejimda bir xil nomli rolni ikki marta qo'shib bo'lmaydi "
            "(aks holda o'yinda bitta rol ikki kishiga tushib qolishi mumkin). "
            "Boshqa nom bilan qaytadan urinib ko'ring yoki mavjud rolni tahrirlang.",
            reply_markup=role_list_view_kb(roles),
        )
        return

    await crud.create_role(
        name=role_name,
        team=RoleTeam(data["team"]),
        night_action_type=NightActionType(data["action"]),
        description=data["description"],
        max_per_game=data["max_per_game"],
        mode=role_mode,
        is_team_boss=data.get("is_team_boss", False),
        acts_independently=data.get("acts_independently", False),
        dual_check_or_kill=data.get("dual_check_or_kill", False),
        succeeds_role_id=data.get("succeeds_role_id"),
        day_vote_weight=data.get("day_vote_weight", 1),
        night_money_target=data.get("night_money_target"),
        night_money_amount=data.get("night_money_amount", 0),
        day_money_target=data.get("day_money_target"),
        day_money_amount=data.get("day_money_amount", 0),
        wins_when_lynched=data.get("wins_when_lynched", False),
        price_diamond=int(message.text.strip()),
    )
    await state.clear()
    roles = await crud.get_roles(active_only=False)
    await message.answer("✅ Rol qo'shildi!", reply_markup=role_list_view_kb(roles))
