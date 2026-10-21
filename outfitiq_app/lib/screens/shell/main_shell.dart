import 'package:flutter/foundation.dart' show defaultTargetPlatform, kIsWeb;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../core/theme.dart';
import '../../widgets/app_bottom_nav.dart';
import '../home/home_screen.dart';
import '../outfit/s_saved_outfits_screen.dart';
import '../profile/profile_screen.dart';
import '../trending/trending_screen.dart';

/// Hosts the signed-in app: one navigator per tab, with the navigation next
/// to all of them. Because every screen a tab pushes lives inside that tab's
/// navigator, the navigation stays visible on every screen, each tab keeps its
/// own back stack and scroll position, and switching tabs never stacks
/// duplicate copies of a page.
///
/// Layout adapts to the window: a bottom bar on phone widths, a side rail on
/// wide screens (desktop web, tablets). The shell only caps the overall width;
/// each page decides how to use it (more columns, or its own narrower column).
class MainShell extends StatefulWidget {
  /// Width from which the side rail replaces the bottom bar.
  static const double wideBreakpoint = 900;

  /// Widest the page area grows. Beyond this the pages stay centered.
  static const double maxContentWidth = 1400;

  /// Page builders per tab. Only overridden in tests.
  final Map<AppTab, WidgetBuilder>? pages;

  const MainShell({super.key, this.pages});

  @override
  State<MainShell> createState() => _MainShellState();
}

class _MainShellState extends State<MainShell> {
  static const List<AppTab> _pageTabs = [
    AppTab.home,
    AppTab.trending,
    AppTab.saved,
    AppTab.profile,
  ];

  late final Map<AppTab, WidgetBuilder> _pages =
      widget.pages ??
      {
        AppTab.home: (_) => const HomeScreen(),
        AppTab.trending: (_) => const TrendingScreen(),
        AppTab.saved: (_) => _savedPage,
        AppTab.profile: (_) => const ProfileScreen(),
      };

  final Map<AppTab, GlobalKey<NavigatorState>> _navigatorKeys = {
    for (final AppTab tab in _pageTabs) tab: GlobalKey<NavigatorState>(),
  };

  // Tabs are built on first visit so Trending and Profile don't fetch data
  // before the user opens them.
  final Set<AppTab> _opened = {AppTab.home};

  // Outfits can be saved from other tabs; the Saved tab reloads when shown.
  final ValueNotifier<int> _savedRefresh = ValueNotifier<int>(0);
  late final Widget _savedPage = SavedOutfitsScreen(refresh: _savedRefresh);

  AppTab _current = AppTab.home;

  void _select(AppTab tab) {
    if (tab == AppTab.saved) {
      _savedRefresh.value++;
    }

    if (tab == _current) {
      // Tapping the active tab returns to its first page.
      _navigatorKeys[tab]?.currentState?.popUntil((route) => route.isFirst);
      return;
    }

    setState(() {
      _current = tab;
      _opened.add(tab);
    });
  }

  // The system Back (Android button/gesture, browser Back) goes one step up:
  // a pushed page closes, then a non-Home tab returns to Home, and only then
  // does Back reach the app itself.
  Future<void> _handleBack() async {
    final NavigatorState? navigator = _navigatorKeys[_current]?.currentState;

    if (navigator != null && navigator.canPop()) {
      // maybePop, not pop: a page that blocks Back (PopScope) is respected.
      await navigator.maybePop();
      return;
    }

    if (_current != AppTab.home) {
      setState(() {
        _current = AppTab.home;
      });
      return;
    }

    _backFromHome();
  }

  DateTime? _lastBackFromHome;

  void _backFromHome() {
    // Only Android has an "exit the app" Back. On the web, SystemNavigator.pop
    // sends the browser away from the app, and iOS has no Back at all.
    if (kIsWeb || defaultTargetPlatform != TargetPlatform.android) return;

    final DateTime now = DateTime.now();
    final DateTime? last = _lastBackFromHome;

    if (last != null && now.difference(last) < _exitConfirmWindow) {
      SystemNavigator.pop();
      return;
    }

    _lastBackFromHome = now;
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(
        const SnackBar(
          content: Text('Press back again to exit'),
          duration: _exitConfirmWindow,
        ),
      );
  }

  static const Duration _exitConfirmWindow = Duration(seconds: 2);

  @override
  void dispose() {
    _savedRefresh.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final bool wide =
        MediaQuery.sizeOf(context).width >= MainShell.wideBreakpoint;
    final Widget content = Center(
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: MainShell.maxContentWidth),
        child: IndexedStack(
          index: _pageTabs.indexOf(_current),
          children: [
            for (final AppTab tab in _pageTabs)
              _opened.contains(tab)
                  ? Navigator(
                      key: _navigatorKeys[tab],
                      onGenerateRoute: (settings) => MaterialPageRoute(
                        settings: settings,
                        builder: _pages[tab]!,
                      ),
                    )
                  : const SizedBox.shrink(),
          ],
        ),
      ),
    );

    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, result) {
        if (!didPop) {
          _handleBack();
        }
      },
      child: Scaffold(
        backgroundColor: AppTheme.backgroundColor,
        // Each tab's own Scaffold handles the keyboard.
        resizeToAvoidBottomInset: false,
        body: _BottomPaddingRemover(
          remove: !wide,
          child: wide
              ? Row(
                  children: [
                    AppSideNav(currentTab: _current, onSelect: _select),
                    Expanded(child: content),
                  ],
                )
              : content,
        ),
        bottomNavigationBar: wide
            ? null
            : _HideWhenKeyboardOpen(
                child: AppBottomNav(currentTab: _current, onSelect: _select),
              ),
      ),
    );
  }
}

/// Hides the bottom bar while the keyboard is open. It listens to the
/// keyboard itself so only this widget rebuilds on each animation frame,
/// not the whole shell and every page in it.
class _HideWhenKeyboardOpen extends StatelessWidget {
  final Widget child;

  const _HideWhenKeyboardOpen({required this.child});

  @override
  Widget build(BuildContext context) {
    return MediaQuery.viewInsetsOf(context).bottom > 0
        ? const SizedBox.shrink()
        : child;
  }
}

/// Tells pages not to pad for the bottom safe area, because the bottom bar
/// already does. Kept as its own widget for the same reason as above.
class _BottomPaddingRemover extends StatelessWidget {
  final bool remove;
  final Widget child;

  const _BottomPaddingRemover({required this.remove, required this.child});

  @override
  Widget build(BuildContext context) {
    return remove
        ? MediaQuery.removePadding(
            context: context,
            removeBottom: true,
            child: child,
          )
        : child;
  }
}
