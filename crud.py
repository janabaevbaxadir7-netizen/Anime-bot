import datetime
from sqlalchemy import select, func, desc, update, delete
from db import async_session
from models import (
    User, Anime, Episode, PremiumRequest, Channel, Admin, Feedback, PostChannel,
    ResponsibleAdmin, ExternalLink,
)
import config


# ==================== USER ====================

async def add_user(tg_id: int, full_name: str, username: str) -> bool:
    """Yangi foydalanuvchini qo'shadi. Agar allaqachon bor bo'lsa False qaytaradi."""
    async with async_session() as session:
        result = await session.execute(select(User).where(User.tg_id == tg_id))
        user = result.scalar_one_or_none()
        if user:
            return False
        session.add(User(tg_id=tg_id, full_name=full_name, username=username or ""))
        await session.commit()
        return True


async def get_user(tg_id: int) -> User | None:
    async with async_session() as session:
        result = await session.execute(select(User).where(User.tg_id == tg_id))
        return result.scalar_one_or_none()


async def is_premium(tg_id: int) -> bool:
    user = await get_user(tg_id)
    if not user or not user.is_premium:
        return False
    if user.premium_until and user.premium_until < datetime.datetime.utcnow():
        return False
    return True


async def set_premium(tg_id: int, until: datetime.datetime) -> bool:
    async with async_session() as session:
        result = await session.execute(select(User).where(User.tg_id == tg_id))
        user = result.scalar_one_or_none()
        if not user:
            return False
        user.is_premium = True
        user.premium_until = until
        await session.commit()
        return True


async def remove_premium(tg_id: int) -> bool:
    async with async_session() as session:
        result = await session.execute(select(User).where(User.tg_id == tg_id))
        user = result.scalar_one_or_none()
        if not user:
            return False
        user.is_premium = False
        user.premium_until = None
        await session.commit()
        return True


async def set_premium_days(tg_id: int, days: int) -> bool:
    """Admin shaxsan kelishib olgandan so'ng, N kunlik Premium beradi."""
    until = datetime.datetime.utcnow() + datetime.timedelta(days=days)
    return await set_premium(tg_id, until)


async def all_user_ids() -> list[int]:
    async with async_session() as session:
        result = await session.execute(select(User.tg_id).where(User.is_blocked == False))
        return [row[0] for row in result.all()]


async def mark_user_blocked(tg_id: int):
    async with async_session() as session:
        await session.execute(update(User).where(User.tg_id == tg_id).values(is_blocked=True))
        await session.commit()


async def find_user(query: str) -> User | None:
    """ID (raqam) yoki @username orqali foydalanuvchini topadi."""
    query = query.strip().lstrip("@")
    async with async_session() as session:
        if query.isdigit():
            result = await session.execute(select(User).where(User.tg_id == int(query)))
        else:
            result = await session.execute(select(User).where(User.username.ilike(query)))
        return result.scalar_one_or_none()


# ==================== STATISTIKA ====================

async def get_stats() -> dict:
    async with async_session() as session:
        total_users = await session.scalar(select(func.count(User.id)))
        today = datetime.datetime.utcnow().date()
        today_users = await session.scalar(
            select(func.count(User.id)).where(func.date(User.joined_at) == today)
        )
        premium_count = await session.scalar(select(func.count(User.id)).where(User.is_premium == True))
        anime_count = await session.scalar(select(func.count(Anime.id)))
        episode_count = await session.scalar(select(func.count(Episode.id)))
        return {
            "total_users": total_users or 0,
            "today_users": today_users or 0,
            "premium_count": premium_count or 0,
            "anime_count": anime_count or 0,
            "episode_count": episode_count or 0,
        }


# ==================== ANIME ====================

async def get_anime_by_code(code: int) -> Anime | None:
    async with async_session() as session:
        result = await session.execute(select(Anime).where(Anime.code == code))
        return result.scalar_one_or_none()


async def search_anime_by_title(title: str) -> list[Anime]:
    async with async_session() as session:
        result = await session.execute(
            select(Anime).where(Anime.title.ilike(f"%{title}%")).limit(15)
        )
        return list(result.scalars().all())


