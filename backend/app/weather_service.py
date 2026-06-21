import httpx
import os
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv
from .city_translator import get_coordinates, translate_city

load_dotenv()

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

async def get_weather_forecast(city: str, days: int = 3, start_date: str = None):
    """
    Получает реальный прогноз погоды из OpenWeatherMap
    Возвращает: (forecast, latitude, longitude)
    """
    if not OPENWEATHER_API_KEY or OPENWEATHER_API_KEY == "your_openweather_key_here":
        print("⚠️ API ключ не найден, использую тестовые данные")
        return generate_test_weather(city, days, start_date), None, None
    
    # Получаем координаты города
    coords = get_coordinates(city)
    
    if coords:
        lat, lon = coords
        print(f"🌆 Город: {city} → координаты: {lat}, {lon}")
        forecast = await get_weather_by_coords(lat, lon, days, start_date)
        if forecast:
            return forecast, lat, lon
        else:
            print(f"⚠️ Не удалось получить погоду по координатам, пробуем по названию")
    else:
        print(f"⚠️ Координаты для города {city} не найдены")
    
    # Fallback по названию
    city_eng = translate_city(city)
    print(f"🌆 Город: {city} → {city_eng} (по названию)")
    forecast = await get_weather_by_name(city_eng, days, start_date)
    
    # Если получили прогноз по названию, пытаемся найти координаты для сохранения
    if forecast:
        coords = get_coordinates(city)
        if coords:
            return forecast, coords[0], coords[1]
        else:
            return forecast, None, None
    else:
        # ЕСЛИ НЕ УДАЛОСЬ — ИСПОЛЬЗУЕМ ТЕСТОВЫЕ ДАННЫЕ
        print("⚠️ Все попытки получить погоду не удались, использую тестовые данные")
        return generate_test_weather(city, days, start_date), None, None


