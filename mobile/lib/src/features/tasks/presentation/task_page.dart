import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'task_controller.dart';

class TaskPage extends ConsumerWidget {
  const TaskPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final tasksAsync = ref.watch(taskControllerProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('ARTEMIS Tasks')),
      body: tasksAsync.when(
        data: (tasks) => ListView(
          children: [
            for (final task in tasks)
              CheckboxListTile(
                title: Text(task.title),
                subtitle: Text(task.description),
                value: task.completed,
                onChanged: (value) {
                  ref.read(taskControllerProvider.notifier).toggleTask(
                    task.id,
                    value ?? false,
                  );
                },
              ),
          ],
        ),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, stackTrace) => Center(
          child: Text('Failed to load tasks: $error'),
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          ref.read(taskControllerProvider.notifier).createTask('New telemetry-aware task');
        },
        child: const Icon(Icons.add),
      ),
    );
  }
}
