import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from dotenv import load_dotenv
import urllib.parse  # <--- Add this import

# 1. Load the .env file
load_dotenv()

config = context.config

# 2. Build the Database URL from your .env variables
db_user = os.getenv("DB_USER")
db_pass = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST", "localhost")
db_port = os.getenv("DB_PORT", "5432")
db_name = os.getenv("DB_NAME")

# 3. URL-encode the password to handle special characters like '$' or '@'
safe_password = urllib.parse.quote_plus(db_pass) if db_pass else ""

# Construct the URL and escape the % signs by doubling them
database_url = f"postgresql://{db_user}:{safe_password}@{db_host}:{db_port}/{db_name}"
database_url = database_url.replace("%", "%%")

# 4. Set the sqlalchemy.url dynamically
config.set_main_option("sqlalchemy.url", database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = None

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    # Use the configuration we just set above
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()