from sqlalchemy import create_engine

from src.models import data_models

# Configs

engine = create_engine('sqlite:///../local.db')
data_models.setup(engine)
