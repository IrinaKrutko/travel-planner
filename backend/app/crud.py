# backend/app/crud.py

from sqlalchemy.orm import Session
from .database import TravelHistory
import json

def save_travel_history(
    db: Session,
    city: str,
    days: int,
    start_date: str,
    weather_forecast: list,
    route_plan: str,
    latitude: float = None,   
    longitude: float = None   
) -> TravelHistory:
    """
    Сохраняет запрос в историю с координатами
    """
    history = TravelHistory(
        city=city,
        days=days,
        start_date=start_date,
        latitude=latitude,
        longitude=longitude,
        weather_forecast=json.dumps(weather_forecast, ensure_ascii=False),
        route_plan=route_plan
    )
    db.add(history)
    db.commit()
    db.refresh(history)
    return history

def get_history(db: Session, limit: int = 10, offset: int = 0) -> list:
    """
    Получает последние записи из истории с распарсенным JSON
    """
    records = db.query(TravelHistory).order_by(
        TravelHistory.created_at.desc()
    ).offset(offset).limit(limit).all()
    
    result = []
    for record in records:
        record_dict = {
            "id": record.id,
            "city": record.city,
            "days": record.days,
            "start_date": record.start_date,
            "latitude": record.latitude,     
            "longitude": record.longitude,   
            "weather_forecast": json.loads(record.weather_forecast) if record.weather_forecast else [],
            "route_plan": record.route_plan,
            "created_at": record.created_at
        }
        result.append(record_dict)
    
    return result

def get_history_by_city(db: Session, city: str, limit: int = 10) -> list:
    """
    Получает историю по городу с распарсенным JSON
    """
    records = db.query(TravelHistory).filter(
        TravelHistory.city.ilike(f"%{city}%")
    ).order_by(
        TravelHistory.created_at.desc()
    ).limit(limit).all()
    
    result = []
    for record in records:
        record_dict = {
            "id": record.id,
            "city": record.city,
            "days": record.days,
            "start_date": record.start_date,
            "latitude": record.latitude,     
            "longitude": record.longitude,   
            "weather_forecast": json.loads(record.weather_forecast) if record.weather_forecast else [],
            "route_plan": record.route_plan,
            "created_at": record.created_at
        }
        result.append(record_dict)
    
    return result