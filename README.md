# Remnawave Admin Bot

**Доступные языки:** [English](README_EN.md)

Telegram-бот для администрирования Remnawave: управление пользователями, нодами, инбаундами, статистикой. Оптимизирован под мобильные устройства и продакшн-среды.

[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)](https://github.com/Case211/remna-ad/pkgs/container/remna-ad)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg?style=for-the-badge)](LICENSE)

Контакты для связи: 
- [openode.xyz](https://openode.xyz)
- [neonode.cc](https://neonode.cc)
- [Github - Case211](https://github.com/Case211)
- [Telegram](https://t.me/remnawave_admin)
### Основные возможности
- **Пользователи**: поиск (username/UUID/Telegram/email/tag), создание/редактирование, включение/отключение, сброс трафика, HWID-устройства, статистика.
- **Ноды**: включение/отключение/перезапуск, сертификаты, метрики и онлайн-пользователи.
- **Инбаунды**: управление точками входа, массовые операции для пользователей и нод.
- **Массовые операции**: сброс трафика, удаление неактивных/просроченных, пакетные обновления.
- **Статистика**: агрегированная и поминутная, удобные форматы и индикация.
- **Мобильный UI**: пагинация 6–8 элементов, понятная навигация, быстрые действия.



### Что нового
- Ускорение отклика: уменьшен `poll_interval` до 0.5s.

Wiki по скрипту eGames'а: [`wiki.egam.es`](https://wiki.egam.es/)

### Авторизация через cookie (eGames)
1) Получите cookie в панели Remnawave согласно инструкции https://wiki.egam.es/ru/configuration/external-api/#%D0%BF%D0%BE%D0%BB%D1%83%D1%87%D0%B5%D0%BD%D0%B8%D0%B5-%D0%B4%D0%BE%D1%81%D1%82%D1%83%D0%BF%D0%B0-%D0%BA-api-%D1%81-%D0%B8%D1%81%D0%BF%D0%BE%D0%BB%D1%8C%D0%B7%D0%BE%D0%B2%D0%B0%D0%BD%D0%B8%D0%B5%D0%BC-cookie.
2) Сохраните "NAME=VALUE" в JSON-формате и задайте их в `REMNAWAVE_COOKIES` (Пример: `{NAME:VALUE}`).
3) При необходимости можно использовать переменную `COOKIES`.
## Быстрый старт

### Роли и права доступа
-`Администратор` — полный доступ к функциям бота и управлению панелью.
-`Оператор` — просмотр списков, статистики и деталей без изменений данных.
### Docker (рекомендуется)
1) Подготовка каталога и загрузка конфигов:
```bash
sudo mkdir -p /opt/remna-bot
cd /opt/remna-bot
curl -o .env https://raw.githubusercontent.com/Case211/remna-ad/main/.env.example
curl -o docker-compose.yml https://raw.githubusercontent.com/Case211/remna-ad/main/docker-compose-prod.yml
```
2) Настройка окружения:
```bash
nano .env
```
3) Запуск:
```bash
docker compose up -d
```
4) Логи:
```bash
docker compose logs -f
```

### Ручной запуск
```bash
git clone https://github.com/Case211/remna-ad.git
cd remna-ad
pip install -r requirements.txt
cp .env.example .env
nano .env
python main.py
```

## Переменные окружения

Обязательные:
- `TELEGRAM_BOT_TOKEN` — токен Telegram-бота
- `API_BASE_URL` — базовый URL API Remnawave (например, `https://panel.example.com/api`)
- `REMNAWAVE_API_TOKEN` — токен API (если используется авторизация по токену)
- `OPERATOR_USER_IDS` — список операторов с правами чтения (например, `789012345`)
- `ADMIN_USER_IDS` — список ID админов через запятую (например, `123,456`)

Производительность/интерфейс:
- `DASHBOARD_SHOW_SYSTEM_STATS` (true/false)
- `DASHBOARD_SHOW_SERVER_INFO` (true/false)
- `DASHBOARD_SHOW_USERS_COUNT` (true/false)
- `DASHBOARD_SHOW_NODES_COUNT` (true/false)
- `DASHBOARD_SHOW_TRAFFIC_STATS` (true/false)
- `DASHBOARD_SHOW_UPTIME` (true/false)
- `ENABLE_PARTIAL_SEARCH` (true/false)
- `SEARCH_MIN_LENGTH` (число)


## Использование
- Запустите бота и отправьте `/start`.
- Навигация через кнопки. Списки постранично, быстрые действия доступны из карточек.
- Поиск по нескольким полям, удобный просмотр деталей и управление.

## Замечания по совместимости
- Проверено с Remnawave API v2.1.13.

## Лицензия
MIT — подробности в файле [LICENSE](LICENSE).
  
Обновлено: 29 сентября 2025

