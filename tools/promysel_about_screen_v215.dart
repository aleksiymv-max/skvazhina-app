import 'dart:async';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
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
              const Chip(label: Text('Версия v2.19')),
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
        _item(context, Icons.history_toggle_off_outlined, 'Версия приложения',
          'Номер установленной версии',
          const _ReleasePage()),
        _item(context, Icons.cloud_outlined, 'Состояние сервера и синхронизации',
          'Единая проверка системы и передачи данных',
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

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Руководство пользователя')),
    body: ListView(
      padding: const EdgeInsets.fromLTRB(14, 16, 14, 28),
      children: const [
        _Section('Как пользоваться «Промыслом»',
          'Откройте интересующий раздел ниже. Инструкция рассчитана на сотрудников промысла. Доступные действия зависят от вашей роли и настроек месторождения.'),
        _ManualTile('Первый вход и выбор месторождения', [
          'Войдите с учётными данными, полученными после согласования регистрации.',
          'Проверьте ФИО, роль и выбранное месторождение в профиле.',
          'Если данные месторождения ещё загружаются, проверьте соединение через «Меню → О приложении → Состояние сервера и синхронизации».',
        ], note:'Не создавайте вторую учётную запись из-за временной ошибки соединения.'),
        _ManualTile('Главная страница', [
          'Просматривайте количество участков добычи, кустовых площадок и скважин, состояние фонда и общие показатели.',
          'Откройте карточку интересующего раздела для подробной информации.',
          'Контролируйте открытые производственные проблемы и сведения о персонале.',
        ]),
        _ManualTile('Обход скважин', [
          'Перейдите во вкладку «Обход», выберите участок добычи, кустовую площадку и скважину.',
          'Заполните только параметры, предусмотренные для данной площадки и скважины. Используйте запятую или точку для дробных значений.',
          'Для нефтяных скважин отмечайте ПКВ/ПИД, если соответствующие параметры включены в настройках. Для газоконденсатных скважин вводите доступные давления, температуры и положение штуцера или дросселя.',
          'Проверьте значения и сохраните обход. При слабой связи дождитесь подтверждения отправки; несинхронизированный замер должен оставаться на устройстве.',
        ], note:'Не повторяйте сохранение многократно. Проверяйте историю и состояние очереди.'),
        _ManualTile('История замеров и тренды', [
          'Откройте «История», выберите кустовую площадку, скважину и дату.',
          'Просмотрите сохранённые значения и параметры конкретного обхода.',
          'Для анализа изменений откройте тренд нужного параметра и период наблюдения.',
          'Корректировка данных и выгрузки доступны только ролям, которым предоставлены соответствующие права.',
        ]),
        _ManualTile('Участки, кусты и скважины', [
          'Откройте структуру месторождения через меню или главную страницу.',
          'Выберите участок, кустовую площадку и скважину для просмотра параметров.',
          'Создание и редактирование структуры доступны уполномоченным ИТР. Удаление объектов ограничено правами руководителя или администратора.',
        ], note:'Изменения структуры должны появиться на других устройствах после синхронизации.'),
        _ManualTile('Производственные проблемы', [
          'При обнаружении неисправности зарегистрируйте проблемный вопрос в доступном разделе.',
          'Укажите объект и кратко опишите ситуацию без лишних персональных данных.',
          'Следите за состоянием вопроса; руководитель и ИТР используют запись для организации устранения.',
        ]),
        _ManualTile('Задания и фотографии', [
          'Откройте вкладку «Задания», выберите назначенное поручение.',
          'Изучите содержание, срок и объект, добавьте комментарий и фотографии при необходимости.',
          'Отметьте выполнение. Если предусмотрено подтверждение, дождитесь решения проверяющего.',
          'До успешной отправки не удаляйте локальные данные и вложения.',
        ]),
        _ManualTile('Чаты', [
          'Откройте вкладку «Чат», выберите переписку или создайте новую, если это разрешено.',
          'Отправляйте рабочие сообщения, фотографии и документы только предназначенным участникам.',
          'Удержание чата открывает дополнительные действия, например закрепление и отключение уведомлений, если они доступны в вашей версии.',
          'При слабой связи проверяйте, что сообщение действительно отправлено.',
        ]),
        _ManualTile('Персонал и статус работы', [
          'Откройте раздел персонала, чтобы посмотреть сотрудников и их доступные рабочие статусы.',
          'Отметки «На работе» и «Отдыхает» меняются сотрудником или уполномоченным руководителем.',
          'Полночь сама по себе не означает окончание вахты. Последний подтверждённый статус должен сохраняться до явного изменения.',
          'Если статус не обновился на другом устройстве, выполните проверку системы и синхронизации.',
        ]),
        _ManualTile('Мой график, отпуск и обучение', [
          'Откройте профиль и раздел «Мой график», выберите дни вахты, отдыха или отпуска.',
          'При необходимости настройте шаблон чередования или уточните даты вручную.',
          'В разделе обучения просматривайте назначенные мероприятия и их состояние.',
          'Следите за уведомлениями о заданиях, сообщениях и изменениях графика.',
        ]),
        _ManualTile('Работа без интернета', [
          'Ранее полученные сведения могут оставаться доступными локально.',
          'Сохраняйте обходы в обычном порядке; после восстановления связи повторите проверку синхронизации.',
          'Откройте «Меню → О приложении → Состояние сервера и синхронизации» и нажмите единственную кнопку проверки.',
          'Если появилась ошибка, сообщите техническому специалисту описание, код, тип и этап ошибки.',
        ], note:'Не очищайте данные браузера, не удаляйте приложение и не выходите из учётной записи, пока есть неотправленные данные.'),
        _ManualTile('Безопасность работы', [
          'Работайте только под собственной учётной записью и не передавайте пароль другим сотрудникам.',
          'Используйте приложение для производственного учёта; оно не заменяет эксплуатационные регламенты и требования безопасности.',
          'Не прикладывайте к чатам и заданиям документы, которые не должны быть доступны участникам переписки.',
        ]),
      ],
    ),
  );
}

