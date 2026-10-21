import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:outfitiq_app/screens/shell/main_shell.dart';
import 'package:outfitiq_app/widgets/app_bottom_nav.dart';

void main() {
  int trendingBuilds = 0;

  Widget app() {
    trendingBuilds = 0;
    return MaterialApp(
      home: MainShell(
        pages: {
          AppTab.home: (context) => Scaffold(
                body: Column(
                  children: [
                    const Text('HOME PAGE'),
                    TextButton(
                      onPressed: () => Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (_) =>
                              const Scaffold(body: Text('DETAIL PAGE')),
                        ),
                      ),
                      child: const Text('open detail'),
                    ),
                  ],
                ),
              ),
          AppTab.trending: (context) {
            trendingBuilds++;
            return const Scaffold(body: Text('TRENDING PAGE'));
          },
          AppTab.saved: (context) => const Scaffold(body: Text('SAVED PAGE')),
          AppTab.profile: (context) =>
              const Scaffold(body: Text('PROFILE PAGE')),
        },
      ),
    );
  }

  testWidgets('nav bar shows on the first page and on pushed pages',
      (tester) async {
    await tester.pumpWidget(app());
    await tester.pumpAndSettle();

    expect(find.text('HOME PAGE'), findsOneWidget);
    for (final label in ['Home', 'Trending', 'Saved', 'Profile']) {
      expect(find.text(label), findsOneWidget);
    }

    await tester.tap(find.text('open detail'));
    await tester.pumpAndSettle();

    expect(find.text('DETAIL PAGE'), findsOneWidget);
    expect(find.byType(AppBottomNav), findsOneWidget);
  });

  testWidgets('tabs keep their own stack and build lazily', (tester) async {
    await tester.pumpWidget(app());
    await tester.pumpAndSettle();
    expect(trendingBuilds, 0);

    await tester.tap(find.text('open detail'));
    await tester.pumpAndSettle();

    await tester.tap(find.text('Trending'));
    await tester.pumpAndSettle();
    expect(find.text('TRENDING PAGE'), findsOneWidget);
    // Built on first visit (it may rebuild later; its state is kept).
    expect(trendingBuilds, greaterThan(0));

    // Back on Home, the detail page is still open.
    await tester.tap(find.text('Home'));
    await tester.pumpAndSettle();
    expect(find.text('DETAIL PAGE'), findsOneWidget);

    // Tapping the active tab returns to its first page.
    await tester.tap(find.text('Home'));
    await tester.pumpAndSettle();
    expect(find.text('HOME PAGE'), findsOneWidget);
    expect(find.text('DETAIL PAGE'), findsNothing);
  });

  testWidgets('saved tab opens its page and there is no bag tab',
      (tester) async {
    await tester.pumpWidget(app());
    await tester.pumpAndSettle();

    expect(find.text('Bag'), findsNothing);

    await tester.tap(find.text('Saved'));
    await tester.pumpAndSettle();

    expect(find.text('SAVED PAGE'), findsOneWidget);
  });

  testWidgets('system back pops the page, then returns to Home',
      (tester) async {
    await tester.pumpWidget(app());
    await tester.pumpAndSettle();

    await tester.tap(find.text('Profile'));
    await tester.pumpAndSettle();
    expect(find.text('PROFILE PAGE'), findsOneWidget);

    await tester.binding.handlePopRoute();
    await tester.pumpAndSettle();
    expect(find.text('HOME PAGE'), findsOneWidget);
  });

  testWidgets('wide screens get a side rail and content capped at 1400',
      (tester) async {
    tester.view.physicalSize = const Size(1800, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);

    await tester.pumpWidget(
      MaterialApp(
        home: MainShell(
          pages: {
            AppTab.home: (context) => Scaffold(
                  body: Column(
                    children: [
                      const SizedBox(
                        key: Key('root-page'),
                        width: double.infinity,
                        height: 20,
                      ),
                      TextButton(
                        onPressed: () => Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (_) => const Scaffold(
                              body: SizedBox(
                                key: Key('pushed-page'),
                                width: double.infinity,
                                height: 20,
                              ),
                            ),
                          ),
                        ),
                        child: const Text('open'),
                      ),
                    ],
                  ),
                ),
            AppTab.trending: (context) => const Scaffold(),
            AppTab.saved: (context) => const Scaffold(),
            AppTab.profile: (context) => const Scaffold(),
          },
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.byType(AppSideNav), findsOneWidget);
    expect(find.byType(AppBottomNav), findsNothing);
    expect(tester.getSize(find.byKey(const Key('root-page'))).width, 1400);

    await tester.tap(find.text('open'));
    await tester.pumpAndSettle();

    // Pushed pages get the same canvas (each page narrows itself if it
    // needs to), and the rail stays.
    expect(tester.getSize(find.byKey(const Key('pushed-page'))).width, 1400);
    expect(find.byType(AppSideNav), findsOneWidget);
  });

  testWidgets('keyboard hides the nav bar without rebuilding the pages',
      (tester) async {
    var homeBuilds = 0;

    await tester.pumpWidget(
      MaterialApp(
        home: MainShell(
          pages: {
            AppTab.home: (context) {
              homeBuilds++;
              return const Scaffold(body: Text('HOME PAGE'));
            },
            AppTab.trending: (context) => const Scaffold(),
            AppTab.saved: (context) => const Scaffold(),
            AppTab.profile: (context) => const Scaffold(),
          },
        ),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.byType(AppBottomNav), findsOneWidget);
    final int buildsBefore = homeBuilds;

    // The keyboard opens: insets change on every animation frame.
    tester.view.viewInsets = const FakeViewPadding(bottom: 600);
    addTearDown(tester.view.resetViewInsets);
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 16));

    expect(find.byType(AppBottomNav), findsNothing);
    expect(homeBuilds, buildsBefore, reason: 'pages must not rebuild per frame');
  });

  testWidgets('back at Home asks once, then exits on the second press (Android)',
      (tester) async {
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

    await tester.pumpWidget(app());
    await tester.pumpAndSettle();

    await tester.binding.handlePopRoute();
    await tester.pump();
    expect(find.text('Press back again to exit'), findsOneWidget);
    expect(platformCalls, isNot(contains('SystemNavigator.pop')));

    await tester.binding.handlePopRoute();
    await tester.pump();
    expect(platformCalls, contains('SystemNavigator.pop'));
  });

  testWidgets('a page that blocks Back is not popped by the system Back',
      (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: MainShell(
          pages: {
            AppTab.home: (context) => Scaffold(
                  body: TextButton(
                    onPressed: () => Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (_) => const PopScope(
                          canPop: false,
                          child: Scaffold(body: Text('LOCKED PAGE')),
                        ),
                      ),
                    ),
                    child: const Text('open locked'),
                  ),
                ),
            AppTab.trending: (context) => const Scaffold(),
            AppTab.saved: (context) => const Scaffold(),
            AppTab.profile: (context) => const Scaffold(),
          },
        ),
      ),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.text('open locked'));
    await tester.pumpAndSettle();
    expect(find.text('LOCKED PAGE'), findsOneWidget);

    await tester.binding.handlePopRoute();
    await tester.pumpAndSettle();
    expect(find.text('LOCKED PAGE'), findsOneWidget);
  });
}
