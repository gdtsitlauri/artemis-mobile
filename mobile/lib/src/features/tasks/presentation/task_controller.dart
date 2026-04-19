import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/observability/telemetry.dart';
import '../data/in_memory_task_repository.dart';
import '../data/task_repository.dart';
import '../domain/task.dart';
import '../domain/task_service.dart';

final telemetryProvider = Provider<TelemetryRecorder>((ref) => TelemetryRecorder());
final taskRepositoryProvider = Provider<TaskRepository>((ref) => InMemoryTaskRepository());
final taskServiceProvider = Provider<TaskService>((ref) {
  return TaskService(
    repository: ref.watch(taskRepositoryProvider),
    telemetry: ref.watch(telemetryProvider),
  );
});

class TaskController extends AsyncNotifier<List<Task>> {
  @override
  Future<List<Task>> build() {
    return ref.watch(taskServiceProvider).loadTasks();
  }

  Future<void> createTask(String title) async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(() async {
      return ref.read(taskServiceProvider).createTask(title);
    });
  }

  Future<void> toggleTask(String id, bool completed) async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(() async {
      return ref.read(taskServiceProvider).toggleTask(id, completed);
    });
  }
}

final taskControllerProvider = AsyncNotifierProvider<TaskController, List<Task>>(TaskController.new);
