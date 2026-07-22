// This is a basic Flutter widget test.
//
// To perform an interaction with a widget in your test, use the WidgetTester
// utility in the flutter_test package. For example, you can send tap and scroll
// gestures. You can also use WidgetTester to find child widgets in the widget
// tree, read text, and verify that the values of widget properties are correct.

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:senu_outfit_frontend/main.dart';
import 'package:senu_outfit_frontend/widgets/custom_bottom_nav_bar.dart';

void main() {
  testWidgets('App loads product list screen', (WidgetTester tester) async {
    await tester.pumpWidget(const SenuOutfitApp());

    expect(find.text('OutfitIQ'), findsOneWidget);
    expect(find.text('Find your best outfit'), findsOneWidget);
    expect(find.text('Explore styles'), findsOneWidget);

    final mainScrollView = find.byType(Scrollable).first;

    await tester.scrollUntilVisible(
      find.text('Flash Sale'),
      300,
      scrollable: mainScrollView,
    );
    expect(find.text('Flash Sale'), findsOneWidget);
  });

  testWidgets('Custom bottom nav reports selected tab taps', (
    WidgetTester tester,
  ) async {
    int selectedIndex = BottomNavTab.home;

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          bottomNavigationBar: StatefulBuilder(
            builder: (context, setState) {
              return CustomBottomNavBar(
                selectedIndex: selectedIndex,
                onItemSelected: (index) {
                  setState(() {
                    selectedIndex = index;
                  });
                },
              );
            },
          ),
        ),
      ),
    );

    expect(selectedIndex, BottomNavTab.home);

    await tester.tap(find.byIcon(Icons.favorite_border));
    await tester.pumpAndSettle();

    expect(selectedIndex, BottomNavTab.saved);
  });
}
