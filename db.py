from datetime import datetime
from sqlalchemy import select, func, update, delete
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import selectinload

from models import Base, User, Anime, Episode, MandatoryChannel, Settings, Feedback
import config

engine = create_async_engine(f"sqlite+aiosqlite:///{config.DB_PATH}")
async_session = async_sessionmaker(engine, expire_on_commit=False)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_session() as session:
        existing = await session.get(Settings, "mandatory_sub")
        if not existing:
            session.add(Settings(key="mandatory_sub", value="on"))
            await session.commit()


async def get_or_create_user(user_id: int, full_name: str, username: str) -> tuple[User, bool]:
    async with async_session() as session:
        user = await session.get(User, user_id)
        if user:
            return user, False
        user = User(id=user_id, full_name=full_name or "", username=username or "")
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user, True


async def set_user_gender(user_id: int, gender: str):
    async with async_session() as session:
        await session.execute(update(User).where(User.id == user_id).values(gender=gender))
        await session.commit()


async def get_user(user_id: int) -> User | None:
    async with async_session() as session:
        return await session.get(User, user_id)


async def set_user_progress(user_id: int, anime_id: int, episode_num: int):
    async with async_session() as session:
        await session.execute(
            update(User).where(User.id == user_id).values(
                last_anime_id=anime_id, last_episode_num=episode_num
            )
        )
        await session.commit()


async def count_users() -> int:
    async with async_session() as session:
        result = await session.execute(select(func.count(User.id)))
        return result.scalar_one()


async def count_users_today() -> int:
    async with async_session() as session:
        today = datetime.utcnow().date()
        result = await session.execute(
            select(func.count(User.id)).where(func.date(User.joined_at) == str(today))
        )
        return result.scalar_one()


async def all_user_ids() -> list[int]:
    async with async_session() as session:
        result = await session.execute(select(User.id).where(User.is_blocked == False))
        return [row[0] for row in result.all()]


async def create_anime(code: str, title: str) -> Anime:
    async with async_session() as session:
        anime = Anime(code=code, title=title)
        session.add(anime)
        await session.commit()
        await session.refresh(anime)
        return anime


async def get_next_code() -> str:
    async with async_session() as session:
        result = await session.execute(select(func.max(Anime.id)))
        max_id = result.scalar_one() or 0
        return str(101 + max_id)


async def get_anime_by_code(code: str) -> Anime | None:
    async with async_session() as session:
        result = await session.execute(
            select(Anime).options(selectinload(Anime.episodes)).where(Anime.code == code.strip())
        )
        return result.scalar_one_or_none()


async def get_anime_by_id(anime_id: int) -> Anime | None:
    async with async_session() as session:
        result = await session.execute(
            select(Anime).options(selectinload(Anime.episodes)).where(Anime.id == anime_id)
        )
        return result.scalar_one_or_none()


async def increment_search_count(anime_id: int):
    async with async_session() as session:
        await session.execute(
            update(Anime).where(Anime.id == anime_id).values(search_count=Anime.search_count + 1)
        )
        await session.commit()


async def add_episode(anime_id: int, file_id: str, caption: str = "") -> int:
    async with async_session() as session:
        result = await session.execute(
            select(func.max(Episode.episode_num)).where(Episode.anime_id == anime_id)
        )
        max_num = result.scalar_one() or 0
        new_num = max_num + 1
        ep = Episode(anime_id=anime_id, episode_num=new_num, file_id=file_id, caption=caption)
        session.add(ep)
        await session.commit()
        return new_num


async def get_episode(anime_id: int, episode_num: int) -> Episode | None:
    async with async_session() as session:
        result = await session.execute(
            select(Episode).where(
                Episode.anime_id == anime_id, Episode.episode_num == episode_num
            )
        )
        return result.scalar_one_or_none()


async def rate_anime(anime_id: int, like: bool):
    async with async_session() as session:
        if like:
            await session.execute(
                update(Anime).where(Anime.id == anime_id).values(likes=Anime.likes + 1)
            )
        else:
            await session.execute(
                update(Anime).where(Anime.id == anime_id).values(dislikes=Anime.dislikes + 1)
            )
        await session.commit()


async def top_anime(limit: int = 5) -> list[Anime]:
    async with async_session() as session:
        result = await session.execute(
            select(Anime).order_by(Anime.search_count.desc()).limit(limit)
        )
        return list(result.scalars().all())


async def list_all_anime() -> list[Anime]:
    async with async_session() as session:
        result = await session.execute(select(Anime).order_by(Anime.id.desc()))
        return list(result.scalars().all())


async def delete_anime(anime_id: int):
    async with async_session() as session:
        await session.execute(delete(Episode).where(Episode.anime_id == anime_id))
        await session.execute(delete(Anime).where(Anime.id == anime_id))
        await session.commit()


async def count_anime_and_episodes() -> tuple[int, int]:
    async with async_session() as session:
        a = (await session.execute(select(func.count(Anime.id)))).scalar_one()
        e = (await session.execute(select(func.count(Episode.id)))).scalar_one()
        return a, e


async def total_likes_dislikes() -> tuple[int, int]:
    async with async_session() as session:
        l = (await session.execute(select(func.sum(Anime.likes)))).scalar_one() or 0
        d = (await session.execute(select(func.sum(Anime.dislikes)))).scalar_one() or 0
        return l, d


async def add_channel(chat_id: str, title: str, url: str) -> MandatoryChannel:
    async with async_session() as session:
        ch = MandatoryChannel(chat_id=chat_id, title=title, url=url)
        session.add(ch)
        await session.commit()
        await session.refresh(ch)
        return ch


async def get_all_channels() -> list[MandatoryChannel]:
    async with async_session() as session:
        result = await session.execute(select(MandatoryChannel))
        return list(result.scalars().all())


async def delete_channel(channel_id: int):
    async with async_session() as session:
        await session.execute(delete(MandatoryChannel).where(MandatoryChannel.id == channel_id))
        await session.commit()


async def get_setting(key: str, default: str = "") -> str:
    async with async_session() as session:
        row = await session.get(Settings, key)
        return row.value if row else default


async def set_setting(key: str, value: str):
    async with async_session() as session:
        row = await session.get(Settings, key)
        if row:
            row.value = value
        else:
            session.add(Settings(key=key, value=value))
        await session.commit()


async def is_mandatory_sub_on() -> bool:
    return await get_setting("mandatory_sub", "on") == "on"


async def add_feedback(user_id: int, user_name: str, text: str) -> Feedback:
    async with async_session() as session:
        fb = Feedback(user_id=user_id, user_name=user_name, text=text)
        session.add(fb)
        await session.commit()
        await session.refresh(fb)
        return fb


async def count_feedback() -> int:
    async with async_session() as session:
        result = await session.execute(select(func.count(Feedback.id)))
        return result.scalar_one()