class _ManualTile extends StatelessWidget {
  const _ManualTile(this.title, this.steps, {this.note});
  final String title;
  final List<String> steps;
  final String? note;

  @override Widget build(BuildContext context) {
    const radius = BorderRadius.all(Radius.circular(16));
    const tileShape = RoundedRectangleBorder(
      borderRadius: radius,
      side: BorderSide(color: Colors.transparent, width: 0),
    );
    final scheme = Theme.of(context).colorScheme;
    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      shape: tileShape,
      clipBehavior: Clip.antiAlias,
      child: Theme(
        data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
        child: ExpansionTile(
          shape: tileShape,
          collapsedShape: tileShape,
          tilePadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
          childrenPadding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
          title: Text(title, style: const TextStyle(
            fontSize: 15, fontWeight: FontWeight.w700)),
          children: [
            for (var i = 0; i < steps.length; i++)
              Padding(
                padding: const EdgeInsets.only(top: 11),
                child: Row(crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Container(
                      width: 25, height: 25,
                      alignment: Alignment.center,
                      decoration: BoxDecoration(
                        color: scheme.primaryContainer,
                        borderRadius: BorderRadius.circular(8)),
                      child: Text('${i + 1}', style: TextStyle(
                        color: scheme.onPrimaryContainer,
                        fontSize: 12, fontWeight: FontWeight.bold)),
                    ),
                    const SizedBox(width: 10),
                    Expanded(child: Padding(
                      padding: const EdgeInsets.only(top: 2),
                      child: Text(steps[i],
                        style: const TextStyle(fontSize: 14, height: 1.45)))),
                  ],
                ),
              ),
            if (note != null)
              Container(
                margin: const EdgeInsets.only(top: 16),
                padding: const EdgeInsets.all(12),
                width: double.infinity,
                decoration: BoxDecoration(
                  color: scheme.primaryContainer.withOpacity(.45),
                  borderRadius: BorderRadius.circular(12)),
                child: Text(note!, style: TextStyle(
                  color: scheme.onSurface, fontSize: 13, height: 1.35)),
              ),
          ],
        ),
      ),
    );
  }
}

