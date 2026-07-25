"""Admin - foydalanuvchi yuborgan chek (olmos to'ldirish so'rovi)ni tasdiqlash/rad etish."""
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery

from database import crud
from database.models import DiamondRequestStatus
from locales.texts import t
from utils.helpers import is_user_admin

router = Router(name="diamond_requests_admin")


@router.callback_query(F.data == "adm:diamond_requests")
async def list_pending_requests(callback: CallbackQuery):
    if not await is_user_admin(callback.from_user.id):
        await callback.answer()
        return
    from database.db import async_session
    from sqlalchemy import select
    from database.models import DiamondTopupRequest

    async with async_session() as s:
        res = await s.execute(
            select(DiamondTopupRequest).where(DiamondTopupRequest.status == DiamondRequestStatus.pending)
        )
        pending = list(res.scalars().all())

    if not pending:
        await callback.answer("✅ Kutilayotgan so'rovlar yo'q.", show_alert=True)
        return

    from keyboards.admin_kb import diamond_request_review_kb
    for req in pending:
        user = await crud.get_user(req.user_id)
        packages = await crud.get_diamond_packages(active_only=False)
        pkg = next((p for p in packages if p.id == req.package_id), None)
        caption = (
            f"🧾 So'rov #{req.id}\n👤 {user.first_name if user else req.user_id} (ID: {req.user_id})\n"
            f"💰 {pkg.price_sum if pkg else '?'} so'm → 💎 {pkg.diamond_amount if pkg else '?'}"
        )
        try:
            await callback.message.answer_photo(
                req.receipt_file_id, caption=caption, reply_markup=diamond_request_review_kb(req.id)
            )
        except Exception:
            pass
    await callback.answer()


@router.callback_query(F.data.startswith("adm:dreq_approve:"))
async def approve_diamond_request(callback: CallbackQuery, bot: Bot):
    if not await is_user_admin(callback.from_user.id):
        await callback.answer()
        return
    req_id = int(callback.data.split(":")[-1])
    req = await crud.review_diamond_request(req_id, approve=True, admin_id=callback.from_user.id)
    if not req:
        await callback.answer("❌ Bu so'rov allaqachon ko'rib chiqilgan.", show_alert=True)
        return

    user = await crud.get_user(req.user_id)
    packages = await crud.get_diamond_packages(active_only=False)
    pkg = next((p for p in packages if p.id == req.package_id), None)

    await callback.message.edit_caption(caption=callback.message.caption + "\n\n✅ TASDIQLANDI")
    try:
        await bot.send_message(
            req.user_id,
            t("diamond_topup_approved_user", user.language, amount=pkg.diamond_amount if pkg else "?"),
        )
    except Exception:
        pass
    await callback.answer("✅ Tasdiqlandi")


@router.callback_query(F.data.startswith("adm:dreq_reject:"))
async def reject_diamond_request(callback: CallbackQuery, bot: Bot):
    if not await is_user_admin(callback.from_user.id):
        await callback.answer()
        return
    req_id = int(callback.data.split(":")[-1])
    req = await crud.review_diamond_request(req_id, approve=False, admin_id=callback.from_user.id)
    if not req:
        await callback.answer("❌ Bu so'rov allaqachon ko'rib chiqilgan.", show_alert=True)
        return

    user = await crud.get_user(req.user_id)
    await callback.message.edit_caption(caption=callback.message.caption + "\n\n❌ RAD ETILDI")
    try:
        await bot.send_message(req.user_id, t("diamond_topup_rejected_user", user.language))
    except Exception:
        pass
    await callback.answer("❌ Rad etildi")