async def get_random_animes(limit: int = 15) -> list[Anime]:
    async with async_session() as session:
        result = await session.execute(
            select(Anime).order_by(func.random()).limit(limit)
        )
        return list(result.scalars().all())


async def get_top_animes(limit: int = 15) -> list[Anime]:
    async with async_session() as session:
        result = await session.execute(
            select(Anime).order_by(desc(Anime.downloads)).limit(limit)
        )
        return list(result.scalars().all())


async def get_last_animes(limit: int = 15) -> list[Anime]:
    async with async_session() as session:
        result = await session.execute(
            select(Anime).order_by(desc(Anime.created_at)).limit(limit)
        )
        return list(result.scalars().all())


async def add_anime(code: int, title: str, description: str = "", is_premium: bool = False) -> Anime:
    async with async_session() as session:
        anime = Anime(code=code, title=title, description=description, is_premium=is_premium)
        session.add(anime)
        await session.commit()
        await session.refresh(anime)
        return anime


async def get_next_code() -> int:
    """Har doim eng katta koddan +1 qiladi (yoki bo'sh bo'lsa 101 dan boshlaydi)."""
    async with async_session() as session:
        max_code = await session.scalar(select(func.max(Anime.code)))
        return (max_code or 100) + 1


async def get_anime_by_id(anime_id: int) -> Anime | None:
    async with async_session() as session:
        return await session.get(Anime, anime_id)


def is_anime_currently_premium(anime: Anime) -> bool:
    """Anime hozirgi vaqtda haqiqatan ham Premium hisoblanadimi (muddati o'tmaganmi)."""
    if not anime.is_premium:
        return False
    if anime.premium_free_at and anime.premium_free_at <= datetime.datetime.utcnow():
        return False
    return True


async def set_anime_premium(anime_id: int, days: int | None) -> bool:
    """Animeni Premium qiladi. days=None yoki 0 -> doimiy Premium. days>0 -> shuncha kundan keyin hammaga tekin bo'ladi."""
    async with async_session() as session:
        anime = await session.get(Anime, anime_id)
        if not anime:
            return False
        anime.is_premium = True
        anime.premium_free_at = (
            datetime.datetime.utcnow() + datetime.timedelta(days=days) if days else None
        )
        await session.commit()
        return True


async def unset_anime_premium(anime_id: int) -> bool:
    """Animedan Premium belgisini butunlay olib tashlaydi (hammaga tekin bo'ladi)."""
    async with async_session() as session:
        anime = await session.get(Anime, anime_id)
        if not anime:
            return False
        anime.is_premium = False
        anime.premium_free_at = None
        await session.commit()
        return True


async def list_all_anime() -> list[Anime]:
    async with async_session() as session:
        result = await session.execute(select(Anime).order_by(desc(Anime.created_at)))
        return list(result.scalars().all())


async def update_anime_title(anime_id: int, title: str):
    async with async_session() as session:
        await session.execute(update(Anime).where(Anime.id == anime_id).values(title=title))
        await session.commit()


async def update_anime_description(anime_id: int, description: str):
    async with async_session() as session:
        await session.execute(update(Anime).where(Anime.id == anime_id).values(description=description))
        await session.commit()


async def update_anime_cover(anime_id: int, file_id: str):
    async with async_session() as session:
        await session.execute(update(Anime).where(Anime.id == anime_id).values(cover_file_id=file_id))
        await session.commit()


async def update_anime_trailer(anime_id: int, file_id: str):
    async with async_session() as session:
        await session.execute(update(Anime).where(Anime.id == anime_id).values(trailer_file_id=file_id))
        await session.commit()


async def delete_anime(anime_id: int):
    """Animeni va unga tegishli BARCHA qismlarni (episodes) o'chiradi.
    Eslatma: bu yerda avval episodlar aniq o'chiriladi, chunki Core `delete()`
    ORM darajasidagi cascade="all, delete-orphan" qoidasini ishga tushirmaydi —
    shu sabab avval bu joyda "etim" qismlar bazada qolib ketardi."""
    async with async_session() as session:
        await session.execute(delete(Episode).where(Episode.anime_id == anime_id))
        await session.execute(delete(Anime).where(Anime.id == anime_id))
        await session.commit()