class _ReleasePage extends StatelessWidget {
  const _ReleasePage();
  @override Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Версия приложения')),
    body: ListView(padding: const EdgeInsets.all(18), children: [
      Card(child: Padding(
        padding: const EdgeInsets.all(22),
        child: Column(children: [
          Icon(Icons.apps_rounded, size: 42, color: Theme.of(context).colorScheme.primary),
          const SizedBox(height: 12),
          Text('ПРОМЫСЕЛ', style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 6),
          const Text('Версия v2.19', style: TextStyle(
            fontWeight: FontWeight.bold, fontSize: 18)),
          const SizedBox(height: 5),
          const Text('Веб-приложение · 6 ноября 2026 года'),
        ]),
      )),
      const SizedBox(height: 16),
      const Text('Обновления устанавливаются при публикации новой версии приложения. Если отображается старая версия, полностью закройте и повторно откройте приложение.',
        style: TextStyle(height: 1.45)),
      const SizedBox(height: 10),
      const Text('Не очищайте данные сайта при наличии неотправленных обходов.',
        style: TextStyle(fontWeight: FontWeight.w600)),
    ]),
  );
}

class _CheckIssue {
  const _CheckIssue(this.description, this.code, this.type,
      {this.stage});
  final String description, code, type;
  final String? stage;
}

class PromyselConnectionPage extends StatefulWidget {
  const PromyselConnectionPage({super.key});
  @override State<PromyselConnectionPage> createState() =>
    _PromyselConnectionPageState();
}

class _PromyselConnectionPageState extends State<PromyselConnectionPage> {
  static const _base = String.fromEnvironment('PROMYSEL_SYNC_URL',
    defaultValue: 'https://xptmcufhuvtcunqzlsme.supabase.co/functions/v1/promysel-compat');
  bool _checking=false, _checked=false;
  bool? _systemOk, _serverOk, _syncOk;
  final List<_CheckIssue> _issues=[];
  String _checkStatus='Проверка ещё не выполнялась';

  String _codeForPhase(String? phase) {
    final value=(phase??'unknown').replaceAll(
      RegExp(r'[^A-Za-z0-9]'),'_').toUpperCase();
    return 'SYNC_' + value;
  }

  String _explainPhase(String? phase) {
    if (phase==null) return 'Обмен завершился без подтверждения успеха.';
    if (phase.contains('persistence')) {
      return 'Не удалось записать полученный снимок на устройство. '
        'Возможна нехватка места в браузерном хранилище.';
    }
    if (phase.contains('sqlite_measurement')) {
      return 'Не удалось сохранить полученные замеры в локальной базе.';
    }
    if (phase.contains('http') || phase.contains('auth')) {
      return 'Ошибка запроса к серверу или авторизации. '
        'Проверьте доступ к сети и действительность сеанса.';
    }
    if (phase.contains('snapshot')) {
      return 'Ошибка восстановления структуры или связанных данных месторождения.';
    }
    return 'Обмен прерван на этапе «' + phase + '». Локальные данные сохранены.';
  }

