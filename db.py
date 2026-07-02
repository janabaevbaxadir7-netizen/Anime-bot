from datetime import datetime
from sqlalchemy import select, func, update, delete, or_
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import selectinload
from models import Base, User, Anime, Episode, MandatoryChannel, Settings, Feedback, PremiumRequest, Admin
import config

engine = create_async_engine(f"sqlite+aiosqlite:///{config.DB_PATH}")
async_session = async_sessionmaker(engine, expire_on_commit=False)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_session() as s:
        if not await s.get(Settings, "mandatory_sub"):
            s.add(Settings(key="mandatory_sub", value="on"))
            await s.commit()


# ── USER ──
async def get_or_create_user(uid, full_name, username):
    async with async_session() as s:
        u = await s.get(User, uid)
        if u:
            return u, False
        u = User(id=uid, full_name=full_name or "", username=username or "")
        s.add(u); await s.commit(); await s.refresh(u)
        return u, True

async def set_user_gender(uid, gender):
    async with async_session() as s:
        await s.execute(update(User).where(User.id==uid).values(gender=gender))
        await s.commit()

async def get_user(uid):
    async with async_session() as s:
        return await s.get(User, uid)

async def set_user_progress(uid, anime_id, ep_num):
    async with async_session() as s:
        await s.execute(update(User).where(User.id==uid).values(last_anime_id=anime_id, last_episode_num=ep_num))
        await s.commit()

async def set_last_menu_msg(uid, msg_id):
    async with async_session() as s:
        await s.execute(update(User).where(User.id==uid).values(last_menu_msg_id=msg_id))
        await s.commit()

async def set_user_premium(uid, is_premium: bool, until: str = ""):
    async with async_session() as s:
        await s.execute(update(User).where(User.id==uid).values(is_premium=is_premium, premium_until=until))
        await s.commit()

async def count_users():
    async with async_session() as s:
        return (await s.execute(select(func.count(User.id)))).scalar_one()

async def count_users_today():
    async with async_session() as s:
        today = str(datetime.utcnow().date())
        return (await s.execute(select(func.count(User.id)).where(func.date(User.joined_at)==today))).scalar_one()

async def count_premium_users():
    async with async_session() as s:
        return (await s.execute(select(func.count(User.id)).where(User.is_premium==True))).scalar_one()

async def all_user_ids():
    async with async_session() as s:
        r = await s.execute(select(User.id).where(User.is_blocked==False))
        return [row[0] for row in r.all()]

async def mark_user_blocked(uid):
    async with async_session() as s:
        await s.execute(update(User).where(User.id==uid).values(is_blocked=True))
        await s.commit()


# ── ANIME ──
async def create_anime(code, title):
    async with async_session() as s:
        a = Anime(code=code, title=title)
        s.add(a); await s.commit(); await s.refresh(a)
        return a

async def get_next_code():
    async with async_session() as s:
        max_id = (await s.execute(select(func.max(Anime.id)))).scalar_one() or 0
        return str(101 + max_id)

async def get_anime_by_code(code):
    async with async_session() as s:
        r = await s.execute(select(Anime).options(selectinload(Anime.episodes)).where(Anime.code==code.strip()))
        return r.scalar_one_or_none()

async def get_anime_by_id(anime_id):
    async with async_session() as s:
        r = await s.execute(select(Anime).options(selectinload(Anime.episodes)).where(Anime.id==anime_id))
        return r.scalar_one_or_none()

async def search_anime_by_title(query):
    async with async_session() as s:
        r = await s.execute(
            select(Anime).options(selectinload(Anime.episodes))
            .where(Anime.title.ilike(f"%{query}%"))
            .order_by(Anime.search_count.desc()).limit(1)
        )
        return r.scalar_one_or_none()

async def search_anime_list(query, limit=5):
    async with async_session() as s:
        r = await s.execute(
            select(Anime).options(selectinload(Anime.episodes))
            .where(or_(Anime.title.ilike(f"%{query}%"), Anime.code==query))
            .order_by(Anime.search_count.desc()).limit(limit)
        )
        return list(r.scalars().all())

async def increment_search_count(anime_id):
    async with async_session() as s:
        await s.execute(update(Anime).where(Anime.id==anime_id).values(search_count=Anime.search_count+1))
        await s.commit()

async def update_anime_title(anime_id, title):
    async with async_session() as s:
        await s.execute(update(Anime).where(Anime.id==anime_id).values(title=title))
        await s.commit()

async def update_anime_cover(anime_id, file_id):
    async with async_session() as s:
        await s.execute(update(Anime).where(Anime.id==anime_id).values(cover_file_id=file_id))
        await s.commit()

async def update_anime_description(anime_id, description):
    async with async_session() as s:
        await s.execute(update(Anime).where(Anime.id==anime_id).values(description=description))
        await s.commit()

