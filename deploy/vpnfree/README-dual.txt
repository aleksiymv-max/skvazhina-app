Промысел — две версии без Cloudflare, один Supabase.
Сайты в архиве: site-stable (сотрудники), site-dev (разработка).
Настройте два DNS A-записи (app.domain.ru и dev.domain.ru) на IP VPS
без Cloudflare-проксирования. Потребуются Ubuntu 24.04 и HTTPS-доступ VPS
к текущему Supabase.
Команда: sudo bash deploy/install-dual.sh app.domain.ru dev.domain.ru admin@example.ru
Обновление только разработки:
  sudo bash deploy/update-channel.sh dev /путь/к/новому/site-dev
Обновление сотрудников — отдельное, только после тестирования.

Оба сайта используют ОДНУ базу, одни аккаунты, чаты, файлы и Edge Functions.
Действия в DEV меняют реальные данные; серверные миграции влияют на всех.
В Supabase Auth Redirect URLs добавьте
https://app.domain.ru/finish-registration.html и
https://dev.domain.ru/finish-registration.html
Секрет PROMYSEL_PUBLIC_ORIGIN=https://app.domain.ru задаётся после выпуска.
До покупки VPS и домена публичного нового адреса нет.
Проверяйте доступ без VPN из сети сотрудников; никакой хостинг не даёт
абсолютной гарантии доступности на каждом провайдере.