  Future<void> _checkAll() async {
    final sync=SyncService.instance;
    if (_checking || sync.syncing) return;
    final started=DateTime.now();
    setState(() {
      _checking=true;
      _checked=false;
      _issues.clear();
      _systemOk=null;_serverOk=null;_syncOk=null;
      _checkStatus='Проверяем приложение, сервер и передачу данных…';
    });
    try {
      try {
        final prefs=await SharedPreferences.getInstance();
        // Read-only check: never remove or rewrite local state or queue.
        prefs.getKeys();
        _systemOk=true;
      } catch (_) {
        _systemOk=false;
        _issues.add(const _CheckIssue(
          'Не удаётся прочитать локальное хранилище устройства. '
          'Сохранённые данные не очищались.',
          'LOCAL_STORAGE_READ', 'Ошибка локального хранилища'));
      }

      try {
        final uri=Uri.parse('$_base/health').replace(
          queryParameters:{'check':DateTime.now().millisecondsSinceEpoch.toString()});
        final response=await http.get(uri,
          headers:const {'cache-control':'no-store'})
          .timeout(const Duration(seconds:7));
        _serverOk=response.statusCode>=200&&response.statusCode<300;
        if (_serverOk!=true) {
          _issues.add(_CheckIssue(
            'Контрольный запрос получил ответ сервера с ошибкой.',
            'HTTP_${response.statusCode}', 'Ошибка HTTP', stage:'server.health'));
        }
      } on TimeoutException {
        _serverOk=false;
        _issues.add(const _CheckIssue(
          'Контрольный запрос не завершился за 7 секунд.',
          'SERVER_TIMEOUT', 'Превышено время ожидания',stage:'server.health'));
      } catch (_) {
        _serverOk=false;
        _issues.add(const _CheckIssue(
          'Не удалось подключиться к серверу. Проверьте доступ к интернету.',
          'SERVER_NETWORK', 'Ошибка сетевого соединения',stage:'server.health'));
      }

      if (_systemOk==true && _serverOk==true) {
        try {
          await sync.syncNow(force:true);
          final failedAt=sync.lastSyncFailureAt;
          final successAt=sync.lastSyncAt;
          final freshFailure=failedAt!=null&&!failedAt.isBefore(started);
          final freshSuccess=successAt!=null&&!successAt.isBefore(started);
          if (freshFailure) {
            _syncOk=false;
            final code=sync.lastSyncHttpStatus==null
              ?_codeForPhase(sync.lastSyncFailurePhase)
              :'HTTP_${sync.lastSyncHttpStatus}';
            _issues.add(_CheckIssue(
              sync.lastSyncStorageCause??_explainPhase(sync.lastSyncFailurePhase),
              code,
              sync.lastSyncFailureType??'Ошибка синхронизации',
              stage:sync.lastSyncFailurePhase));
          } else if(freshSuccess&&sync.pending==0) {
            _syncOk=true;
          } else {
            _syncOk=false;
            _issues.add(_CheckIssue(
              sync.status.isEmpty?'Подтверждение успешной синхронизации не получено.'
                :sync.status,
              sync.pending>0?'SYNC_PENDING': 'SYNC_UNCONFIRMED',
              sync.pending>0?'Ожидают отправки':'Обмен не подтверждён',
              stage:'sync.status'));
          }
        } catch (_) {
          _syncOk=false;
          _issues.add(const _CheckIssue(
            'Произошла ошибка во время проверки синхронизации. '
            'Локальные записи не очищались.',
            'SYNC_CHECK_FAILED','Ошибка приложения',stage:'sync.check'));
        }
      } else {
        _syncOk=null; // Skip remote sync if a prerequisite is unavailable.
      }
    } finally {
      if (mounted) setState(() {
        _checking=false;_checked=true;
        _checkStatus=_issues.isEmpty
          ?'Проверка завершена: ошибок не обнаружено'
          :'Проверка завершена: обнаружены проблемы';
      });
    }
  }

  Widget _line(IconData icon, String label, bool? result,
      {String? pending}) {
    final scheme=Theme.of(context).colorScheme;
    return Padding(padding:const EdgeInsets.symmetric(vertical:6),
      child:Row(children:[
        Icon(icon,size:21,color:result==null?scheme.outline:
          result?Colors.green:scheme.error),
        const SizedBox(width:10),
        Expanded(child:Text(label)),
        Flexible(child:Text(result==null?(pending??'Не проверено'):
          result?'Успешно':'Ошибка',
          textAlign:TextAlign.end,style:TextStyle(
            color:result==false?scheme.error:null,
            fontWeight:FontWeight.w600))),
      ]));
  }

