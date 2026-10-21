import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:outfitiq_app/core/support_info.dart';
import 'package:outfitiq_app/screens/profile/help_center_screen.dart';

void main() {
  Future<void> open(WidgetTester tester) async {
    tester.view.physicalSize = const Size(800, 2400);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    await tester.pumpWidget(const MaterialApp(home: HelpCenterScreen()));
    await tester.pumpAndSettle();
  }

  testWidgets('shows tips, questions and the support email', (tester) async {
    await open(tester);

    expect(find.text('Help Center'), findsOneWidget);
    expect(find.text('Quick tips'), findsOneWidget);
    expect(find.text('Common questions'), findsOneWidget);
    expect(find.text('How does OutfitIQ choose my recommendations?'),
        findsOneWidget);

    await tester.scrollUntilVisible(
      find.text('Email support'),
      300,
      scrollable: find.byType(Scrollable).first,
    );
    expect(find.text(SupportInfo.email), findsOneWidget);
    expect(find.text('Email support'), findsOneWidget);
  });

  testWidgets('a question expands to show its answer', (tester) async {
    await open(tester);

    const answerStart = 'Each product gets a match score';
    expect(find.textContaining(answerStart), findsNothing);

    await tester.tap(find.text('How does OutfitIQ choose my recommendations?'));
    await tester.pumpAndSettle();

    expect(find.textContaining(answerStart), findsOneWidget);
  });

  testWidgets('copy button confirms the address was copied', (tester) async {
    final List<String> platformCalls = [];
    tester.binding.defaultBinaryMessenger.setMockMethodCallHandler(
      SystemChannels.platform,
      (call) async {
        platformCalls.add(call.method);
        return null;
      },
    );
    addTearDown(
      () => tester.binding.defaultBinaryMessenger
          .setMockMethodCallHandler(SystemChannels.platform, null),
    );
    await open(tester);

    await tester.scrollUntilVisible(
      find.byTooltip('Copy email address'),
      300,
      scrollable: find.byType(Scrollable).first,
    );
    await tester.tap(find.byTooltip('Copy email address'));
    // the clipboard call is async; let it finish, then let the snack bar appear
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 300));

    expect(platformCalls, contains('Clipboard.setData'));
    expect(find.text('Email address copied.'), findsOneWidget);
  });

  testWidgets('a failing clipboard still shows the address', (tester) async {
    tester.binding.defaultBinaryMessenger.setMockMethodCallHandler(
      SystemChannels.platform,
      (call) async {
        if (call.method == 'Clipboard.setData') {
          throw PlatformException(code: 'unavailable');
        }
        return null;
      },
    );
    addTearDown(
      () => tester.binding.defaultBinaryMessenger
          .setMockMethodCallHandler(SystemChannels.platform, null),
    );
    await open(tester);

    await tester.scrollUntilVisible(
      find.byTooltip('Copy email address'),
      300,
      scrollable: find.byType(Scrollable).first,
    );
    await tester.tap(find.byTooltip('Copy email address'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 300));

    expect(find.text('Email us at ${SupportInfo.email}'), findsOneWidget);
  });
}
