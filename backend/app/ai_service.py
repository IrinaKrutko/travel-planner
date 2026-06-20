import os
import httpx
import random
from dotenv import load_dotenv

load_dotenv()

POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY")
POLLINATIONS_AVAILABLE = bool(POLLINATIONS_API_KEY)

if POLLINATIONS_AVAILABLE:
    print("✅ Pollinations клиент инициализирован")
else:
    print("⚠️ POLLINATIONS_API_KEY не найден в .env")

async def generate_route_with_ai(city: str, days: int, weather_forecast: list) -> str:
    """Генерирует маршрут через Pollinations AI (новое API)"""
    print(f"🤖 Генерация маршрута для города: {city}")

    if POLLINATIONS_AVAILABLE:
        ai_response = await try_pollinations_ai(city, days, weather_forecast)
        if ai_response:
            print("✅ AI маршрут сгенерирован через Pollinations!")
            return ai_response
        else:
            print("⚠️ AI не ответил, используем fallback")
    else:
        print("⚠️ Pollinations не доступен, используем fallback")

    return generate_smart_fallback(city, days, weather_forecast)

async def try_pollinations_ai(city: str, days: int, weather_forecast: list) -> str:
    """Пытается получить ответ от нового API Pollinations"""
    weather_summary = "\n".join([
        f"День {i+1}: {day['weather']}, {day['temperature']}°C"
        for i, day in enumerate(weather_forecast)
    ])

    prompt = f"""
Ты — гид. Составь готовый маршрут по городу {city} на {days} дня.

Погода:
{weather_summary}

Правила:
1. НЕ задавай вопросы пользователю.
2. НЕ проси уточнить предпочтения.
3. НЕ добавляй фразы типа "Если вы хотите...", "Можете выбрать...".
4. Просто выдай готовый план.

Формат (строго):
**День 1 (дата)**
- Утро: [реальное место в городе {city}]
- День: [реальное место в городе {city}]
- Вечер: [реальное место в городе {city}]
- 🍽️ Совет: что попробовать из местной кухни

**День 2 (дата)**
...

Используй реальные достопримечательности города {city}! 
Попробуй учитывать погоду. Если дождь ищем варианты достопримечательностей в помещениях.
Если тепло и без осадков выбираем интересные места на открытом воздухе.
Ответь только готовым маршрутом, без лишнего текста, на русском языке.
"""

    try:
        print("🔄 Отправка запроса к Pollinations...")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://gen.pollinations.ai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {POLLINATIONS_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "openai",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 1000,
                    "temperature": 0.7
                }
            )

            print(f"📡 Статус Pollinations: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                result = data["choices"][0]["message"]["content"]
                print(f"📝 Длина ответа: {len(result)} символов")
                if len(result) > 50:
                    return result
                else:
                    print(f"⚠️ Ответ слишком короткий: {result}")
            else:
                print(f"⚠️ Pollinations ошибка: {response.status_code} - {response.text[:200]}")

    except Exception as e:
        print(f"❌ Ошибка Pollinations: {e}")

    return None

# --- Функция fallback ---
def generate_smart_fallback(city: str, days: int, weather_forecast: list) -> str:
    """Запасной план с реальными достопримечательностями"""
    places_db = {
        "moscow": {"name": "Москва", "places": ["Кремль", "Красная площадь", "Третьяковская галерея", "Парк Горького", "ВДНХ", "Арбат"], "food": "борщ, пельмени, блины"},
        "kazan": {"name": "Казань", "places": ["Казанский Кремль", "Мечеть Кул-Шариф", "Бауманская улица", "Дворец земледельцев", "Старо-Татарская слобода"], "food": "эчпочмак, чак-чак"},
        "saint petersburg": {"name": "Санкт-Петербург", "places": ["Эрмитаж", "Петропавловская крепость", "Невский проспект", "Исаакиевский собор"], "food": "котлета по-киевски, солянка"},
        "sochi": {"name": "Сочи", "places": ["Олимпийский парк", "Дендрарий", "Морской порт", "Гора Ахун"], "food": "хачапури, шашлык"}
    }

    city_key = city.lower().strip()
    city_data = places_db.get(city_key)
    if not city_data:
        city_data = places_db["moscow"]
        city_name = city.capitalize()
    else:
        city_name = city_data["name"]

    places = city_data["places"].copy()
    random.shuffle(places)

    plan = f"🗺️ **План по городу {city_name} на {days} дня**\n\n"

    for day in range(days):
        if day < len(weather_forecast):
            w = weather_forecast[day]
            weather_text = f"{w['weather']}, {w['temperature']}°C"
            date_text = w['date']
        else:
            weather_text = "☀️ хорошая погода"
            date_text = f"День {day+1}"

        plan += f"**День {day+1} ({date_text})**\n🌡️ {weather_text}\n\n"

        if len(places) >= 3:
            day_places = places[:3]
            places = places[3:]
        else:
            all_places = city_data["places"]
            random.shuffle(all_places)
            day_places = all_places[:3]

        plan += f"☀️ Утро: {day_places[0]}\n"
        plan += f"🌤️ День: {day_places[1]}\n"
        plan += f"🌙 Вечер: {day_places[2]}\n"
        plan += f"🍽️ Совет: попробуйте {city_data['food']}\n\n"

    return plan