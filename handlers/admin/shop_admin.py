"""Admin - Do'kon bo'limi: himoya buyumlarini qo'shish/o'chirish."""
import logging

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from database import crud
from database.models import ProtectionType
from keyboards.admin_kb import list_with_delete_kb, back_admin_kb, protection_type_select_kb
from states.states import AdminShopItem
from utils.helpers import is_user_admin

router = Router(name="shop_admin")
logger = logging.getLogger(__name__)

PROTECTION_EMOJI = {
    "himoya": "🛡", "hujjat": "📄", "osishdan_himoya": "🪂", "qotildan_himoya": "🩸",
    "miltiq": "🔫", "doridan_himoya": "🧪", "maska": "🎭",
    "sirpanishdan_himoya": "🥷", "qahramon_himoyasi": "📗",
}


@router.callback_query(F.data == "adm:shop")
async def adm_shop_list(callback: CallbackQuery):
    if not await is_user_admin(callback.from_user.id):
        await callback.answer()
        return
    items = await crud.get_shop_items(active_only=False)
    text = "🛒 <b>Do'kon buyumlari</b>\n\nO'chirish uchun bosing, yangi qo'shish uchun pastdagi tugma:"
    await callback.message.edit_text(text, reply_markup=list_with_delete_kb(items, "adm_shop"))
    await callback.answer()


@router.callback_query(F.data.startswith("adm_shop:del:"))
async def adm_shop_delete(callback: CallbackQuery):
    if not await is_user_admin(callback.from_user.id):
        await callback.answer()
        return
    item_id = int(callback.data.split(":")[-1])
    await crud.delete_shop_item(item_id)
    items = await crud.get_shop_items(active_only=False)
    await callback.message.edit_reply_markup(reply_markup=list_with_delete_kb(items, "adm_shop"))
    await callback.answer("🗑 O'chirildi")


@router.callback_query(F.data == "adm_shop:add")
async def adm_shop_add_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminShopItem.waiting_name)
    await callback.message.edit_text("📝 Buyum nomini kiriting (masalan: Bronjilet):", reply_markup=back_admin_kb("adm:shop"))
    await callback.answer()


@router.message(AdminShopItem.waiting_name)
async def adm_shop_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(AdminShopItem.waiting_protection_type)
    await message.answer("🛡 Bu buyum nimadan himoya qiladi? Turini tanlang:", reply_markup=protection_type_select_kb())


@router.callback_query(AdminShopItem.waiting_protection_type, F.data.startswith("protection_type:"))
async def adm_shop_protection_type(callback: CallbackQuery, state: FSMContext):
    p_type = callback.data.split(":", 1)[1]
    await state.update_data(protection_type=p_type)
    await state.set_state(AdminShopItem.waiting_description)
    await callback.message.edit_text(
        "✍️ Bu buyum haqida tavsif yozing (foydalanuvchi ko'radigan matn - nimadan himoya qilishi):"
    )
    await callback.answer()


@router.message(AdminShopItem.waiting_description)
async def adm_shop_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text.strip())
    await state.set_state(AdminShopItem.waiting_price_money)
    await message.answer("💵 Narxini Dollarda kiriting (agar Olmosda sotilsa 0 yozing):")


@router.message(AdminShopItem.waiting_price_money)
async def adm_shop_price_money(message: Message, state: FSMContext):
    if not message.text.strip().isdigit():
        await message.answer("❌ Faqat raqam yuboring.")
        return
    await state.update_data(price_money=int(message.text.strip()))
    await state.set_state(AdminShopItem.waiting_price_diamond)
    await message.answer("💎 Narxini Olmosda kiriting (agar Dollarda sotilsa 0 yozing):")


@router.message(AdminShopItem.waiting_price_diamond)
async def adm_shop_price_diamond(message: Message, state: FSMContext):
    if not message.text.strip().isdigit():
        await message.answer("❌ Faqat raqam yuboring.")
        return
    await state.update_data(price_diamond=int(message.text.strip()))
    await state.set_state(AdminShopItem.waiting_category)
    await message.answer(
        "📂 Bu buyum qaysi Xarid qilish tugmasida ko'rinsin?\n"
        "Qo'shtirnoqsiz shundan birini yozing: himoya | qurol | umumiy\n"
        "(umumiy — faqat Do'kon bo'limida ko'rinadi):"
    )


@router.message(AdminShopItem.waiting_category)
async def adm_shop_category(message: Message, state: FSMContext):
    category = message.text.strip().lower().strip("'\"“”‘’")
    if category not in ("himoya", "qurol", "umumiy"):
        await message.answer("❌ Faqat himoya, qurol yoki umumiy deb yozing (qo'shtirnoqsiz).")
        return

    data = await state.get_data()
    emoji = PROTECTION_EMOJI.get(data["protection_type"], "🛡")

    try:
        await crud.create_shop_item(
            name=data["name"],
            emoji=emoji,
            protection_type=ProtectionType(data["protection_type"]),
            description=data["description"],
            price_money=data["price_money"],
            price_diamond=data["price_diamond"],
            category=category,
        )
    except Exception:
        logger.exception("Do'kon buyumini qo'shishda xatolik")
        await state.clear()
        await message.answer("❌ Buyumni qo'shishda xatolik yuz berdi. Qaytadan urinib ko'ring: /admin")
        return

    await state.clear()
    items = await crud.get_shop_items(active_only=False)
    await message.answer("✅ Buyum qo'shildi!", reply_markup=list_with_delete_kb(items, "adm_shop"))