async def add_episode(anime_id, file_id, caption=""):
    async with async_session() as s:
        max_num = (await s.execute(select(func.max(Episode.episode_num)).where(Episode.anime_id==anime_id))).scalar_one() or 0
        new_num = max_num + 1
        s.add(Episode(anime_id=anime_id, episode_num=new_num, file_id=file_id, caption=caption))
        await s.commit()
        return new_num

async def get_episode(anime_id, ep_num):
    async with async_session() as s:
        r = await s.execute(select(Episode).where(Episode.anime_id==anime_id, Episode.episode_num==ep_num))
        return r.scalar_one_or_none()

async def delete_episode(anime_id, ep_num):
    async with async_session() as s:
        await s.execute(delete(Episode).where(Episode.anime_id==anime_id, Episode.episode_num==ep_num))
        await s.commit()

async def rate_anime(anime_id, like: bool):
    async with async_session() as s:
        if like:
            await s.execute(update(Anime).where(Anime.id==anime_id).values(likes=Anime.likes+1))
        else:
            await s.execute(update(Anime).where(Anime.id==anime_id).values(dislikes=Anime.dislikes+1))
        await s.commit()

async def top_anime(limit=5):
    async with async_session() as s:
        r = await s.execute(select(Anime).order_by(Anime.search_count.desc()).limit(limit))
        return list(r.scalars().all())

async def list_all_anime():
    async with async_session() as s:
        r = await s.execute(select(Anime).options(selectinload(Anime.episodes)).order_by(Anime.id.desc()))
        return list(r.scalars().all())

async def delete_anime(anime_id):
    async with async_session() as s:
        await s.execute(delete(Episode).where(Episode.anime_id==anime_id))
        await s.execute(delete(Anime).where(Anime.id==anime_id))
        await s.commit()

async def count_anime_and_episodes():
    async with async_session() as s:
        a = (await s.execute(select(func.count(Anime.id)))).scalar_one()
        e = (await s.execute(select(func.count(Episode.id)))).scalar_one()
        return a, e

async def total_likes_dislikes():
    async with async_session() as s:
        l = (await s.execute(select(func.sum(Anime.likes)))).scalar_one() or 0
        d = (await s.execute(select(func.sum(Anime.dislikes)))).scalar_one() or 0
        return l, d


# ── CHANNELS ──
async def add_channel(chat_id, title, url):
    async with async_session() as s:
        ch = MandatoryChannel(chat_id=chat_id, title=title, url=url)
        s.add(ch); await s.commit(); await s.refresh(ch)
        return ch

async def get_all_channels():
    async with async_session() as s:
        r = await s.execute(select(MandatoryChannel))
        return list(r.scalars().all())

async def delete_channel(ch_id):
    async with async_session() as s:
        await s.execute(delete(MandatoryChannel).where(MandatoryChannel.id==ch_id))
        await s.commit()


# ── SETTINGS ──
async def get_setting(key, default=""):
    async with async_session() as s:
        row = await s.get(Settings, key)
        return row.value if row else default

async def set_setting(key, value):
    async with async_session() as s:
        row = await s.get(Settings, key)
        if row:
            row.value = value
        else:
            s.add(Settings(key=key, value=value))
        await s.commit()

async def is_mandatory_sub_on():
    return await get_setting("mandatory_sub", "on") == "on"


# ── FEEDBACK ──
async def add_feedback(uid, user_name, text):
    async with async_session() as s:
        fb = Feedback(user_id=uid, user_name=user_name, text=text)
        s.add(fb); await s.commit(); await s.refresh(fb)
        return fb

async def count_feedback():
    async with async_session() as s:
        return (await s.execute(select(func.count(Feedback.id)))).scalar_one()


# ── PREMIUM ──
async def add_premium_request(uid, user_name, plan):
    async with async_session() as s:
        pr = PremiumRequest(user_id=uid, user_name=user_name, plan=plan)
        s.add(pr); await s.commit()
        return pr


# ── ADMINLAR (bazada, dinamik) ──
async def add_admin(uid, full_name, added_by):
    async with async_session() as s:
        existing = await s.get(Admin, uid)
        if existing:
            return False
        s.add(Admin(id=uid, full_name=full_name or "", added_by=added_by))
        await s.commit()
        return True

async def remove_admin(uid):
    async with async_session() as s:
        existing = await s.get(Admin, uid)
        if not existing:
            return False
        await s.execute(delete(Admin).where(Admin.id==uid))
        await s.commit()
        return True

async def is_db_admin(uid):
    async with async_session() as s:
        return (await s.get(Admin, uid)) is not None

async def list_admins():
    async with async_session() as s:
        r = await s.execute(select(Admin))
        return list(r.scalars().all())
    
