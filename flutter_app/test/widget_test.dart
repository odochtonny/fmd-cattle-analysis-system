import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:fmd_cattle_analysis_system/main.dart';

void main() {
  testWidgets(
    'FMD Cattle Analysis System loads successfully',
    (WidgetTester tester) async {
      // Build the app
      await tester.pumpWidget(const FmdCattleApp());

      // Allow widgets and async operations to complete
      await tester.pumpAndSettle();

      // Verify MaterialApp loads
      expect(find.byType(MaterialApp), findsOneWidget);

      // Verify app title text exists somewhere in the UI (optional)
      expect(find.byType(Scaffold), findsWidgets);
    },
  );
}
