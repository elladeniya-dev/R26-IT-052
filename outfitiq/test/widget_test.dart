import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('OutfitIQ test app loads', (WidgetTester tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(
          body: Center(
            child: Text('OutfitIQ'),
          ),
        ),
      ),
    );

    expect(find.text('OutfitIQ'), findsOneWidget);
  });
}