async def increment_downloads(anime_id: int):
    async with async_session() as session:
        result = await session.execute(select(Anime).where(Anime.id == anime_id))
        anime = result.scalar_one_or_none()
        if anime:
            anime.downloads += 1
            await session.commit()


# ==================== EPISODES ====================

async def add_episode(anime_id: int, part_number: int, file_id: str) -> Episode:
    async with async_session() as session:
        ep = Episode(anime_id=anime_id, part_number=part_number, file_id=file_id)
        session.add(ep)
        await session.commit()
        await session.refresh(ep)
        return ep


async def get_episodes(anime_id: int) -> list[Episode]:
    async with async_session() as session:
        result = await session.execute(
            select(Episode).where(Episode.anime_id == anime_id).order_by(Episode.part_number)
        )
        return list(result.scalars().all())


async def get_episode(anime_id: int, part_number: int) -> Episode | None:
    async with async_session() as session:
        result = await session.execute(
            select(Episode).where(
                Episode.anime_id == anime_id, Episode.part_number == part_number
            )
        )
        return result.scalar_one_or_none()


async def delete_episode(anime_id: int, part_number: int):
    async with async_session() as session:
        await session.execute(
            delete(Episode).where(Episode.anime_id == anime_id, Episode.part_number == part_number)
        )
        await session.commit()


# ==================== PREMIUM SO'ROVLAR ====================

async def add_premium_request(tg_id: int, full_name: str) -> PremiumRequest:
    async with async_session() as session:
        req = PremiumRequest(tg_id=tg_id, full_name=full_name)
        session.add(req)
        await session.commit()
        await session.refresh(req)
        return req


async def get_pending_requests() -> list[PremiumRequest]:
    async with async_session() as session:
        result = await session.execute(
            select(PremiumRequest).where(PremiumRequest.status == "pending")
        )
        return list(result.scalars().all())


async def update_request_status(request_id: int, status: str):
    async with async_session() as session:
        result = await session.execute(select(PremiumRequest).where(PremiumRequest.id == request_id))
        req = result.scalar_one_or_none()
        if req:
            req.status = status
            await session.commit()


# ==================== KANALLAR (majburiy obuna) ====================

async def add_channel(chat_id: str, title: str, url: str) -> Channel:
    async with async_session() as session:
        ch = Channel(chat_id=chat_id, title=title, url=url)
        session.add(ch)
        await session.commit()
        await session.refresh(ch)
        return ch


async def get_all_channels() -> list[Channel]:
    async with async_session() as session:
        result = await session.execute(select(Channel))
        return list(result.scalars().all())


async def delete_channel(channel_id: int):
    async with async_session() as session:
        await session.execute(delete(Channel).where(Channel.id == channel_id))
        await session.commit()


# ==================== POST KANALLARI (tez tanlash ro'yxati) ====================

async def add_or_update_post_channel(chat_id: str, title: str) -> PostChannel:
    """Kanalni ro'yxatga qo'shadi. Agar shu chat_id allaqachon bor bo'lsa — sarlavhasini yangilab, o'shani qaytaradi."""
    async with async_session() as session:
        result = await session.execute(select(PostChannel).where(PostChannel.chat_id == chat_id))
        ch = result.scalar_one_or_none()
        if ch:
            if title:
                ch.title = title
            await session.commit()
            await session.refresh(ch)
            return ch
        ch = PostChannel(chat_id=chat_id, title=title)
        session.add(ch)
        await session.commit()
        await session.refresh(ch)
        return ch


async def get_all_post_channels() -> list[PostChannel]:
    async with async_session() as session:
        result = await session.execute(select(PostChannel).order_by(PostChannel.added_at))
        return list(result.scalars().all())


async def get_post_channels_by_ids(ids: list[int]) -> list[PostChannel]:
    if not ids:
        return []
    async with async_session() as session:
        result = await session.execute(select(PostChannel).where(PostChannel.id.in_(ids)))
        return list(result.scalars().all())


async def delete_post_channel(channel_id: int):
    async with async_session() as session:
        await session.execute(delete(PostChannel).where(PostChannel.id == channel_id))
        await session.commit()


# ==================== ADMINLAR (dinamik, ruxsatlar bilan) ====================

