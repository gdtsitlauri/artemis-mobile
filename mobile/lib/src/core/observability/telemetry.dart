class TelemetrySpan {
  const TelemetrySpan({
    required this.name,
    required this.startedAt,
    required this.attributes,
  });

  final String name;
  final DateTime startedAt;
  final Map<String, Object?> attributes;
}

class TelemetryRecorder {
  final List<TelemetrySpan> _spans = <TelemetrySpan>[];

  List<TelemetrySpan> get spans => List<TelemetrySpan>.unmodifiable(_spans);

  void record(String name, {Map<String, Object?> attributes = const {}}) {
    _spans.add(
      TelemetrySpan(
        name: name,
        startedAt: DateTime.now().toUtc(),
        attributes: attributes,
      ),
    );
  }
}
