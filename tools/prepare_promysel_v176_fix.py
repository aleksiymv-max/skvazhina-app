from pathlib import Path
p=Path.cwd()/'lib/features/organization/training_screen.dart'
p.write_text(r'''import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../../core/services/training_store.dart';
import '../../core/services/sync_service.dart';

class TrainingScreen extends StatefulWidget {
  const TrainingScreen({super.key, required this.userId});
  final String userId;
  @override
  State<TrainingScreen> createState() => _TrainingScreenState();
}

class _TrainingScreenState extends State<TrainingScreen> {
  Future<void> _add() async {
    final ctl = TextEditingController();
    DateTime? next;
    final ok = await showDialog<bool>(
      context: context,
      builder: (c) => StatefulBuilder(
        builder: (c, setD) => AlertDialog(
          title: const Text('Добавить обучение'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(controller: ctl, decoration: const InputDecoration(labelText: 'Наименование обучения')),
              const SizedBox(height: 12),
              ListTile(
                contentPadding: EdgeInsets.zero,
                leading: const Icon(Icons.event_outlined),
                title: const Text('Дата следующего прохождения'),
                subtitle: Text(next == null ? 'Выберите дату' : DateFormat('dd.MM.yyyy').format(next!)),
                onTap: () async {
                  final d = await showDatePicker(
                    context: c,
                    initialDate: next ?? DateTime.now().add(const Duration(days: 365)),
                    firstDate: DateTime.now(),
                    lastDate: DateTime.now().add(const Duration(days: 3650)),
                  );
                  if (d != null) setD(() => next = d);
                },
              ),
            ],
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(c, false), child: const Text('Отмена')),
            FilledButton(onPressed: () => Navigator.pop(c, true), child: const Text('Сохранить')),
          ],
        ),
      ),
    );
    if (ok == true && ctl.text.trim().isNotEmpty && next != null) {
      await TrainingStore.instance.add(TrainingItem(
        id: DateTime.now().microsecondsSinceEpoch.toString(),
        userId: widget.userId,
        title: ctl.text.trim(),
        date: next!,
      ));
      SyncService.instance.markStateDirty();
      if (mounted) setState(() {});
    }
    ctl.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Обучение')),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _add,
        icon: const Icon(Icons.add),
        label: const Text('Добавить'),
      ),
      body: ListenableBuilder(
        listenable: TrainingStore.instance,
        builder: (context, _) {
          final list = TrainingStore.instance.forUser(widget.userId);
          if (list.isEmpty) return const Center(child: Text('Обучение пока не добавлено.'));
          return ListView(
            padding: const EdgeInsets.all(16),
            children: list.map((x) => Card(
              child: ListTile(
                leading: const Icon(Icons.school_outlined),
                title: Text(x.title, style: const TextStyle(fontWeight: FontWeight.w800)),
                subtitle: Text('Следующее прохождение: ${DateFormat('dd.MM.yyyy').format(x.date)}'),
                trailing: IconButton(
                  icon: const Icon(Icons.delete_outline),
                  onPressed: () async {
                    await TrainingStore.instance.remove(x.id);
                    SyncService.instance.markStateDirty();
                  },
                ),
              ),
            )).toList(),
          );
        },
      ),
    );
  }
}
''')
s=p.read_text()
assert 'class TrainingScreen extends StatefulWidget' in s
assert 'Дата следующего прохождения' in s
assert 'children: list.map((x) => Card(' in s
print('v1.76.2 training screen rewritten with valid structured Dart',flush=True)
