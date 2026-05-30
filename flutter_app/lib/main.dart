import 'package:flutter/material.dart';
import 'screens/dashboard_screen.dart';
import 'screens/analysis_screen.dart';
import 'theme/app_theme.dart';

void main() {
  runApp(const FmdCattleApp());
}

class FmdCattleApp extends StatelessWidget {
  const FmdCattleApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'FMD Cattle Analysis System',
      theme: AppTheme.lightTheme,
      routes: {
        '/': (_) => const DashboardScreen(),
        '/analysis': (_) => const AnalysisScreen(),
      },
    );
  }
}
