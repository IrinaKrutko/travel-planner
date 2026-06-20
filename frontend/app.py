
import streamlit as st
import requests
from datetime import datetime, timedelta
import json
import pandas as pd

# --- Настройка страницы ---
st.set_page_config(
    page_title="Travel Planner AI",
    page_icon="✈️",
    layout="wide"
)

# --- API URL ---
API_URL = "http://localhost:8000"

# --- Заголовок ---
st.title("✈️ AI Планировщик путешествий")
st.markdown("Создай маршрут с учетом погоды с помощью ИИ")

# --- Боковая панель ---
with st.sidebar:
    st.header("📋 Параметры")
    
    city = st.text_input("🏙️ Город", value="Москва")
    
    # --- ВЫБОР ДАТЫ ---
    st.subheader("📅 Дата начала")
    
    today = datetime.now().date()
    max_date = today + timedelta(days=4)
    
    st.info(f"📌 OpenWeatherMap даёт прогноз на 5 дней вперёд (до {max_date.strftime('%d.%m.%Y')})")
    
    start_date = st.date_input(
        "Выберите дату",
        value=today,
        min_value=today,
        max_value=max_date,
        help="Выберите день, с которого начать прогноз (доступно 5 дней)"
    )
    
    # --- ВЫБОР КОЛИЧЕСТВА ДНЕЙ ---
    st.subheader("📆 Количество дней")
    
    max_days_from_start = (max_date - start_date).days + 1
    max_days = min(5, max_days_from_start)
    
    if max_days == 1:
        days = 1
        st.info(f"📆 Доступен только 1 день прогноза ({start_date.strftime('%d.%m.%Y')})")
    else:
        days = st.slider(
            "Дней прогноза",
            min_value=1,
            max_value=max_days,
            value=min(3, max_days),
            help=f"Доступно {max_days} дней прогноза от выбранной даты"
        )
    
    end_date = start_date + timedelta(days=days - 1)
    st.caption(f"📆 Прогноз с {start_date.strftime('%d.%m.%Y')} по {end_date.strftime('%d.%m.%Y')}")
    
    generate_button = st.button("🚀 Сгенерировать маршрут", type="primary", use_container_width=True)
    
    st.divider()
    
    # --- КНОПКА ДЛЯ ИСТОРИИ ---
    if st.button("📜 Показать историю", use_container_width=True):
        st.session_state.show_history = not st.session_state.get("show_history", False)
    
    st.caption("ℹ️ Погода от OpenWeatherMap (5 дней), маршруты от AI")

# --- Основная часть ---
if generate_button:
    with st.spinner("⏳ Генерируем маршрут..."):
        try:
            response = requests.post(
                f"{API_URL}/generate_route",
                json={
                    "city": city,
                    "days": days,
                    "start_date": start_date.strftime("%Y-%m-%d")
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                st.success(f"✅ Маршрут по городу {data['city']} на {data['days']} дня с {data['start_date']} сгенерирован!")
                
                # --- Погода ---
                st.subheader("🌤️ Прогноз погоды")
                weather_cols = st.columns(days)
                for i, day in enumerate(data['weather_forecast']):
                    with weather_cols[i]:
                        st.metric(
                            label=f"📅 {day['date']}",
                            value=f"{day['temperature']}°C",
                            delta=day['weather']
                        )
                        st.caption(f"💧 Влажность: {day['humidity']}%")
                        st.caption(f"💨 Ветер: {day['wind_speed']} м/с")
                
                # --- Маршрут ---
                st.subheader("🗺️ Маршрут")
                st.markdown(data['route_plan'])
                
            else:
                st.error(f"❌ Ошибка: {response.status_code}")
                st.write(response.text)
                
        except requests.exceptions.ConnectionError:
            st.error("❌ Бэкенд не запущен! Запустите FastAPI: uvicorn app.main:app --reload")
        except Exception as e:
            st.error(f"❌ Ошибка: {str(e)}")

# --- ИСТОРИЯ ---
if st.session_state.get("show_history", False):
    st.divider()
    st.header("📜 История запросов")
    
    try:
        response = requests.get(f"{API_URL}/history?limit=20", timeout=10)
        
        if response.status_code == 200:
            history = response.json()
            
            if history:
                st.info(f"📊 Всего записей: {len(history)}")
                
                # Показываем каждый запрос как раскрывающийся блок
                for item in history:
                    # Форматируем дату
                    created_at = item.get("created_at", "")
                    if created_at:
                        created_at = created_at[:16].replace("T", " ")
                    
                    # Заголовок для раскрывающегося блока
                    expander_title = f"🗺️ {item['city']} | {item['days']} дня | {item.get('start_date', '')} | 📅 {created_at}"
                    
                    with st.expander(expander_title):
                        # --- Город, дата и координаты ---
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("🏙️ Город", item['city'])
                        with col2:
                            st.metric("📆 Дней", item['days'])
                        with col3:
                            st.metric("📅 Дата старта", item.get('start_date', 'не указана'))
                        with col4:
                            # Показываем координаты
                            lat = item.get('latitude')
                            lon = item.get('longitude')
                            if lat and lon:
                                st.metric("📍 Координаты", f"{lat:.4f}, {lon:.4f}")
                            else:
                                st.metric("📍 Координаты", "не найдены")
                        
                        st.divider()
                        
                        # --- Погода ---
                        st.subheader("🌤️ Прогноз погоды")
                        weather = item.get('weather_forecast', [])
                        
                        if weather and isinstance(weather, list) and len(weather) > 0:
                            # Создаем колонки для погоды
                            weather_cols = st.columns(min(len(weather), 5))
                            for i, day in enumerate(weather):
                                if i >= 5:  # Не больше 5 колонок
                                    break
                                with weather_cols[i]:
                                    date = day.get('date', '')
                                    temp = day.get('temperature', '?')
                                    weather_desc = day.get('weather', '')
                                    humidity = day.get('humidity', '?')
                                    wind = day.get('wind_speed', '?')
                                    
                                    st.metric(
                                        label=f"📅 {date}",
                                        value=f"{temp}°C",
                                        delta=weather_desc
                                    )
                                    st.caption(f"💧 Влажность: {humidity}%")
                                    st.caption(f"💨 Ветер: {wind} м/с")
                        else:
                            st.info("Нет данных о погоде")
                        
                        st.divider()
                        
                        # --- Маршрут ---
                        st.subheader("🗺️ Маршрут")
                        route = item.get('route_plan', 'Маршрут не сгенерирован')
                        st.markdown(route)
                        
                        st.divider()
                        st.caption(f"🆔 ID записи: {item.get('id', '')}")
            else:
                st.info("📭 История пуста. Сгенерируйте первый маршрут!")
        else:
            st.warning(f"⚠️ Не удалось загрузить историю (статус: {response.status_code})")
            
    except requests.exceptions.ConnectionError:
        st.error("❌ Бэкенд не запущен! Запустите FastAPI: uvicorn app.main:app --reload")
    except Exception as e:
        st.warning(f"⚠️ Ошибка загрузки истории: {e}")

# --- Проверка статуса API ---
st.divider()
col1, col2 = st.columns(2)
with col1:
    st.caption("📡 Статус API:")
    try:
        response = requests.get(f"{API_URL}/health", timeout=2)
        if response.status_code == 200:
            st.success("✅ Онлайн")
        else:
            st.warning("⚠️ Недоступен")
    except:
        st.error("❌ Офлайн")