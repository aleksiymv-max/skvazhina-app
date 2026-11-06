import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:http/http.dart' as http;
import '../../core/services/sync_service.dart';

/// Read-only help and diagnostics. Never clears local state, tokens or queues.
class PromyselAboutScreen extends StatelessWidget {
  const PromyselAboutScreen({super.key});

  void _open(BuildContext context, Widget page) {
    Navigator.of(context).push(MaterialPageRoute<void>(builder: (_) => page));
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(title: const Text('О приложении')),
      body: ListView(padding: const EdgeInsets.all(16), children: [
        Card(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 24),
            child: Column(children: [
              Icon(Icons.oil_barrel_outlined, size: 54, color: theme.colorScheme.primary),
              const SizedBox(height: 12),
              Text('ПРОМЫСЕЛ', style: theme.textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w800)),
              const SizedBox(height: 5),
              const Text('Цифровая система производственного учёта',
                textAlign: TextAlign.center),
              const SizedBox(height: 10),
              const Chip(label: Text('Версия v2.17')),
            ]),
          ),
        ),
        const SizedBox(height: 12),
        _item(context, Icons.info_outline, 'О системе',
          'Назначение, возможности и пользователи',
          const _AboutTextPage()),
        _item(context, Icons.menu_book_outlined, 'Руководство пользователя',
          'Обход, история, задания и работа без сети',
          const _ManualPage()),
        _item(context, Icons.history_toggle_off_outlined, 'Версия и история обновлений',
          'Что изменилось в последних выпусках',
          const _ReleasePage()),
        _item(context, Icons.cloud_outlined, 'Состояние сервера и синхронизации',
          'Проверка связи, ожидающие замеры и последний обмен',
          const PromyselConnectionPage()),
        const SizedBox(height: 14),
        const Text('Информация о разработчике и правообладателе будет добавлена после подтверждения прав.',
          textAlign: TextAlign.center,
          style: TextStyle(fontSize: 12, color: Colors.grey)),
      ]),
    );
  }

  Widget _item(BuildContext context, IconData icon, String title,
      String subtitle, Widget page) => Card(
    margin: const EdgeInsets.only(bottom: 8),
    child: ListTile(
      leading: Icon(icon, color: Theme.of(context).colorScheme.primary),
      title: Text(title, style: const TextStyle(fontWeight: FontWeight.w600)),
      subtitle: Text(subtitle),
      trailing: const Icon(Icons.chevron_right),
      onTap: () => _open(context, page),
    ),
  );
}

class _AboutTextPage extends StatelessWidget {
  const _AboutTextPage();
  @override Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('О системе')),
    body: ListView(padding: const EdgeInsets.all(18), children: const [
      _Section('ПРОМЫСЕЛ',
        'Приложение помогает сотрудникам нефтегазового промысла вести технологические обходы, фиксировать производственные замечания, управлять заданиями и обмениваться рабочей информацией.'),
      _Section('Для кого',
        'Для операторов ДНГ, инженерно-технических работников, мастеров и руководителей цеха. Возможности зависят от назначенной роли.'),
      _Section('Основные возможности',
        'Учёт месторождений, участков добычи, кустовых площадок и скважин; обходы и история замеров; проблемные вопросы; задания с фотографиями; чаты; обучение и график работы.'),
      _Section('Работа без интернета',
        'Ранее сохранённые данные и доступные офлайн-функции остаются на устройстве. Неотправленные замеры должны сохраняться в очереди до подтверждения сервером.'),
      _Section('Важно',
        'Промысел является инструментом производственного учёта и не заменяет утверждённые требования промышленной безопасности и эксплуатационную документацию.'),
    ]),
  );
}

class _Section extends StatelessWidget {
  const _Section(this.heading, this.body);
  final String heading, body;
  @override Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(bottom: 20),
    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text(heading, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
      const SizedBox(height: 7), Text(body),
    ]),
  );
}

