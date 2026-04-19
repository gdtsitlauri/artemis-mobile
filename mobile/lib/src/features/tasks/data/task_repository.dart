import '../domain/task.dart';

abstract class TaskRepository {
  Future<List<Task>> loadTasks();

  Future<List<Task>> createTask(String title);

  Future<List<Task>> toggleTask(String id, bool completed);
}
