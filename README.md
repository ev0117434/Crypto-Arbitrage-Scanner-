# Binance Prices Fetcher (Версия 3.1)
## Обзор проекта
Модульный Python-скрипт для получения реал-тайм цен торговых пар на Binance в формате `[биржа, рынок, символ, bid, ask, last, ts]`. Поддержка Spot и USDT-M Futures рынков с минимальными задержками (<10 мс на обновления WS + <100 мс на снапшоты). Список пар обновляется редко (раз в 2 дня), цены — в реальном времени через WebSocket с периодическими REST-снапшотами для гарантии покрытия. Данные выводятся в консоль и сохраняются построчно в `prices_log.txt`.

- **Цель**: Мониторинг для арбитража (Spot-Futures спред) с фокусом на низкую latency и полное покрытие всех пар.
- **Ключевые особенности**:
  - WebSocket aggregate stream для всех ~440 Spot + ~538 Futures USDT-M пар.
  - Last price: `(bid + ask) / 2`.
  - TS: Unix timestamp в мс.
  - Heartbeat: Ping каждые 3 мин.
  - Initial/periodic REST-снапшоты (каждые 0.5 с) для полного покрытия.
  - Фильтрация по `FILTER_SYMBOLS` (опционально).
  - Обработка ошибок записи в лог (try-except).
- **API**: Public WebSocket/REST endpoints Binance (без ключей).
- **Версия Python**: 3.8+.
- **Зависимости**: `pip install aiohttp websockets`.

## Структура проекта
```
binance_prices/
├── config.py          # Конфигурация (интервалы, фильтры)
├── pairs_fetcher.py   # Редкий fetch списка пар (Spot/Futures USDT)
├── spot_ws.py         # WebSocket для Spot цен (@bookTicker) с логом
├── futures_ws.py      # WebSocket для USDT-M Futures (@bookTicker) с логом
├── main.py            # Оркестратор (WS, snapshots, лог)
└── prices_log.txt     # Автоматически генерируемый лог (построчный)
└── symbols.json       # Опциональный JSON с парами (при fetch)
```

## Установка и запуск
1. Создайте директорию `binance_prices/` и сохраните файлы.
2. Установите зависимости: `pip install aiohttp websockets`.
3. Настройте `config.py` (см. ниже).
4. Запуск: `python main.py`.
5. Остановка: Ctrl+C (логи на shutdown).
6. Мониторинг: Консоль для live-вывод, `prices_log.txt` для хранения (UTF-8, append).

Ожидаемый вывод (реал-тайм + снапшоты):
```
[Binance, Spot, BTCUSDT, 45000.0, 45001.0, 45000.5, 1733145600000]
[Binance, Futures, BTCUSDT, 45000.1, 45001.1, 45000.6, 1733145601000]
```
- WS: Только при изменениях; снапшоты: Все пары каждые 0.5 с.
- Лог: Полный, с 0.0 для неактивных пар.

## Конфигурация (config.py)
```python
INTERVAL = 180  # секунды для ping (3 мин)
SNAPSHOT_INTERVAL = 0.5  # секунды для снапшотов (минимум 0.5 с)
FILTER_SYMBOLS = None  # ['BTCUSDT'] или None (все)
LOG_LEVEL = 'INFO'  # 'DEBUG'/'INFO'/'ERROR'
FETCH_PAIRS_INTERVAL = 172800  # секунды для pairs (2 дня)
```
- `SNAPSHOT_INTERVAL`: Частота снапшотов (0.5 с — оптимально).
- `FILTER_SYMBOLS`: Фильтр вывода/лога (не влияет на подписку).
- Изменения — перезапуск.

## Модули в деталях

### config.py
Глобальные настройки. `INTERVAL` — для WS keepalive; `SNAPSHOT_INTERVAL` — для REST-цикла.

### pairs_fetcher.py
- **Endpoints**: `/api/v3/exchangeInfo` (Spot), `/fapi/v1/exchangeInfo` (Futures).
- **Функции**: `get_all_spot_symbols`, `get_all_futures_symbols` — USDT-пары в TRADING.
- **Логика**: Асинхронный GET, фильтр по status/quoteAsset. Вызов в main.py при старте; сохраняет в `symbols.json`.
- **Использование**: Разово; обновляйте вручную (задержки не критичны).

### spot_ws.py
- **URI**: `wss://stream.binance.com:9443/ws/!bookTicker@arr` (все Spot).
- **Функции**:
  - `handle_spot_updates`: Парсинг JSON, расчет last/ts, print + `await asyncio.to_thread(save_to_file, line)`.
  - `send_periodic_ping`: Ping каждые 180 с.
  - `connect_spot_ws`: Reconnect (sleep 5 с на ошибку).
- **Логика**: Фильтр по `FILTER_SYMBOLS`; обработка `e: 'bookTicker'`.
- **Лог**: Построчный append в `prices_log.txt`.

### futures_ws.py
- **URI**: `wss://fstream.binance.com/ws/!bookTicker@arr` (все USDT-M).
- **Функции**: Аналогично spot_ws.py, market='Futures'.
- **Лог**: Тот же файл.

### main.py
- **Оркестратор**: Параллельный `asyncio.gather(WS, periodic_snapshot)`.
- **Функции**:
  - `save_to_file`: Append в лог с try-except (PermissionError — skip + log).
  - `initial_snapshot`: REST-снапшот всех пар при старте (print + лог).
  - `periodic_snapshot`: Цикл снапшотов каждые 0.5 с.
  - `fetch_pairs_once`: Инициализация пар.
  - `main`: Fetch + initial + gather.
- **Логика**: Обработка KeyboardInterrupt; фильтр в снапшотах.

## Эффективность и лимиты
- **Задержка**: WS <10 мс (push); снапшоты ~100 мс/цикл (2 req: Spot + Futures).
- **Трафик**: Aggregate WS — все пары; снапшоты 120 req/мин (лимит 1200/min — безопасно).
- **Стабильность**: Reconnect + ping; try-except на лог.
- **Масштаб**: ~978 пар (Spot + Futures); лог ~GB/день — мониторьте размер.

## Обработка ошибок
- **WS disconnect**: Reconnect + warning.
- **Parse/JSON**: Skip + ERROR log.
- **Rate limit (429)**: Лог + пустой fetch (авто-восстановление).
- **File PermissionError**: Skip записи + ERROR log (скрипт продолжается).
- **Логи**: `logging` на уровне `INFO`; DEBUG для трассировки.

## Расширение
- **Specific streams**: Динамический URI для `FILTER_SYMBOLS` (снижение трафика).
- **Pairs-таймер**: `asyncio.create_task(update_pairs_every(FETCH_PAIRS_INTERVAL))`.
- **Спред-алерты**: В handlers: Сравнение Spot/Futures, уведомления (e.g., Telegram).
- **Ротация лога**: `logging.handlers.RotatingFileHandler` по размеру/дате.
- **Тестирование**: Mock WS/REST (unittest); Binance testnet.

## История версий
- **1.0**: REST polling (/ticker/price).
- **2.0**: REST (/bookTicker), bid/ask/last, цикл.
- **3.0**: WS (@bookTicker), heartbeat, pairs-fetcher.
- **3.1**: Snapshots (initial/periodic), лог с try-except, обработка 0.0 пар.

## Лицензия
MIT. Для Разработчика.

**Вопросы и рекомендации:**  
- Вопрос: Нужно ли добавить ротацию лога (новый файл ежедневно) для управления размером?  
- Рекомендация: Для арбитража интегрируйте pandas в отдельный скрипт для анализа `prices_log.txt` (e.g., спред Spot-Futures по символу).