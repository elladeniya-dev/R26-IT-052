import 'package:flutter/material.dart';

import '../core/theme.dart';

/// The app's top-level sections.
enum AppTab { home, trending, saved, profile }

const List<({AppTab tab, IconData icon, String label})> _navTabs = [
  (tab: AppTab.home, icon: Icons.home_rounded, label: 'Home'),
  (tab: AppTab.trending, icon: Icons.trending_up_rounded, label: 'Trending'),
  (tab: AppTab.saved, icon: Icons.favorite_border_rounded, label: 'Saved'),
  (tab: AppTab.profile, icon: Icons.person_outline_rounded, label: 'Profile'),
];

/// One tab button: icon over label, tinted when active.
class _NavItem extends StatelessWidget {
  final IconData icon;
  final String label;
  final bool isActive;
  final VoidCallback onTap;

  const _NavItem({
    required this.icon,
    required this.label,
    required this.isActive,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final Color color =
        isActive ? AppTheme.primaryColor : AppTheme.inactiveColor;

    return Semantics(
      button: true,
      selected: isActive,
      label: label,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(22),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, color: color, size: 24),
            const SizedBox(height: 3),
            Text(
              label,
              style: TextStyle(
                fontSize: 11,
                fontWeight: isActive ? FontWeight.w600 : FontWeight.w500,
                color: color,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// Bottom navigation for phone-width screens. It only reports taps;
/// [MainShell] decides what a tap does.
class AppBottomNav extends StatelessWidget {
  final AppTab currentTab;
  final ValueChanged<AppTab> onSelect;

  const AppBottomNav({
    super.key,
    required this.currentTab,
    required this.onSelect,
  });

  static const double maxWidth = 520;

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      top: false,
      // heightFactor: without it Center fills all the height it is given.
      child: Center(
        heightFactor: 1,
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: maxWidth),
          child: Container(
            height: 68,
            margin: const EdgeInsets.fromLTRB(16, 0, 16, 12),
            padding: const EdgeInsets.symmetric(horizontal: 8),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(28),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withValues(alpha: 0.08),
                  blurRadius: 20,
                  offset: const Offset(0, 6),
                ),
              ],
            ),
            child: Row(
              children: [
                for (final item in _navTabs)
                  Expanded(
                    child: _NavItem(
                      icon: item.icon,
                      label: item.label,
                      isActive: item.tab == currentTab,
                      onTap: () => onSelect(item.tab),
                    ),
                  ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

/// Side rail for wide screens (desktop web, tablets): same tabs as
/// [AppBottomNav], stacked vertically.
class AppSideNav extends StatelessWidget {
  final AppTab currentTab;
  final ValueChanged<AppTab> onSelect;

  const AppSideNav({
    super.key,
    required this.currentTab,
    required this.onSelect,
  });

  static const double width = 96;

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Container(
        width: width,
        margin: const EdgeInsets.fromLTRB(16, 16, 0, 16),
        padding: const EdgeInsets.symmetric(vertical: 18, horizontal: 8),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(28),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.06),
              blurRadius: 20,
              offset: const Offset(0, 6),
            ),
          ],
        ),
        child: Column(
          children: [
            Container(
              height: 42,
              width: 42,
              decoration: BoxDecoration(
                color: AppTheme.primaryColor,
                borderRadius: BorderRadius.circular(14),
              ),
              child: const Icon(
                Icons.auto_awesome_rounded,
                color: Colors.white,
                size: 22,
              ),
            ),
            const SizedBox(height: 24),
            for (final item in _navTabs)
              SizedBox(
                height: 68,
                width: double.infinity,
                child: _NavItem(
                  icon: item.icon,
                  label: item.label,
                  isActive: item.tab == currentTab,
                  onTap: () => onSelect(item.tab),
                ),
              ),
          ],
        ),
      ),
    );
  }
}
