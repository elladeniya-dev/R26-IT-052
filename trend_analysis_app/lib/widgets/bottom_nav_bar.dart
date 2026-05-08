import 'package:flutter/material.dart';

class TrendBottomNavBar extends StatelessWidget {
  final VoidCallback? onHistoryTap;

  const TrendBottomNavBar({
    super.key,
    this.onHistoryTap,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 76,
      margin: const EdgeInsets.fromLTRB(18, 0, 18, 16),
      decoration: BoxDecoration(
        color: const Color(0xFF00796B),
        borderRadius: BorderRadius.circular(28),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF00796B).withValues(alpha: 0.25),
            blurRadius: 18,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          const BottomNavIcon(icon: Icons.home_rounded, isActive: true),
          GestureDetector(
            onTap: onHistoryTap,
            child: const BottomNavIcon(icon: Icons.history_rounded),
          ),
          const BottomNavIcon(icon: Icons.auto_graph_rounded),
          const BottomNavIcon(icon: Icons.person_outline_rounded),
        ],
      ),
    );
  }
}

class BottomNavIcon extends StatelessWidget {
  final IconData icon;
  final bool isActive;

  const BottomNavIcon({
    super.key,
    required this.icon,
    this.isActive = false,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 44,
      width: 44,
      decoration: BoxDecoration(
        color: isActive ? Colors.white : Colors.transparent,
        shape: BoxShape.circle,
      ),
      child: Icon(
        icon,
        color: isActive ? const Color(0xFF00796B) : Colors.white,
      ),
    );
  }
}