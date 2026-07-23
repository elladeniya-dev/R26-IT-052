import 'package:flutter/material.dart';

import 'notification_detail_screen.dart';

/// A single notification data model
class AppNotification {
  final String id;
  final String title;
  final String body;
  final String category; // 'outfit', 'sale', 'tip', 'system'
  final DateTime time;
  bool isRead;

  AppNotification({
    required this.id,
    required this.title,
    required this.body,
    required this.category,
    required this.time,
    this.isRead = false,
  });
}

class NotificationsScreen extends StatefulWidget {
  const NotificationsScreen({super.key});

  @override
  State<NotificationsScreen> createState() => _NotificationsScreenState();
}

class _NotificationsScreenState extends State<NotificationsScreen> {
  static const _blue = Color(0xFF0B5D85);
  static const _blueLight = Color(0xFF5AB4D6);

  // Sample notification data
  final List<AppNotification> _notifications = [
    AppNotification(
      id: 'N001',
      title: '🎉 New Outfit Suggestion Ready!',
      body:
          'We generated 5 compatible outfit combinations for your Black Casual Crop Top. Tap to explore them now.',
      category: 'outfit',
      time: DateTime.now().subtract(const Duration(minutes: 12)),
      isRead: false,
    ),
    AppNotification(
      id: 'N002',
      title: '🔥 Flash Sale — Up to 40% Off',
      body:
          'Kelly Felder denim jeans and Fashion Bug blazers are now on sale. Limited stock available. Shop before it\'s gone!',
      category: 'sale',
      time: DateTime.now().subtract(const Duration(hours: 1, minutes: 30)),
      isRead: false,
    ),
    AppNotification(
      id: 'N003',
      title: '💡 Style Tip of the Day',
      body:
          'Pair a white jacket with navy or black bottoms for an effortlessly clean, modern look that works for both casual and smart-casual occasions.',
      category: 'tip',
      time: DateTime.now().subtract(const Duration(hours: 5)),
      isRead: true,
    ),
    AppNotification(
      id: 'N004',
      title: '✅ Outfit Saved Successfully',
      body:
          'Your outfit "Casual Blue Look" has been saved to your collection. You can re-use it anytime from the Saved Outfits tab.',
      category: 'outfit',
      time: DateTime.now().subtract(const Duration(hours: 9)),
      isRead: true,
    ),
    AppNotification(
      id: 'N005',
      title: '🛍️ New Arrivals from Gflock',
      body:
          'Gflock just added 12 new casual tops and summer jackets. Check them out and generate a compatible outfit suggestion.',
      category: 'sale',
      time: DateTime.now().subtract(const Duration(days: 1)),
      isRead: true,
    ),
    AppNotification(
      id: 'N006',
      title: '⚙️ App Updated to v2.1',
      body:
          'OutfitIQ has been updated. New features include improved outfit compatibility scoring and a redesigned search experience.',
      category: 'system',
      time: DateTime.now().subtract(const Duration(days: 2)),
      isRead: true,
    ),
  ];

  int get _unreadCount => _notifications.where((n) => !n.isRead).length;

  void _markAllRead() {
    setState(() {
      for (final n in _notifications) {
        n.isRead = true;
      }
    });
  }

