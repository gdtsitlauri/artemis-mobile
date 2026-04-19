import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import 'features/tasks/presentation/task_page.dart';

class ArtemisApp extends StatelessWidget {
  const ArtemisApp({super.key});

  @override
  Widget build(BuildContext context) {
    final router = GoRouter(
      routes: [
        GoRoute(
          path: '/',
          builder: (context, state) => const TaskPage(),
        ),
      ],
    );

    return MaterialApp.router(
      title: 'ARTEMIS',
      theme: ThemeData.light(useMaterial3: true),
      darkTheme: ThemeData.dark(useMaterial3: true),
      routerConfig: router,
    );
  }
}
