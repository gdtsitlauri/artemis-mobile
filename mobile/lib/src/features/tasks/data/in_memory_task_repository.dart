import 'package:uuid/uuid.dart';

import '../domain/task.dart';
import 'task_repository.dart';

class InMemoryTaskRepository implements TaskRepository {
  InMemoryTaskRepository()
    : _tasks = <Task>[
        const Task(
          id: '1',
          title: 'Instrument task sync',
          completed: false,
          description: 'Capture spans for every sync edge.',
        ),
        const Task(
          id: '2',
          title: 'Review GUARDIAN alert',
          completed: true,
          description: 'Validate predictive alert explanation.',
        ),
      ];

  final List<Task> _tasks;
  final Uuid _uuid = const Uuid();

  @override
  Future<List<Task>> loadTasks() async {
    return List<Task>.unmodifiable(_tasks);
  }

  @override
  Future<List<Task>> createTask(String title) async {
    _tasks.add(
      Task(
        id: _uuid.v4(),
        title: title,
        description: 'Created locally and queued for sync.',
        completed: false,
      ),
    );
    return List<Task>.unmodifiable(_tasks);
  }

  @override
  Future<List<Task>> toggleTask(String id, bool completed) async {
    final index = _tasks.indexWhere((task) => task.id == id);
    if (index >= 0) {
      _tasks[index] = _tasks[index].copyWith(completed: completed);
    }
    return List<Task>.unmodifiable(_tasks);
  }
}
