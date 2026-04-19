class Task {
  const Task({
    required this.id,
    required this.title,
    required this.completed,
    this.description = '',
  });

  final String id;
  final String title;
  final bool completed;
  final String description;

  Task copyWith({String? id, String? title, bool? completed, String? description}) {
    return Task(
      id: id ?? this.id,
      title: title ?? this.title,
      completed: completed ?? this.completed,
      description: description ?? this.description,
    );
  }
}
