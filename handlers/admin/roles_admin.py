"""Admin - Rollar bo'limi: rol qo'shish/o'chirish, jamoa va tungi harakat turini belgilash."""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from database import crud
from database.models import RoleTeam, NightActionType
from keyboards.admin_kb import list_with_delete_kb, back_admin_kb, role_team_select_kb, role_action_select_kb
from states.states import AdminRole
from utils.helpers import is_user_admin

router = Router(name="roles_admin")


@router.callback_query(F.data == "adm:roles")
async def adm_roles_list(callback: CallbackQuery):
    if not await is_user_admin(callback.from_user.id):
        await callback.answer()
        return
    roles = await crud.get_roles(active_only=False)
    await callback.message.edit_text(
        "🎭 <b>Rollar</b>\n\nO'chirish uchun bosing, yangi qo'shish uchun pastdagi tugma:",
        reply_markup=list_with_delete_kb(roles, "adm_role"),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("adm_role:del:"))
async def adm_role_delete(callback: CallbackQuery):
    role_id = int(callback.data.split(":")[-1])
    await crud.delete_role(role_id)
    roles = await crud.get_roles(active_only=False)
    await callback.message.edit_reply_markup(reply_markup=list_with_delete_kb(roles, "adm_role"))
    await callback.answer("🗑 O'chirildi")


@router.callback_query(F.data == "adm_role:add")
async def adm_role_add_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminRole.waiting_name)
    await callback.message.edit_text(
        "📝 Rol nomini kiriting (masalan: Shergar, Advokat, Jurnalist...):",
        reply_markup=back_admin_kb("adm:roles"),
    )
    await callback.answer()


@router.message(AdminRole.waiting_name)
async def adm_role_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(AdminRole.waiting_team)
    await message.answer("⚔️ Bu rol qaysi jamoaga tegishli?", reply_markup=role_team_select_kb())


@router.callback_query(AdminRole.waiting_team, F.data.startswith("role_team:"))
async def adm_role_team(callback: CallbackQuery, state: FSMContext):
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
    action = callback.data.split(":", 1)[1]
    await state.update_data(action=action)
    await state.set_state(AdminRole.waiting_mode)

    modes = await crud.get_game_modes(active_only=False)
    modes_text = (
        "\n".join(f"• {m.name} ({m.min_players}-{m.max_players} kishi)" for m in modes)
        if modes else "— hozircha maxsus rejim yo'q, faqat \"classic\" mavjud —"
    )
    await callback.message.edit_text(
        "🎲 Bu rol qaysi o'yin rejimiga tegishli? Rejim nomini yozing "
        "(mos rejim bo'lmasa \"classic\" deb yozing):\n\n"
        f"Mavjud rejimlar:\n{modes_text}",
        reply_markup=back_admin_kb("adm:roles"),
    )
    await callback.answer()


@router.message(AdminRole.waiting_mode)
async def adm_role_mode(message: Message, state: FSMContext):
    mode = message.text.strip().lower().strip("'\"“”‘’") or "classic"
    await state.update_data(mode=mode)
    await state.set_state(AdminRole.waiting_description)
    await message.answer(
        "✍️ Rol tavsifini yozing (bu matn foydalanuvchi /roles bosganda ko'radigan tavsif bo'ladi - "
        "'bu rol nima qila oladi'):"
    )


@router.message(AdminRole.waiting_description)
async def adm_role_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text.strip())
    await state.set_state(AdminRole.waiting_max_per_game)
    await message.answer("🔢 Bitta o'yinda bu roldan nechta bo'lishi mumkin? (masalan: 1):")


@router.message(AdminRole.waiting_max_per_game)
async def adm_role_max(message: Message, state: FSMContext):
    if not message.text.strip().isdigit():
        await message.answer("❌ Faqat raqam yuboring.")
        return
    await state.update_data(max_per_game=int(message.text.strip()))
    await state.set_state(AdminRole.waiting_is_boss)

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Ha", callback_data="role_boss:1")
    builder.button(text="❌ Yo'q", callback_data="role_boss:0")
    builder.adjust(2)
    await message.answer(
        "👑 Bu rol o'z JAMOASI uchun \"boshliq\"mi? (Masalan Don - mafiyalar turlicha "
        "nishon tansa ham, OXIRGI qaror shu rolga tegishli bo'ladi):",
        reply_markup=builder.as_markup(),
    )


@router.callback_query(AdminRole.waiting_is_boss, F.data.startswith("role_boss:"))
async def adm_role_boss(callback: CallbackQuery, state: FSMContext):
    await state.update_data(is_team_boss=callback.data.endswith(":1"))
    await state.set_state(AdminRole.waiting_dual_action)

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Ha", callback_data="role_dual:1")
    builder.button(text="❌ Yo'q", callback_data="role_dual:0")
    builder.adjust(2)
    await callback.message.edit_text(
        "🔀 Bu rol har kecha \"Tekshirish\" yoki \"Otish\" dan birini o'zi tanlab harakat "
        "qiladimi? (Masalan Komissar - xohlasa tekshiradi, xohlasa o'ldiradi):",
        reply_markup=builder.as_markup(),
    )
    await callback.answer()


@router.callback_query(AdminRole.waiting_dual_action, F.data.startswith("role_dual:"))
async def adm_role_dual(callback: CallbackQuery, state: FSMContext):
    await state.update_data(dual_check_or_kill=callback.data.endswith(":1"))
    await state.set_state(AdminRole.waiting_succeeds)

    roles = await crud.get_roles(active_only=False)
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="➖ Hech kimning o'rnini bosmaydi", callback_data="role_succ:0")
    for r in roles:
        builder.button(text=f"{r.emoji} {r.name}", callback_data=f"role_succ:{r.id}")
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
    succ_id = int(callback.data.split(":")[-1])
    data = await state.get_data()
    await crud.create_role(
        name=data["name"],
        team=RoleTeam(data["team"]),
        night_action_type=NightActionType(data["action"]),
        description=data["description"],
        max_per_game=data["max_per_game"],
        mode=data.get("mode", "classic"),
        is_team_boss=data.get("is_team_boss", False),
        dual_check_or_kill=data.get("dual_check_or_kill", False),
        succeeds_role_id=succ_id or None,
    )
    await state.clear()
    roles = await crud.get_roles(active_only=False)
    await callback.message.edit_text("✅ Rol qo'shildi!", reply_markup=list_with_delete_kb(roles, "adm_role"))
    await callback.answer()
