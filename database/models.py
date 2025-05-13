import aiosqlite
from datetime import datetime
from config.settings import DATABASE_PATH

async def init_db():
    """Initialize database with required tables"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Users table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                points REAL DEFAULT 0,
                streak INTEGER DEFAULT 0,
                last_check_in TEXT,
                last_task_date TEXT,
                tasks_today INTEGER DEFAULT 0,
                is_banned BOOLEAN DEFAULT 0,
                referrer_id INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Achievements table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS achievements (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                emoji TEXT NOT NULL,
                description TEXT NOT NULL
            )
        """)
        
        # User achievements table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_achievements (
                user_id INTEGER,
                achievement_id TEXT,
                earned_at TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, achievement_id),
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (achievement_id) REFERENCES achievements(id)
            )
        """)
        
        # Daily tasks table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS daily_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_text TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                FOREIGN KEY (created_by) REFERENCES users(user_id)
            )
        """)
        
        # Subscriptions table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                id TEXT PRIMARY KEY,
                url TEXT NOT NULL,
                type TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Admin logs table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS admin_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER,
                action TEXT,
                details TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db.commit()

async def add_user(user_id: int, username: str, referrer_id: int = None):
    """Add new user to database"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username, referrer_id) VALUES (?, ?, ?)",
            (user_id, username, referrer_id)
        )
        await db.commit()

async def get_user(user_id: int):
    """Get user data from database"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT points, streak, last_check_in, last_task_date, tasks_today, is_banned FROM users WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            return await cursor.fetchone()

async def add_points(user_id: int, points: float):
    """Add points to user"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "UPDATE users SET points = points + ? WHERE user_id = ?",
            (points, user_id)
        )
        await db.commit()

async def get_top_users(limit: int = 10):
    """Get top users by points"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT username, points FROM users WHERE is_banned = 0 ORDER BY points DESC LIMIT ?",
            (limit,)
        ) as cursor:
            return await cursor.fetchall()

async def add_achievement(user_id: int, achievement_id: str):
    """Add achievement to user"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO user_achievements (user_id, achievement_id) VALUES (?, ?)",
            (user_id, achievement_id)
        )
        await db.commit()

async def get_user_achievements(user_id: int):
    """Get user achievements"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT achievement_id FROM user_achievements WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            return [row[0] for row in await cursor.fetchall()]

async def set_daily_task(task_text: str, created_by: int):
    """Set new daily task"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT INTO daily_tasks (task_text, created_by) VALUES (?, ?)",
            (task_text, created_by)
        )
        await db.commit()

async def get_current_task():
    """Get current daily task"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT task_text FROM daily_tasks ORDER BY created_at DESC LIMIT 1"
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

async def update_subscription(sub_id: str, url: str, type: str):
    """Update subscription URL"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO subscriptions (id, url, type, updated_at) VALUES (?, ?, ?, ?)",
            (sub_id, url, type, datetime.now().isoformat())
        )
        await db.commit()

async def get_subscriptions():
    """Get all subscription URLs"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT id, url, type FROM subscriptions") as cursor:
            return await cursor.fetchall()

async def update_check_in(user_id: int, streak: int):
    """Update user's last check-in time and streak"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "UPDATE users SET last_check_in = ?, streak = ? WHERE user_id = ?",
            (datetime.now().isoformat(), streak, user_id)
        )
        await db.commit()

async def log_admin_action(admin_id: int, action: str, details: str = None):
    """Log admin action to the database"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT INTO admin_logs (admin_id, action, details) VALUES (?, ?, ?)",
            (admin_id, action, details)
        )
        await db.commit() 