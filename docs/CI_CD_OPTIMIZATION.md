# Promysel CI/CD — экономный режим

**Исходный код:** `aleksiymv-max/skvazhina-app`, branch `main`, исходный архив `neftyanik_v1.24.1_stable_hotfix.zip` + последовательные `tools/prepare_promysel_*.py` и патчи. `aleksiymv-max/promysel-web` содержит только README и не является исходным Flutter-проектом.

**Web DEV:** вручную Actions → **Build Promysel Web for iPhone** → Run workflow на main. Проверка API, генерация исходников, тесты, Flutter Web release, проверка ZIP; затем Wrangler публикует только ветку `dev` Cloudflare Pages, адрес `https://dev.promysel-web.pages.dev`. Если проверка провалена — публикации нет. Артефакт web 7 дней.

**Web PROD:** вручную Actions → **Promysel — вручную опубликовать проверенную Web-версию**. Введите run_id успешной Web-сборки и PROMOTE. Повторная сборка НЕ запускается; публикуется тот же проверенный ZIP в production-ветку `main` проекта `promysel-web`; проверяются результат сборки, ancestry stable и состав архива. Сериализация production: `promysel-production-release`, `cancel-in-progress:false`, Environment production. Адрес `https://promysel-web.pages.dev` не меняется. Сайт `https://promysel-app.tuqo.ru` и его загрузки не затрагиваются.

**Android (исходники без APK):** компиляция Android в GitHub отключена полностью — активный workflow `.github/workflows/android.yml` удалён из .github/workflows, исходная конфигурация сохранена как `tools/archive/android-build.workflow.yml.txt` (неисполняемый архив). Изменения Flutter вносятся в общий исходный проект (ZIP + `tools/prepare_promysel_*.py` + patches), а Android-рецепт обновляется синхронно при каждом изменении Web. Лёгкий тест `tools/check_promysel_android_source_sync.py` сравнивает список общих патчей и проверок двух платформ; никаких Android SDK, Gradle, APK или расходов минут на APK. Когда понадобится APK, будет отдельное решение о разовой сборке — сейчас она запрещена. **Stability diagnostic** — только вручную. VPN-free ZIP workflows — только вручную, без веб-сборки.

**Automatic fast check:** короткая проверка Python и регистрации при изменениях исходного кода, серверных файлов и workflows; документация .md исключена. `timeout-minutes:4`, `cancel-in-progress:true` только для короткой проверки.

**Rollback:** Cloudflare Dashboard → Workers & Pages → promysel-web → Deployments → выберите прежнюю рабочую production deployment → Rollback; сохраняется Pages URL. Git stable pointer должен быть приведён к реально опубликованной версии после отката. Для Tuqo используйте сохранённый исправный ZIP и историю деплоев Tuqo; не заменяйте PROD тестовым архивом.

**Секреты:** Cloudflare token/account ID остаются GitHub Secrets; действия не выводят их в логи. `promysel-web` репозиторий и Supabase не менялись.

**Ручное действие в Cloudflare (при наличии Git-интеграции):** Pages → Settings → Builds/Branch control. Выключить автоматическую сборку в production и preview, поскольку выпуск ведётся из GitHub Actions через Wrangler. Без доступа к Cloudflare Dashboard факт наличия второго автоматического билда неизвестен.


## Режим релизов после 4 ноября 2026
По умолчанию каждое изменение готовится для **DEV и PROD**, с одним Web-артефактом: сначала Flutter-анализ/тесты, Cloudflare DEV, затем продвижение точно того же проверенного артефакта в Cloudflare PROD. Без успешной проверки публикация PROD запрещена. Когда пользователь явно укажет «только DEV», пропустить продвижение PROD. Рабочий сайт Tuqo `promysel-app.tuqo.ru` не управляется Cloudflare workflow: ZIP той же Web-сборки необходимо отдельно загрузить через Tuqo Deploys, не смешивая его с DEV-архивом, где есть отметка разработчика. Исходники Android сохраняются синхронно, APK не собирается.