class _ManualPage extends StatelessWidget {
  const _ManualPage();
  @override Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Руководство пользователя')),
    body: ListView(padding: const EdgeInsets.all(12), children: const [
      _ManualTile('Главная',
        'Просматривайте сводные показатели месторождения, фонд скважин, сотрудников и зарегистрированные проблемные вопросы.'),
      _ManualTile('Обход',
        'Выберите участок, кустовую площадку и скважину. Заполните доступные для неё технологические параметры, проверьте значения и сохраните обход. При отсутствии интернета не удаляйте приложение: ожидающие записи отправятся после восстановления соединения.'),
      _ManualTile('История и тренды',
        'Выберите площадку, скважину и дату, чтобы открыть сохранённые измерения. Корректировка и выгрузка данных доступны сотрудникам с соответствующими правами.'),
      _ManualTile('Проблемные вопросы',
        'При обнаружении неисправности зарегистрируйте проблему во время обхода. Руководители и ИТР смогут увидеть её для организации устранения.'),
      _ManualTile('Задания',
        'Откройте назначенное задание, ознакомьтесь с описанием и при выполнении приложите комментарий и необходимые фотографии. Закрытие задания может требовать подтверждения руководителем.'),
      _ManualTile('Чаты',
        'Используйте рабочие чаты для переписки с сотрудниками и обмена доступными вложениями. При слабом интернете дождитесь подтверждения отправки.'),
      _ManualTile('Мой график и обучение',
        'В профиле управляйте своим графиком, просматривайте обучение и уведомления. Набор функций определяется ролью.'),
      _ManualTile('Если нет связи с сервером',
        'Откройте «Меню → О приложении → Состояние сервера и синхронизации». Проверьте ответ сервера и очередь замеров. Не очищайте данные браузера и не переустанавливайте приложение, пока остались неотправленные записи.'),
    ]),
  );
}

class _ManualTile extends StatelessWidget {
  const _ManualTile(this.title, this.description);
  final String title, description;
  @override Widget build(BuildContext context) => Card(
    child: ExpansionTile(title: Text(title, style: const TextStyle(fontWeight: FontWeight.w600)),
      children: [Padding(padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
        child: Align(alignment: Alignment.centerLeft, child: Text(description)))]),
  );
}

class _ReleasePage extends StatelessWidget {
  const _ReleasePage();
  @override Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Версия и история обновлений')),
    body: ListView(padding: const EdgeInsets.all(16), children: const [
      _Section('Текущая версия: v2.17 · 06.11.2026',
        'Добавлены расширенные коды диагностики обмена, проверка этапов импорта SQLite и восстановления данных, а также ручной повтор без ожидания автоматической паузы.'),
      _Section('v2.16',
        'Расширена диагностика стадий синхронизации и ручная повторная попытка.'),
      _Section('v2.15',
        'Добавлены «О приложении», руководство, проверка сервера и улучшено отображение сетевых ошибок.'),
      _Section('v2.14',
        'Оптимизированы ожидания синхронизации отдельных разделов и сохранение очереди при частичных ошибках.'),
      _Section('v2.13',
        'Добавлена пакетная отправка замеров с подтверждением и уменьшена повторная передача фотографий сотрудников.'),
      _Section('v2.11',
        'Разделены очереди изменений структуры, задач, обучения и графика работы.'),
      _Section('Обновление приложения',
        'Веб-приложение обновляется после публикации новой сборки. Если версия не изменилась, полностью закройте и повторно откройте приложение. Не очищайте данные сайта при наличии неотправленных обходов.'),
    ]),
  );
}

class PromyselConnectionPage extends StatefulWidget {
  const PromyselConnectionPage({super.key});
  @override State<PromyselConnectionPage> createState() => _PromyselConnectionPageState();
}

class _PromyselConnectionPageState extends State<PromyselConnectionPage> {
  static const _base = String.fromEnvironment('PROMYSEL_SYNC_URL',
    defaultValue: 'https://xptmcufhuvtcunqzlsme.supabase.co/functions/v1/promysel-compat');
  bool _checking = false;
  bool? _reachable;
  String _probeDescription = 'Проверка сервера ещё не проводилась';

  @override void initState() {
    super.initState();
    unawaited(_probe());
  }

  Future<void> _probe() async {
    if (_checking) return;
    setState(() { _checking = true; _probeDescription = 'Проверяем ответ сервера…'; });
    try {
      final response = await http.get(Uri.parse(_base + '/health'),
        headers: const {'cache-control': 'no-store'}).timeout(const Duration(seconds: 7));
      if (!mounted) return;
      setState(() {
        _reachable = response.statusCode >= 200 && response.statusCode < 300;
        _probeDescription = _reachable!
          ? 'Сервер отвечает на контрольный запрос'
          : 'Сервер ответил с кодом HTTP ' + response.statusCode.toString();
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _reachable = false;
        _probeDescription = 'Контрольный запрос не завершился. Проверьте сеть.';
      });
    } finally {
      if (mounted) setState(() => _checking = false);
    }
  }