  @override Widget build(BuildContext context) {
    final sync=SyncService.instance;
    final scheme=Theme.of(context).colorScheme;
    return Scaffold(
      appBar:AppBar(title:const Text('Сервер и синхронизация')),
      body:ListenableBuilder(listenable:sync,builder:(context,_) {
        final disabled=_checking||sync.syncing;
        return ListView(padding:const EdgeInsets.all(16),children:[
          Card(child:Padding(padding:const EdgeInsets.all(18),
            child:Column(crossAxisAlignment:CrossAxisAlignment.stretch,children:[
              Text('Проверка системы',style:Theme.of(context).textTheme.titleLarge
                ?.copyWith(fontWeight:FontWeight.w700)),
              const SizedBox(height:8),
              const Text('Одной кнопкой проверяются локальные данные приложения, '
                'доступность сервера и фактическая синхронизация.',
                style:TextStyle(height:1.4)),
              const SizedBox(height:16),
              FilledButton.icon(
                onPressed:disabled?null:_checkAll,
                icon:_checking?const SizedBox(width:18,height:18,
                   child:CircularProgressIndicator(strokeWidth:2)):
                   const Icon(Icons.fact_check_outlined),
                label:Text(_checking?'Проверка выполняется…':
                  sync.syncing?'Дождитесь завершения обмена':
                  'Проверить систему')),
              const SizedBox(height:14),
              Text(_checkStatus,style:TextStyle(
                fontWeight:FontWeight.w600,
                color:_checked&&_issues.isNotEmpty?scheme.error:null)),
              const SizedBox(height:10),
              _line(Icons.phone_iphone,'Приложение',_systemOk,
                pending:_checking?'Проверяется':'Не проверено'),
              _line(Icons.cloud_outlined,'Сервер',_serverOk,
                pending:_checking?'Проверяется':'Не проверено'),
              _line(Icons.sync,'Синхронизация',_syncOk,
                pending:_checking?'Проверяется':'Не проверено'),
              const Divider(height:28),
              Text('Ожидают отправки замеры: ${sync.pending}'),
              const SizedBox(height:5),
              Text(sync.lastSyncAt==null
                ?'Успешный обмен ещё не зарегистрирован'
                :'Последний успешный обмен: ${_stamp(sync.lastSyncAt!)}'),
            ]))),
          if(_checked&&_issues.isNotEmpty)...[
            const SizedBox(height:14),
            Text('Обнаруженные ошибки',style:Theme.of(context)
              .textTheme.titleMedium?.copyWith(fontWeight:FontWeight.bold)),
            const SizedBox(height:8),
            for(final issue in _issues)
              Card(
                color:scheme.errorContainer.withOpacity(.40),
                child:Padding(padding:const EdgeInsets.all(16),
                  child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
                    Text('Описание ошибки',style:TextStyle(
                      color:scheme.error,fontWeight:FontWeight.w700)),
                    const SizedBox(height:5),
                    SelectableText(issue.description),
                    const SizedBox(height:12),
                    _detail('Код ошибки',issue.code),
                    const SizedBox(height:7),
                    _detail('Тип ошибки',issue.type),
                    if(issue.stage!=null)...[
                      const SizedBox(height:7),
                      _detail('Этап',issue.stage!),
                    ]
                  ])))
          ],
          const SizedBox(height:16),
          const Text('При неудачной синхронизации не очищайте данные браузера '
            'и не удаляйте приложение: неотправленные записи должны сохраниться.',
            style:TextStyle(fontWeight:FontWeight.w600,height:1.35)),
        ]);
      }),
    );
  }

  static String _stamp(DateTime date) {
    final d=date.toLocal();
    String t(int x)=>x.toString().padLeft(2,'0');
    return '${t(d.day)}.${t(d.month)}.${d.year} ${t(d.hour)}:${t(d.minute)}';
  }

  Widget _detail(String title,String value)=>Row(
    crossAxisAlignment:CrossAxisAlignment.start,
    children:[
      SizedBox(width:106,child:Text(title,style:const TextStyle(fontSize:13))),
      const SizedBox(width:8),
      Expanded(child:SelectableText(value,
        style:const TextStyle(fontWeight:FontWeight.w700,fontSize:13))),
    ]);
}
