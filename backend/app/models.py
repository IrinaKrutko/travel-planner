from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Union

# --- Модели запросов/ответов API ---
class RouteRequest(BaseModel):
    city: str
    days: int = 3
    start_date: Optional[str] = None

class RouteResponse(BaseModel):
    city: str
    days: int
    start_date: str
    weather_forecast: list
    route_plan: str

# --- Модель для истории (с распарсенным JSON) ---
class HistoryResponse(BaseModel):
    id: int
    city: str
    days: int
    start_date: Optional[str]
    weather_forecast: Union[List[dict], str]  # Может быть список или строка
    route_plan: str
    created_at: datetime