async def get_weather_by_coords(lat: float, lon: float, days: int, start_date: str = None):
    """
    Получает прогноз по координатам
    """
    start_date_obj = parse_start_date(start_date)
    if not start_date_obj:
        start_date_obj = datetime.now().date()
    
    # Проверяем, что дата в пределах 5 дней
    today = datetime.now().date()
    max_date = today + timedelta(days=4)
    
    if start_date_obj > max_date:
        print(f"⚠️ Дата {start_date_obj} за пределами 5-дневного прогноза")
        return []
    
    days = min(days, 5)
    
    url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
        "lang": "ru"
    }
    
    print(f"📡 Запрос к OpenWeatherMap (координаты)...")
    
    try:
        # задаем таймаут, proxy=None
        async with httpx.AsyncClient(timeout=30.0, proxy=None) as client:
            response = await client.get(url, params=params)
            print(f"📡 Статус: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                return parse_weather_data(data, days, start_date_obj)
            else:
                print(f"⚠️ Ошибка OpenWeatherMap: {response.status_code}")
                print(f"📄 {response.text[:200]}")
                return []
                
    except httpx.TimeoutException:
        print("❌ Таймаут подключения к OpenWeatherMap (координаты)")
        return []
    except Exception as e:
        print(f"❌ Ошибка: {type(e).__name__}: {e}")
        return []


async def get_weather_by_name(city: str, days: int, start_date: str = None):
    """
    Получает прогноз по названию города
    """
    start_date_obj = parse_start_date(start_date)
    if not start_date_obj:
        start_date_obj = datetime.now().date()
    
    # Проверяем, что дата в пределах 5 дней
    today = datetime.now().date()
    max_date = today + timedelta(days=4)
    
    if start_date_obj > max_date:
        print(f"⚠️ Дата {start_date_obj} за пределами 5-дневного прогноза")
        return []
    
    days = min(days, 5)
    
    url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {
        "q": city,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
        "lang": "ru"
    }
    
    print(f"📡 Запрос к OpenWeatherMap (по названию)...")
    
    try:
        # задаем таймаут, proxy=None
        async with httpx.AsyncClient(timeout=30.0, proxy=None) as client:
            response = await client.get(url, params=params)
            print(f"📡 Статус: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                return parse_weather_data(data, days, start_date_obj)
            else:
                print(f"⚠️ Ошибка OpenWeatherMap: {response.status_code}")
                print(f"📄 {response.text[:200]}")
                return []
                
    except httpx.TimeoutException:
        print("❌ Таймаут подключения к OpenWeatherMap (по названию)")
        return []
    except Exception as e:
        print(f"❌ Ошибка: {type(e).__name__}: {e}")
        return []


def parse_start_date(start_date: str):
    """Парсит дату из строки"""
    if start_date:
        try:
            return datetime.strptime(start_date, "%Y-%m-%d").date()
        except ValueError:
            return None
    return None


def parse_weather_data(data: dict, days: int, start_date_obj) -> list:
    """
    Парсит данные от OpenWeatherMap и возвращает прогноз
    """
    forecast = []
    
    # Фильтруем прогнозы, начиная с start_date
    selected_forecasts = []
    for item in data['list']:
        item_date = item['dt_txt'].split()[0]
        item_date_obj = datetime.strptime(item_date, "%Y-%m-%d").date()
        
        if item_date_obj >= start_date_obj:
            selected_forecasts.append(item)
    
    # Группируем по дням
    days_data = {}
    for item in selected_forecasts:
        item_date = item['dt_txt'].split()[0]
        if item_date not in days_data:
            days_data[item_date] = []
        days_data[item_date].append(item)
    
    # Берём первые `days` дней
    day_count = 0
    for date_key in sorted(days_data.keys()):
        if day_count >= days:
            break
        
        day_forecasts = days_data[date_key]
        
        # Ищем прогноз на 12:00
        found = None
        for item in day_forecasts:
            time = item['dt_txt'].split()[1]
            if time.startswith("12:"):
                found = item
                break
        
        if found:
            item = found
            forecast.append({
                "date": item['dt_txt'].split()[0],
                "temperature": round(item['main']['temp']),
                "weather": item['weather'][0]['description'],
                "icon": item['weather'][0]['icon'],
                "humidity": item['main']['humidity'],
                "wind_speed": round(item['wind']['speed'], 1)
            })
        else:
            # Среднее за день
            avg_temp = sum(item['main']['temp'] for item in day_forecasts) / len(day_forecasts)
            avg_humidity = sum(item['main']['humidity'] for item in day_forecasts) / len(day_forecasts)
            avg_wind = sum(item['wind']['speed'] for item in day_forecasts) / len(day_forecasts)
            
            # Находим самое частое описание погоды
            weather_counts = {}
            for item in day_forecasts:
                desc = item['weather'][0]['description']
                weather_counts[desc] = weather_counts.get(desc, 0) + 1
            
            # Находим описание с максимальным количеством
            most_common_weather = max(weather_counts, key=weather_counts.get)
            
            # Берём иконку из первого прогноза
            item = day_forecasts[0]
            
            forecast.append({
                "date": item['dt_txt'].split()[0],
                "temperature": round(avg_temp),
                "weather": most_common_weather,
                "icon": item['weather'][0]['icon'],
                "humidity": round(avg_humidity),
                "wind_speed": round(avg_wind, 1)
            })
        
        day_count += 1
    
    return forecast

# Генерация тестовых данных погоды
def generate_test_weather(city: str, days: int, start_date: str = None):
    """
    Генерирует тестовые данные погоды (используется, если API недоступен)
    """
    weather_types = ["☀️ Солнечно", "⛅ Облачно", "🌧️ Дождь", "🌤️ Ясно", "🌥️ Пасмурно"]
    forecast = []
    
    # Определяем дату старта
    if start_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
        except:
            start = datetime.now().date()
    else:
        start = datetime.now().date()
    
    for i in range(days):
        current_date = start + timedelta(days=i)
        forecast.append({
            "date": current_date.strftime("%Y-%m-%d"),
            "temperature": random.randint(10, 30),
            "weather": random.choice(weather_types),
            "icon": "01d",
            "humidity": random.randint(40, 80),
            "wind_speed": round(random.uniform(1, 10), 1)
        })
    
    return forecast