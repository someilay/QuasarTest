from sqlalchemy import create_engine

from src.models import data_models


engine = create_engine('sqlite:///../local.db', echo=True)
data_models.setup(engine)
