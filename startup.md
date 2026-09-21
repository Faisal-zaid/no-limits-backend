python reset_db.py && python -c "from alembic.config import Config; from alembic import command; alembic_cfg = Config('alembic.ini'); command.upgrade(alembic_cfg, 'head')" && python seed_admin.py && uvicorn app:app --host 0.0.0.0 --port $PORT           

#the line above is my backup start command incase it breaks and below is the ctual startup i should use 