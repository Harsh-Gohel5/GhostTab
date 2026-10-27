from alembic import context

from ghosttab_api.config import Settings
from ghosttab_api.database import make_engine
from ghosttab_api.models import Base

engine = make_engine(Settings().database_url)
with engine.connect() as connection:
    context.configure(connection=connection, target_metadata=Base.metadata)
    with context.begin_transaction():
        context.run_migrations()
