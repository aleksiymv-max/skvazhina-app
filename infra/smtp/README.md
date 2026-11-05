# Собственный SMTP-канал для «Промысла»

Цель — вынести Auth-письма (приглашения, восстановление пароля) из встроенного тестового отправителя Supabase. Никаких паролей в этом репозитории нет.

## Быстрый вариант без покупки домена — служебный Gmail SMTP

В проекте уже использовалась служебная почта Google с паролем приложения. Если учётная запись и пароль приложения по-прежнему действуют, можно подключить SMTP непосредственно к Supabase. Это **своя отдельная SMTP-учётная запись**, но не физически самостоятельный сервер.

Настройки Supabase Dashboard → Authentication → SMTP Settings:

- Enable Custom SMTP.
- Sender email: адрес служебной Gmail-учётной записи.
- Sender name: Промысел.
- SMTP host: smtp.gmail.com.
- SMTP port: 465 (TLS), допустим 587 (STARTTLS).
- SMTP username: тот же служебный Gmail-адрес.
- SMTP password: пароль приложения Google (НЕ основной пароль аккаунта).

Для включения без ноутбука имеется ручной GitHub Actions workflow .github/workflows/promysel-smtp-setup.yml.
В репозитории откройте Settings → Secrets and variables → Actions. Создайте три секрета:

1. SUPABASE_ACCESS_TOKEN — токен управления из https://supabase.com/dashboard/account/tokens, не service_role ключ БД.
2. PROMYSEL_SMTP_USER — служебный Gmail-адрес.
3. PROMYSEL_SMTP_PASSWORD — пароль приложения Google. Не отправляйте его в чат.

По желанию задайте в Actions Variables PROMYSEL_SMTP_HOST, PROMYSEL_SMTP_PORT, PROMYSEL_SMTP_FROM (для Gmail по умолчанию уже определены). Затем Actions → Configure Promysel custom SMTP → Run workflow → режим gmail → подтверждение ENABLE_PROMYSEL_SMTP.

Сценарий проверяет TLS и SMTP AUTH без отправки писем и только при успешной проверке обновляет настройки Supabase Auth через Management API. Токены не публикуются в репозитории или артефактах.

Без GitHub Actions можно заполнить эти же поля прямо в Authentication → SMTP Settings. Это безопаснее, если не хотите сохранять Management Token в GitHub Secrets.

После включения отправьте **одно** контрольное приглашение на собственный адрес и проверьте получение, ссылку на установку пароля и spam folder. Три старые одобренные заявки пока не рассылаем автоматически. После успешного теста следует уменьшить 31-минутный ограничитель v2.05 (отдельная серверная очередь приглашений).

Справка: https://supabase.com/docs/guides/auth/auth-smtp
Google: https://support.google.com/mail/answer/185833

## Полностью независимый SMTP-сервер — Stalwart (отдельный путь)

Файл infra/smtp/selfhost/compose.yaml позволяет запустить собственный SMTP на Docker/VPS. НО для надёжной доставки в Gmail/Yandex/Mail.ru требуются:

- Собственный почтовый домен с управлением A/MX/SPF/DKIM/DMARC.
- VPS с постоянным публичным IP и правильным обратным DNS (PTR).
- Открытый исходящий и входящий порт 25; 465 для TLS SMTP-клиентов.
- Настроенный сертификат TLS и запрет открытого ретранслятора (open relay).
- Наблюдение за очередью доставки, спамом и отклонениями.

На текущем VPS может работать Nginx на 443; не запускайте этот compose поверх существующих сетевых сервисов без выделенного IP/перенастройки портов. TUQO или Cloudflare Pages — не SMTP-сервер. Поддомены TUQO/Beget нельзя использовать как собственный почтовый домен без доступа к его DNS.

Официальная инструкция: https://www.stalw.art/docs/install/platform/docker/
Первый запуск: Docker Compose → Stalwart Wizard через SSH-туннель на 127.0.0.1:8080 → TLS → DNS → test messages. После этого укажите в Supabase SMTP host вашего сервера, port 465, отправителя и отдельный пароль SMTP.

## Безопасность, ограничения и тестирование

- Нельзя вставлять пароль приложения в исходники Flutter, .env GitHub, публичные issues или chat.
- Supabase после включения Custom SMTP может применять собственный лимит 30 писем/час; очередь Промысла v2.05 имеет дополнительный ограничитель.
- Отправлено по SMTP не равно доставлено во входящие. Нужна проверка mailbox и почтовых логов.
- Автоматическая отправка трёх старых приглашений сознательно не включена.
- Тест без обращения в сеть: python3 -m unittest discover -s infra/smtp -v.
- Команда в собственном терминале: python3 infra/smtp/configure_supabase_smtp.py --mode gmail --interactive (только проверка). Для настройки потребуется переменная PROMYSEL_SMTP_CONFIRM=ENABLE_PROMYSEL_SMTP и флаг --apply.
