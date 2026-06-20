from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Используем SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./travel.db")

# Для SQLite нужно добавить этот параметр
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# --- Модель базы данных ---
class TravelHistory(Base):
    __tablename__ = "travel_history"

    id = Column(Integer, primary_key=True, index=True)
    city = Column(String(100), nullable=False)
    days = Column(Integer, nullable=False)
    start_date = Column(String(20))
    
    # СТОЛБЦЫ ДЛЯ КООРДИНАТ
    latitude = Column(Float, nullable=True)   # Широта
    longitude = Column(Float, nullable=True)  # Долгота
    
    weather_forecast = Column(Text)  # Сохраняем как JSON строку
    route_plan = Column(Text)
    created_at = Column(DateTime, default=datetime.now)

# Создаём таблицы
def init_db():
    Base.metadata.create_all(bind=engine)

# Зависимость для получения сессии БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()