async def add_admin(tg_id: int, full_name: str, added_by: int, permissions: str = "anime,channels,broadcast,premium,posts") -> bool:
    async with async_session() as session:
        existing = await session.get(Admin, tg_id)
        if existing:
            return False
        session.add(Admin(id=tg_id, full_name=full_name or "", added_by=added_by, permissions=permissions))
        await session.commit()
        return True


async def remove_admin(tg_id: int) -> bool:
    async with async_session() as session:
        existing = await session.get(Admin, tg_id)
        if not existing:
            return False
        await session.execute(delete(Admin).where(Admin.id == tg_id))
        await session.commit()
        return True


async def get_admin(tg_id: int) -> Admin | None:
    async with async_session() as session:
        return await session.get(Admin, tg_id)


async def list_admins() -> list[Admin]:
    async with async_session() as session:
        result = await session.execute(select(Admin))
        return list(result.scalars().all())


async def set_admin_permissions(tg_id: int, permissions: str):
    async with async_session() as session:
        await session.execute(update(Admin).where(Admin.id == tg_id).values(permissions=permissions))
        await session.commit()


# ==================== MUROJAATLAR ====================

async def add_feedback(tg_id: int, full_name: str, text: str) -> Feedback:
    async with async_session() as session:
        fb = Feedback(tg_id=tg_id, full_name=full_name, text=text)
        session.add(fb)
        await session.commit()
        await session.refresh(fb)
        return fb


async def get_feedback_list(page: int = 0, per_page: int = 5) -> list[Feedback]:
    async with async_session() as session:
        result = await session.execute(
            select(Feedback).order_by(desc(Feedback.created_at)).offset(page * per_page).limit(per_page)
        )
        return list(result.scalars().all())


async def count_feedback() -> int:
    async with async_session() as session:
        return await session.scalar(select(func.count(Feedback.id))) or 0


# ==================== SAQLANGAN ANIMELAR ====================

async def save_anime_for_user(tg_id: int, code: int) -> bool:
    async with async_session() as session:
        result = await session.execute(select(User).where(User.tg_id == tg_id))
        user = result.scalar_one_or_none()
        if not user:
            return False
        codes = [c for c in user.saved_codes.split(",") if c]
        if str(code) in codes:
            return False
        codes.append(str(code))
        user.saved_codes = ",".join(codes)
        await session.commit()
        return True


async def get_saved_animes(tg_id: int) -> list[Anime]:
    user = await get_user(tg_id)
    if not user or not user.saved_codes:
        return []
    codes = [int(c) for c in user.saved_codes.split(",") if c]
    async with async_session() as session:
        result = await session.execute(select(Anime).where(Anime.code.in_(codes)))
        return list(result.scalars().all())


# ==================== MAS'UL ADMINLAR (reklama / yordam / premium) ====================

async def get_responsible_admin(role: str) -> int:
    """Berilgan soha ("ads"/"help"/"premium") uchun mas'ul admin ID sini qaytaradi.
    Agar hali belgilanmagan bo'lsa — standart bo'yicha 1-bosh admin qaytadi."""
    async with async_session() as session:
        ra = await session.get(ResponsibleAdmin, role)
        if ra:
            return ra.admin_id
    return config.ADMIN_IDS[0] if config.ADMIN_IDS else 0


async def set_responsible_admin(role: str, admin_id: int):
    async with async_session() as session:
        ra = await session.get(ResponsibleAdmin, role)
        if ra:
            ra.admin_id = admin_id
        else:
            session.add(ResponsibleAdmin(role=role, admin_id=admin_id))
        await session.commit()


# ==================== TASHQI LINKLAR (Instagram, YouTube va h.k.) ====================

async def add_external_link(title: str, url: str) -> ExternalLink:
    async with async_session() as session:
        link = ExternalLink(title=title, url=url)
        session.add(link)
        await session.commit()
        await session.refresh(link)
        return link


async def get_all_external_links() -> list[ExternalLink]:
    async with async_session() as session:
        result = await session.execute(select(ExternalLink))
        return list(result.scalars().all())


async def delete_external_link(link_id: int):
    async with async_session() as session:
        await session.execute(delete(ExternalLink).where(ExternalLink.id == link_id))
        await session.commit()
