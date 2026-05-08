import 'package:flutter_test/flutter_test.dart';
import 'package:trend_analysis_app/main.dart';

void main() {
  testWidgets('Trend Analysis app loads successfully', (WidgetTester tester) async {
    await tester.pumpWidget(const TrendAnalysisApp());

    expect(find.text('Trend Analysis'), findsOneWidget);
  });
}