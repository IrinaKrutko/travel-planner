from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
import uvicorn

from .models import RouteRequest, RouteResponse, HistoryResponse
from .weather_service import get_weather_forecast
from .ai_service import generate_route_with_ai
from .database import init_db, get_db
from .crud import save_travel_history, get_history, get_history_by_city

# Инициализируем БД
init_db()

app = FastAPI(
    title="Travel Planner AI",
    description="Генератор маршрутов с реальной погодой и ИИ",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "Travel Planner AI API",
        "status": "online",
        "version": "2.0.0",
        "endpoints": [
            "/ - Главная",
            "/health - Проверка здоровья",
            "/generate_route - Генерация маршрута (POST)",
            "/history - История запросов (GET)",
            "/history/{city} - История по городу (GET)"
        ]
    }

@app.get("/health")
async def health():
    return {"status": "ok", "message": "Сервер работает"}

@app.post("/generate_route")
async def generate_route(
    request: RouteRequest,
    db: Session = Depends(get_db)
):
    """Генерирует маршрут с учетом погоды и сохраняет в историю"""
    if request.days < 1 or request.days > 5:
        raise HTTPException(status_code=400, detail="Дней должно быть от 1 до 5")
    
    # Получаем погоду и координаты
    weather, latitude, longitude = await get_weather_forecast(
        request.city, 
        request.days, 
        request.start_date
    )
    
    if not weather:
        raise HTTPException(
            status_code=400, 
            detail="Нет данных о погоде для указанной даты. Доступен прогноз на 5 дней вперёд."
        )
    
    # Генерируем маршрут через ИИ
    route_plan = await generate_route_with_ai(
        request.city, 
        request.days, 
        weather
    )
    
    start_date = request.start_date if request.start_date else datetime.now().strftime("%Y-%m-%d")
    
    # Сохраняем в БД с координатами
    save_travel_history(
        db=db,
        city=request.city,
        days=request.days,
        start_date=start_date,
        weather_forecast=weather,
        route_plan=route_plan,
        latitude=latitude,   
        longitude=longitude  
    )
    
    return RouteResponse(
        city=request.city,
        days=request.days,
        start_date=start_date,
        weather_forecast=weather,
        route_plan=route_plan
    )

@app.get("/history")
async def get_history_endpoint(
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Получить историю запросов"""
    history = get_history(db, limit, offset)
    return history

@app.get("/history/{city}")
async def get_history_by_city_endpoint(
    city: str,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Получить историю запросов по городу"""
    history = get_history_by_city(db, city, limit)
    return history

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)