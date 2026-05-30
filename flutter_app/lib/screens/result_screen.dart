import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../widgets/professional_shell.dart';

class ResultScreen extends StatelessWidget {
  final Map<String, dynamic> result;
  const ResultScreen({super.key, required this.result});

  @override
  Widget build(BuildContext context) {
    final analysis = result['result'] ?? {};
    final prediction = analysis['final_prediction'] ?? analysis['status'] ?? 'Unknown';
    final severity = analysis['severity'] ?? 'N/A';
    final confidence = analysis['final_confidence'] ?? analysis['confidence'] ?? 0;
    final treatment = analysis['treatment_recommendation'] ?? analysis['recommendation'] ?? 'No treatment recommendation returned.';

    return ProfessionalShell(
      title: 'Analysis Result',
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Card(child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Row(children: [
                CircleAvatar(radius: 30, backgroundColor: AppTheme.primary.withOpacity(.1), child: const Icon(Icons.health_and_safety, color: AppTheme.primary, size: 32)),
                const SizedBox(width: 16),
                Expanded(child: Text(prediction.toString(), style: Theme.of(context).textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.w900))),
              ]),
              const SizedBox(height: 16),
              _row('Severity', severity.toString()),
              _row('Confidence', confidence is num ? '${(confidence * 100).toStringAsFixed(1)}%' : confidence.toString()),
              _row('MongoDB Record ID', result['record_id']?.toString() ?? 'N/A'),
              _row('Image ID', result['image_id']?.toString() ?? 'N/A'),
            ]),
          )),
          const SizedBox(height: 18),
          Card(child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              const Text('Treatment / Control Recommendation', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800)),
              const SizedBox(height: 10),
              Text(treatment.toString(), style: const TextStyle(height: 1.5)),
            ]),
          )),
          const SizedBox(height: 18),
          FilledButton.icon(onPressed: () => Navigator.pushNamedAndRemoveUntil(context, '/', (_) => false), icon: const Icon(Icons.dashboard_outlined), label: const Text('Back to Dashboard')),
        ]),
      ),
    );
  }

  Widget _row(String label, String value) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 6),
    child: Row(children: [SizedBox(width: 160, child: Text(label, style: const TextStyle(fontWeight: FontWeight.w700))), Expanded(child: Text(value))]),
  );
}
