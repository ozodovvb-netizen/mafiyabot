"""
Guruh a'zoligini kuzatuvchi middleware.

Ilgari bot hech qanday "kim qaysi guruhda faol" degan ro'yxatni saqlamas edi --
shu sabab /paratop kabi "shu GURUHDA ro'yxatdan o'tgan foydalanuvchilar orasidan"
degan buyruqni yozib bo'lmasdi. Bu middleware guruhda yozilgan HAR BIR xabarni
(botlardan tashqari) kuzatib, database/crud.track_group_member() orqali
(chat_id, user_id) juftligini eslab qoladi -- boshqa hech qanday handler ishini
to'xtatmaydi yoki o'zgartirmaydi, faqat orqa fonda yozib qo'yadi.
"""
import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from database import crud

logger = logging.getLogger(__name__)


class GroupMemberTrackerMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(event, Message) and event.chat.type in ("group", "supergroup"):
            user = event.from_user
            if user and not user.is_bot:
                try:
                    await crud.track_group_member(event.chat.id, user.id)
                except Exception:
                    # Kuzatuv muvaffaqiyatsiz bo'lsa ham, asosiy xabar ishlashi to'xtamasin.
                    logger.exception("Guruh a'zosini yozishda xatolik (chat_id=%s)", event.chat.id)
        return await handler(event, data)
