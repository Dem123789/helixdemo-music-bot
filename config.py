import os

from dotenv import load_dotenv

load_dotenv()


# ============================================================
# TELEGRAM
# ============================================================

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# User account session used by PyTgCalls.
# This is separate from BOT_TOKEN.
SESSION_NAME = os.getenv(
    "SESSION_NAME",
    "kristinemusic"
)


# ============================================================
# BOT
# ============================================================

BOT_NAME = os.getenv(
    "BOT_NAME",
    "KristineMusicBot"
)

BOT_USERNAME = os.getenv(
    "BOT_USERNAME",
    ""
)

OWNER_ID = int(
    os.getenv("OWNER_ID", "0")
)


# ============================================================
# MUSIC
# ============================================================

DOWNLOAD_DIR = os.getenv(
    "DOWNLOAD_DIR",
    "downloads"
)

MAX_QUEUE_SIZE = int(
    os.getenv("MAX_QUEUE_SIZE", "50")
)

DEFAULT_VOLUME = int(
    os.getenv("DEFAULT_VOLUME", "100")
)

DEFAULT_LOOP = os.getenv(
    "DEFAULT_LOOP",
    "off"
).lower()


# ============================================================
# DATABASE
# ============================================================

DATABASE_FILE = os.getenv(
    "DATABASE_FILE",
    "kristine.db"
)


# ============================================================
# LOGGING
# ============================================================

LOG_LEVEL = os.getenv(
    "LOG_LEVEL",
    "INFO"
)


# ============================================================
# VALIDATION
# ============================================================

def validate_config():
    """
    Check the required environment variables before
    starting the bot.
    """

    missing = []

    if API_ID == 0:
        missing.append("API_ID")

    if not API_HASH:
        missing.append("API_HASH")

    if not BOT_TOKEN:
        missing.append("BOT_TOKEN")

    if OWNER_ID == 0:
        missing.append("OWNER_ID")

    if missing:
        raise RuntimeError(
            "Missing required environment variables: "
            + ", ".join(missing)
        )


def ensure_directories():
    """
    Create directories required by the music system.
    """

    os.makedirs(
        DOWNLOAD_DIR,
        exist_ok=True
    )
