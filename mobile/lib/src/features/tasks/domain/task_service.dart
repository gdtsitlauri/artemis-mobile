import '../../../core/observability/telemetry.dart';
import '../data/task_repository.dart';
import 'task.dart';

class TaskService {
  TaskService({required TaskRepository repository, required TelemetryRecorder telemetry})
    : _repository = repository,
      _telemetry = telemetry;

  final TaskRepository _repository;
  final TelemetryRecorder _telemetry;

  Future<List<Task>> loadTasks() async {
    _telemetry.record('task.load');
    return _repository.loadTasks();
  }

  Future<List<Task>> createTask(String title) async {
    _telemetry.record('task.create', attributes: <String, Object?>{'title': title});
    return _repository.createTask(title);
  }

  Future<List<Task>> toggleTask(String id, bool completed) async {
    _telemetry.record(
      'task.toggle',
      attributes: <String, Object?>{'task_id': id, 'completed': completed},
    );
    return _repository.toggleTask(id, completed);
  }
}
