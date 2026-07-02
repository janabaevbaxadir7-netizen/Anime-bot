import datetime
from sqlalchemy import select, func, desc
from database.db import async_session
from database.models import User, Anime, Episode, PremiumRequest


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
