import 'package:flutter/material.dart';

import 's_notifications_screen.dart';

class NotificationDetailScreen extends StatelessWidget {
  final AppNotification notification;

  const NotificationDetailScreen({super.key, required this.notification});

  static const _blue = Color(0xFF0B5D85);
  static const _blueLight = Color(0xFF5AB4D6);

  IconData _categoryIcon(String cat) {
    switch (cat) {
      case 'outfit':
        return Icons.checkroom_rounded;
      case 'sale':
        return Icons.local_offer_rounded;
      case 'tip':
        return Icons.lightbulb_rounded;
      case 'system':
        return Icons.settings_rounded;
      default:
        return Icons.notifications_rounded;
    }
  }

  Color _categoryColor(String cat) {
    switch (cat) {
      case 'outfit':
        return _blue;
      case 'sale':
        return const Color(0xFFE85D04);
      case 'tip':
        return const Color(0xFF059669);
      case 'system':
        return const Color(0xFF6B7280);
      default:
        return _blueLight;
    }
  }

  String _categoryLabel(String cat) {
    switch (cat) {
      case 'outfit':
        return 'Outfit Update';
      case 'sale':
        return 'Sale & Offers';
      case 'tip':
        return 'Style Tip';
      case 'system':
        return 'System';
      default:
        return 'Notification';
    }
  }

  String _fullTime(DateTime time) {
    final hour = time.hour % 12 == 0 ? 12 : time.hour % 12;
    final min = time.minute.toString().padLeft(2, '0');
    final ampm = time.hour < 12 ? 'AM' : 'PM';
    final day = time.day.toString().padLeft(2, '0');
    final months = [
      'Jan',
      'Feb',
      'Mar',
      'Apr',
      'May',
      'Jun',
      'Jul',
      'Aug',
      'Sep',
      'Oct',
      'Nov',
      'Dec',
    ];
    return '${months[time.month - 1]} $day, ${time.year}  $hour:$min $ampm';
  }

  @override
  Widget build(BuildContext context) {
    final catColor = _categoryColor(notification.category);
    final safePad = MediaQuery.paddingOf(context);

    return Scaffold(
      backgroundColor: const Color(0xFFF8F8F8),
      body: Column(
        children: [
          // ── App bar ────────────────────────────────────────
          Container(
            color: Colors.white,
            padding: EdgeInsets.only(
              top: safePad.top + 6,
              left: 4,
              right: 16,
              bottom: 12,
            ),
            child: Row(
              children: [
                IconButton(
                  icon:
                      const Icon(Icons.arrow_back_ios_new, size: 20),
                  color: const Color(0xFF111827),
                  onPressed: () => Navigator.pop(context),
                ),
                const Expanded(
                  child: Text(
                    'Notification Details',
                    style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.w900,
                      color: Color(0xFF111827),
                    ),
                  ),
                ),
              ],
            ),
          ),

          const Divider(height: 1, thickness: 0.5, color: Color(0xFFE5E7EB)),

          // ── Content ────────────────────────────────────────
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(18),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // ── Category badge + timestamp row ──────────
                  Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 12, vertical: 6),
                        decoration: BoxDecoration(
                          color: catColor.withValues(alpha: 0.10),
                          borderRadius: BorderRadius.circular(20),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(
                              _categoryIcon(notification.category),
                              size: 14,
                              color: catColor,
                            ),
                            const SizedBox(width: 6),
                            Text(
                              _categoryLabel(notification.category),
                              style: TextStyle(
                                fontSize: 12,
                                fontWeight: FontWeight.w700,
                                color: catColor,
                              ),
                            ),
                          ],
                        ),
                      ),
                      const Spacer(),
                      Text(
                        _fullTime(notification.time),
                        style: const TextStyle(
                          fontSize: 12,
                          color: Color(0xFF9CA3AF),
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ],
                  ),

                  const SizedBox(height: 22),

                  // ── Large icon ──────────────────────────────
                  Center(
                    child: Container(
                      width: 80,
                      height: 80,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: catColor.withValues(alpha: 0.12),
                        border: Border.all(
                          color: catColor.withValues(alpha: 0.25),
                          width: 2,
                        ),
                      ),
                      child: Icon(
                        _categoryIcon(notification.category),
                        size: 38,
                        color: catColor,
                      ),
                    ),
                  ),

                  const SizedBox(height: 22),

                  // ── Title ───────────────────────────────────
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(18),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(20),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withValues(alpha: 0.05),
                          blurRadius: 12,
                          offset: const Offset(0, 4),
                        ),
                      ],
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'TITLE',
                          style: TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w700,
                            color: Color(0xFF9CA3AF),
                            letterSpacing: 1.2,
                          ),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          notification.title,
                          style: const TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.w900,
                            color: Color(0xFF111827),
                            height: 1.3,
                          ),
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 14),

                  // ── Body ────────────────────────────────────
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(18),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(20),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withValues(alpha: 0.05),
                          blurRadius: 12,
                          offset: const Offset(0, 4),
                        ),
                      ],
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'MESSAGE',
                          style: TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w700,
                            color: Color(0xFF9CA3AF),
                            letterSpacing: 1.2,
                          ),
                        ),
                        const SizedBox(height: 10),
                        Text(
                          notification.body,
                          style: const TextStyle(
                            fontSize: 15,
                            color: Color(0xFF374151),
                            height: 1.65,
                            fontWeight: FontWeight.w400,
                          ),
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 28),

                  // ── Action button ───────────────────────────
                  if (notification.category == 'outfit' ||
                      notification.category == 'sale')
                    SizedBox(
                      width: double.infinity,
                      height: 52,
                      child: ElevatedButton.icon(
                        onPressed: () {
                          Navigator.popUntil(
                              context, (route) => route.isFirst);
                        },
                        icon: Icon(
                          notification.category == 'outfit'
                              ? Icons.checkroom_rounded
                              : Icons.shopping_bag_rounded,
                          size: 20,
                        ),
                        label: Text(
                          notification.category == 'outfit'
                              ? 'View Outfit'
                              : 'Shop Now',
                          style: const TextStyle(
                            fontSize: 15,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: _blue,
                          foregroundColor: Colors.white,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(16),
                          ),
                          elevation: 0,
                        ),
                      ),
                    ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
