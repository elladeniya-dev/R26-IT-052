import 'package:flutter/material.dart';

class BottomNavTab {
  static const int home = 0;
  static const int search = 1;
  static const int camera = 2;
  static const int saved = 3;
  static const int profile = 4;

  const BottomNavTab._();
}

class CustomBottomNavBar extends StatelessWidget {
  final int selectedIndex;
  final ValueChanged<int> onItemSelected;

  const CustomBottomNavBar({
    super.key,
    required this.selectedIndex,
    required this.onItemSelected,
  });

  static const List<_BottomNavDestination> _destinations = [
    _BottomNavDestination(
      index: BottomNavTab.home,
      icon: Icons.home_outlined,
      label: 'Home',
    ),
    _BottomNavDestination(
      index: BottomNavTab.search,
      icon: Icons.search,
      label: 'Search',
    ),
    _BottomNavDestination(
      index: BottomNavTab.camera,
      icon: Icons.camera_alt,
      label: 'Camera',
    ),
    _BottomNavDestination(
      index: BottomNavTab.saved,
      icon: Icons.favorite_border,
      label: 'Saved outfits',
    ),
    _BottomNavDestination(
      index: BottomNavTab.profile,
      icon: Icons.person,
      label: 'Profile',
    ),
  ];

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      top: false,
      child: Padding(
        padding: const EdgeInsets.fromLTRB(10, 0, 10, 10),
        child: Container(
          height: 58,
          padding: const EdgeInsets.symmetric(horizontal: 18),
          decoration: BoxDecoration(
            color: const Color(0xFFFFF7FF),
            borderRadius: BorderRadius.circular(28),
            boxShadow: [
              BoxShadow(
                color: const Color(0xFF111827).withValues(alpha: 0.08),
                blurRadius: 18,
                offset: const Offset(0, 8),
              ),
            ],
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: _destinations.map((destination) {
              return _BottomNavItem(
                icon: destination.icon,
                label: destination.label,
                isSelected: selectedIndex == destination.index,
                onTap: () {
                  onItemSelected(destination.index);
                },
              );
            }).toList(),
          ),
        ),
      ),
    );
  }
}

class _BottomNavDestination {
  final int index;
  final IconData icon;
  final String label;

  const _BottomNavDestination({
    required this.index,
    required this.icon,
    required this.label,
  });
}

class _BottomNavItem extends StatelessWidget {
  final IconData icon;
  final String label;
  final bool isSelected;
  final VoidCallback onTap;

  const _BottomNavItem({
    required this.icon,
    required this.label,
    required this.isSelected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Tooltip(
      message: label,
      child: GestureDetector(
        onTap: onTap,
        behavior: HitTestBehavior.opaque,
        child: Semantics(
          button: true,
          selected: isSelected,
          label: label,
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 180),
            width: 42,
            height: 42,
            decoration: BoxDecoration(
              color: isSelected ? const Color(0xFFD3E5EC) : Colors.transparent,
              shape: BoxShape.circle,
            ),
            child: Icon(
              icon,
              size: isSelected ? 21 : 24,
              color: const Color(0xFF2F2A3A),
            ),
          ),
        ),
      ),
    );
  }
}
