import 'package:artemis_mobile/src/app.dart';
import 'package:artemis_mobile/src/core/observability/telemetry.dart';
import 'package:artemis_mobile/src/features/tasks/data/in_memory_task_repository.dart';
import 'package:artemis_mobile/src/features/tasks/domain/task_service.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

void main() {
  testWidgets('task list renders', (tester) async {
    await tester.pumpWidget(const ProviderScope(child: ArtemisApp()));
    await tester.pumpAndSettle();
    expect(find.text('ARTEMIS Tasks'), findsOneWidget);
    expect(find.text('Instrument task sync'), findsOneWidget);
  });

  test('test_task_crud', () async {
    final repo = InMemoryTaskRepository();
    final telemetry = TelemetryRecorder();
    final service = TaskService(repository: repo, telemetry: telemetry);

    final initial = await service.loadTasks();
    final initialCount = initial.length;

    final afterCreate = await service.createTask('CRUD test task');
    expect(afterCreate.length, initialCount + 1);
    expect(afterCreate.last.title, 'CRUD test task');
    expect(afterCreate.last.completed, isFalse);

    final newId = afterCreate.last.id;
    final afterToggle = await service.toggleTask(newId, true);
    final toggled = afterToggle.firstWhere((t) => t.id == newId);
    expect(toggled.completed, isTrue);
  });

  test('test_telemetry_capture', () async {
    final repo = InMemoryTaskRepository();
    final telemetry = TelemetryRecorder();
    final service = TaskService(repository: repo, telemetry: telemetry);

    await service.loadTasks();
    expect(telemetry.spans.any((s) => s.name == 'task.load'), isTrue);

    await service.createTask('Telemetry probe');
    expect(telemetry.spans.any((s) => s.name == 'task.create'), isTrue);
    final createSpan = telemetry.spans.lastWhere((s) => s.name == 'task.create');
    expect(createSpan.attributes['title'], 'Telemetry probe');
  });

  test('test_offline_sync', () async {
    // InMemoryTaskRepository is the offline store — no network required.
    final repo = InMemoryTaskRepository();
    final telemetry = TelemetryRecorder();
    final service = TaskService(repository: repo, telemetry: telemetry);

    final tasks = await service.loadTasks();
    expect(tasks, isNotEmpty);

    final after = await service.createTask('Offline task');
    expect(after.any((t) => t.title == 'Offline task'), isTrue);

    final toggled = await service.toggleTask(after.last.id, true);
    expect(toggled.last.completed, isTrue);
  });
}