  void _openDetail(AppNotification notification) {
    setState(() => notification.isRead = true);
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => NotificationDetailScreen(notification: notification),
      ),
    );
  }

  void _delete(String id) {
    setState(() {
      _notifications.removeWhere((n) => n.id == id);
    });
  }

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

  String _timeAgo(DateTime time) {
    final diff = DateTime.now().difference(time);
    if (diff.inMinutes < 60) return '${diff.inMinutes}m ago';
    if (diff.inHours < 24) return '${diff.inHours}h ago';
    if (diff.inDays == 1) return 'Yesterday';
    return '${diff.inDays}d ago';
  }

  @override
  Widget build(BuildContext context) {
    final safePad = MediaQuery.paddingOf(context);

    return Scaffold(
      backgroundColor: const Color(0xFFF8F8F8),
      body: Column(
        children: [
          // ── Header ──────────────────────────────────────────
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
                  icon: const Icon(Icons.arrow_back_ios_new, size: 20),
                  color: const Color(0xFF111827),
                  onPressed: () => Navigator.pop(context),
                ),
                const Expanded(
                  child: Text(
                    'Notifications',
                    style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.w900,
                      color: Color(0xFF111827),
                    ),
                  ),
                ),
                if (_unreadCount > 0)
                  TextButton(
                    onPressed: _markAllRead,
                    style: TextButton.styleFrom(
                      foregroundColor: _blue,
                      padding: const EdgeInsets.symmetric(
                          horizontal: 10, vertical: 6),
                      textStyle: const TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    child: const Text('Mark all read'),
                  ),
              ],
            ),
          ),

          const Divider(height: 1, thickness: 0.5, color: Color(0xFFE5E7EB)),

          // ── Unread badge ────────────────────────────────────
          if (_unreadCount > 0)
            Container(
              width: double.infinity,
              color: _blue.withValues(alpha: 0.06),
              padding:
                  const EdgeInsets.symmetric(horizontal: 18, vertical: 10),
              child: Text(
                '$_unreadCount unread notification${_unreadCount == 1 ? '' : 's'}',
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w700,
                  color: _blue,
                ),
              ),
            ),

          // ── List ────────────────────────────────────────────
          Expanded(
            child: _notifications.isEmpty
                ? _buildEmptyState()
                : ListView.separated(
                    padding: const EdgeInsets.symmetric(vertical: 8),
                    itemCount: _notifications.length,
                    separatorBuilder: (_, _) => const Divider(
                      height: 1,
                      thickness: 0.5,
                      indent: 72,
                      color: Color(0xFFE5E7EB),
                    ),
                    itemBuilder: (context, index) {
                      final n = _notifications[index];
                      return _NotificationTile(
                        notification: n,
                        categoryIcon: _categoryIcon(n.category),
                        categoryColor: _categoryColor(n.category),
                        timeLabel: _timeAgo(n.time),
                        onTap: () => _openDetail(n),
                        onDelete: () => _delete(n.id),
                      );
                    },
                  ),
          ),
        ],
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            Icons.notifications_off_outlined,
            size: 64,
            color: _blueLight.withValues(alpha: 0.4),
          ),
          const SizedBox(height: 16),
          const Text(
            'No notifications',
            style: TextStyle(
              fontSize: 17,
              fontWeight: FontWeight.w800,
              color: Color(0xFF111827),
            ),
          ),
          const SizedBox(height: 6),
          const Text(
            'You\'re all caught up!',
            style: TextStyle(fontSize: 14, color: Color(0xFF6B7280)),
          ),
        ],
      ),
    );
  }
}

// ── Single tile widget ──────────────────────────────────────────────────────

class _NotificationTile extends StatelessWidget {
  final AppNotification notification;
  final IconData categoryIcon;
  final Color categoryColor;
  final String timeLabel;
  final VoidCallback onTap;
  final VoidCallback onDelete;

  const _NotificationTile({
    required this.notification,
    required this.categoryIcon,
    required this.categoryColor,
    required this.timeLabel,
    required this.onTap,
    required this.onDelete,
  });

  @override
  Widget build(BuildContext context) {
    final isUnread = !notification.isRead;

    return Dismissible(
      key: Key(notification.id),
      direction: DismissDirection.endToStart,
      background: Container(
        alignment: Alignment.centerRight,
        color: const Color(0xFFEF4444),
        padding: const EdgeInsets.only(right: 22),
        child: const Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.delete_rounded, color: Colors.white, size: 24),
            SizedBox(height: 4),
            Text(
              'Delete',
              style: TextStyle(
                color: Colors.white,
                fontSize: 11,
                fontWeight: FontWeight.w700,
              ),
            ),
          ],
        ),
      ),
      onDismissed: (_) => onDelete(),
      child: InkWell(
        onTap: onTap,
        child: Container(
          color: isUnread
              ? const Color(0xFF0B5D85).withValues(alpha: 0.04)
              : Colors.white,
          padding:
              const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Icon circle
              Container(
                width: 44,
                height: 44,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: categoryColor.withValues(alpha: 0.12),
                ),
                child: Icon(categoryIcon, color: categoryColor, size: 22),
              ),

              const SizedBox(width: 12),

              // Content
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            notification.title,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: TextStyle(
                              fontSize: 14,
                              fontWeight: isUnread
                                  ? FontWeight.w800
                                  : FontWeight.w600,
                              color: const Color(0xFF111827),
                            ),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Text(
                          timeLabel,
                          style: const TextStyle(
                            fontSize: 11.5,
                            color: Color(0xFF9CA3AF),
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 4),
                    Text(
                      notification.body,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        fontSize: 13,
                        color: Color(0xFF6B7280),
                        height: 1.4,
                        fontWeight: FontWeight.w400,
                      ),
                    ),
                  ],
                ),
              ),

              // Unread dot
              if (isUnread) ...[
                const SizedBox(width: 8),
                const CircleAvatar(
                  radius: 4,
                  backgroundColor: Color(0xFF0B5D85),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
