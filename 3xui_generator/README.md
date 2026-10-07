# 3x-ui Manager v4.1

Полноценная Home Assistant App-панель для удалённого 3x-ui 3.9.0.

## Управление inbound
- список inbound
- включение/выключение
- изменение remark/port
- сброс трафика
- удаление

## Управление клиентами / подписками
- список клиентов
- ON/OFF
- изменение email, quota, expiry, IP/HWID limits, flow
- удаление клиента
- сброс трафика
- просмотр и очистка IP/HWID
- VLESS + REALITY ссылка
- QR
- очистка depleted/orphan клиентов

## Создание
- VLESS Reality inbound
- X25519 через 3x-ui
- shortId
- UUID
- traffic quota
- срок
- IP/HWID limit

## Безопасность
3x-ui API token хранится в `/data/options.json` App и не передаётся JavaScript-коду браузера. UI доступен через Home Assistant Ingress.