  String _date(DateTime? at) {
    if (at == null) return 'Успешный обмен ещё не зарегистрирован';
    final local = at.toLocal();
    String two(int n) => n.toString().padLeft(2, '0');
    return two(local.day) + '.' + two(local.month) + '.' +
      local.year.toString() + '  ' + two(local.hour) + ':' + two(local.minute);
  }

  @override Widget build(BuildContext context) {
    final sync = SyncService.instance;
    return Scaffold(
      appBar: AppBar(title: const Text('Сервер и синхронизация')),
      body: ListenableBuilder(listenable: sync, builder: (context, _) {
        final available = sync.serverAvailable;
        final busy = sync.syncing;
        return ListView(padding: const EdgeInsets.all(16), children: [
          Card(child: Padding(padding: const EdgeInsets.all(16),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text('Доступность сервера',
                style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
              const SizedBox(height: 10),
              Row(children: [
                Icon(_reachable == null ? Icons.help_outline :
                  _reachable! ? Icons.check_circle_outline : Icons.error_outline,
                  color: _reachable == true ? Colors.green : null),
                const SizedBox(width: 10),
                Expanded(child: Text(_probeDescription)),
              ]),
              const SizedBox(height: 10),
              OutlinedButton.icon(
                onPressed: _checking ? null : () => unawaited(_probe()),
                icon: const Icon(Icons.refresh), label: const Text('Проверить сервер')),
            ]),
          )),
          const SizedBox(height: 10),
          Card(child: Padding(padding: const EdgeInsets.all(16),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text('Обмен данными приложения',
                style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
              const SizedBox(height: 10),
              Text(busy ? 'Синхронизация выполняется' :
                available ? 'Последний запрос выполнен' : 'Состояние обмена требует проверки',
                style: const TextStyle(fontWeight: FontWeight.w600)),
              const SizedBox(height: 8),
              Text(sync.status),
              const Divider(height: 28),
              _metric('Ожидающие замеры', sync.pending.toString()),
              const SizedBox(height: 8),
              _metric('Последний успешный обмен', _date(sync.lastSyncAt)),
              if(sync.lastSyncFailurePhase!=null)...[
                const SizedBox(height: 12),
                _metric('Этап последней ошибки',sync.lastSyncFailurePhase!),
                const SizedBox(height: 8),
                _metric('Тип ошибки',sync.lastSyncFailureType??'Не определён'),
                if(sync.lastSyncHttpStatus!=null)...[
                  const SizedBox(height:8),
                  _metric('Код ответа HTTP',sync.lastSyncHttpStatus.toString()),
                ],
                const SizedBox(height: 8),
                _metric('Время ошибки',_date(sync.lastSyncFailureAt)),
                const SizedBox(height: 12),
                OutlinedButton.icon(
                  onPressed: () {
                    final safeReport='Промысел v2.16\n'
                      'Этап: ${sync.lastSyncFailurePhase??"не определён"}\n'
                      'Тип: ${sync.lastSyncFailureType??"не определён"}\n'
                      'Время: ${_date(sync.lastSyncFailureAt)}\n'
                      'Ожидающих замеров: ${sync.pending}\n'
                      'HTTP: ${sync.lastSyncHttpStatus?.toString()??"нет"}';
                    Clipboard.setData(ClipboardData(text:safeReport));
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content:Text('Диагностический код скопирован')));
                  },
                  icon:const Icon(Icons.copy_outlined),
                  label:const Text('Скопировать диагностику')),
              ],
              const SizedBox(height: 14),
              FilledButton.icon(
                onPressed: busy ? null : () { unawaited(sync.syncNow(force:true)); },
                icon: const Icon(Icons.sync),
                label: Text(busy ? 'Синхронизация выполняется…' : 'Повторить синхронизацию')),
            ]),
          )),
          const SizedBox(height: 14),
          const Text('Важно: ответ сервера на проверку связи не означает, что все данные синхронизированы. Ориентируйтесь также на количество ожидающих замеров и время последнего успешного обмена.',
            style: TextStyle(fontSize: 12)),
          const SizedBox(height: 12),
          const Text('Не удаляйте приложение и не очищайте данные браузера при незавершённой синхронизации.',
            style: TextStyle(fontWeight: FontWeight.w600)),
        ]);
      }),
    );
  }

  Widget _metric(String label, String value) => Row(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Expanded(child: Text(label, style: const TextStyle(color: Colors.grey))),
      const SizedBox(width: 12),
      Flexible(child: Text(value, textAlign: TextAlign.end,
        style: const TextStyle(fontWeight: FontWeight.w600))),
    ],
  );
}
