import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/theme.dart';
import '../../providers/auth_provider.dart';
import '../../services/interaction_history_service.dart';
import 'my_preferences_screen.dart';
import 'my_learning_profile_screen.dart';
import 'my_current_preferences_screen.dart';
import 'interaction_history_screen.dart';
import '../auth/welcome_screen.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  final InteractionHistoryService _interactionHistoryService =
      InteractionHistoryService();

  String _selectedCount = '0';
  String _savedCount = '0';

  @override
  void initState() {
    super.initState();
    _loadProfileStats();
  }

  Future<void> _loadProfileStats() async {
    try {
      final historyData =
          await _interactionHistoryService.getInteractionHistory();

      final Map<String, dynamic> stats =
          Map<String, dynamic>.from(historyData['stats'] ?? {});

      if (!mounted) {
        return;
      }

      setState(() {
        _selectedCount = '${stats['select_count'] ?? 0}';
        _savedCount = '${stats['save_count'] ?? 0}';
      });
    } catch (_) {
      if (!mounted) {
        return;
      }

      setState(() {
        _selectedCount = '0';
        _savedCount = '0';
      });
    }
  }

  Future<void> _handleLogout(BuildContext context) async {
    final authProvider = Provider.of<AuthProvider>(
      context,
      listen: false,
    );

    await authProvider.logout();

    if (!context.mounted) {
      return;
    }

    Navigator.pushAndRemoveUntil(
      context,
      MaterialPageRoute(
        builder: (context) => const WelcomeScreen(),
      ),
      (route) => false,
    );

    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Logged out successfully.'),
      ),
    );
  }

  Future<void> _showDeleteAccountDialog(
    BuildContext context,
  ) async {
    final bool? confirmed = await showDialog<bool>(
      context: context,
      barrierDismissible: false,
      builder: (dialogContext) {
        return AlertDialog(
          title: const Text(
            'Delete Account?',
          ),
          content: const Text(
            'This will permanently delete your account, '
            'onboarding preferences, interaction history, '
            'learned preferences, and saved personalization data.\n\n'
            'This action cannot be undone.',
          ),
          actions: [
            TextButton(
              onPressed: () {
                Navigator.pop(
                  dialogContext,
                  false,
                );
              },
              child: const Text(
                'Cancel',
              ),
            ),
            TextButton(
              onPressed: () {
                Navigator.pop(
                  dialogContext,
                  true,
                );
              },
              child: const Text(
                'Delete',
                style: TextStyle(
                  color: Color(0xFFEF4444),
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          ],
        );
      },
    );

    if (confirmed == true && context.mounted) {
      await _handleDeleteAccount(context);
    }
  }

  Future<void> _handleDeleteAccount(
    BuildContext context,
  ) async {
    final authProvider = Provider.of<AuthProvider>(
      context,
      listen: false,
    );

    final bool success =
        await authProvider.deleteAccount();

    if (!context.mounted) {
      return;
    }

    if (success) {
      Navigator.pushAndRemoveUntil(
        context,
        MaterialPageRoute(
          builder: (context) => const WelcomeScreen(),
        ),
        (route) => false,
      );

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'Account deleted successfully.',
          ),
        ),
      );

      return;
    }

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          authProvider.errorMessage ??
              'Failed to delete account.',
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final authProvider = Provider.of<AuthProvider>(context);
    final user = authProvider.currentUser;

    return Scaffold(
      backgroundColor: AppTheme.backgroundColor,
      body: SafeArea(
        child: Column(
          children: [
            _buildHeader(context),
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(
                  20,
                  12,
                  20,
                  24,
                ),
                child: Column(
                  children: [
                    _buildProfileCard(
                      fullName:
                          user?.fullName ?? 'OutfitIQ User',
                      email:
                          user?.email ?? 'No email available',
                      profilePicture:
                          user?.profilePicture,
                    ),
                    const SizedBox(height: 20),

                    _buildMenuItem(
                      icon: Icons.tune_rounded,
                      title: 'My Preferences',
                      subtitle:
                          'Style, colors and fashion preferences',
                      onTap: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) =>
                                const MyPreferencesScreen(),
                          ),
                        );
                      },
                    ),

                    _buildMenuItem(
                      icon: Icons.psychology_alt_rounded,
                      title: 'My Learning Profile',
                      subtitle:
                          'Preferences learned from your interactions',
                      onTap: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) =>
                                const MyLearningProfileScreen(),
                          ),
                        );
                      },
                    ),

                    _buildMenuItem(
                      icon: Icons.auto_awesome_rounded,
                      title: 'My Current Preferences',
                      subtitle:
                          'Your current likes based on preferences and activity',
                      onTap: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) =>
                                const MyCurrentPreferencesScreen(),
                          ),
                        );
                      },
                    ),

                    _buildMenuItem(
                      icon: Icons.history_rounded,
                      title: 'Interaction History',
                      subtitle:
                          'Clicked, selected and saved fashion items',
                      onTap: () async {
                        await Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) =>
                                const InteractionHistoryScreen(),
                          ),
                        );

                        _loadProfileStats();
                      },
                    ),

                    _buildMenuItem(
                      icon: Icons.notifications_none_rounded,
                      title: 'Notifications',
                      subtitle:
                          'Manage fashion update notifications',
                      onTap: () {
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(
                            content: Text(
                              'Notifications will be added later.',
                            ),
                          ),
                        );
                      },
                    ),

                    _buildMenuItem(
                      icon: Icons.privacy_tip_outlined,
                      title: 'Privacy & Security',
                      subtitle: 'Manage account security',
                      onTap: () {
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(
                            content: Text(
                              'Privacy settings will be added later.',
                            ),
                          ),
                        );
                      },
                    ),

                    _buildMenuItem(
                      icon: Icons.help_outline_rounded,
                      title: 'Help Center',
                      subtitle: 'Get support and FAQs',
                      onTap: () {
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(
                            content: Text(
                              'Help center will be added later.',
                            ),
                          ),
                        );
                      },
                    ),

                    const SizedBox(height: 8),

                    _buildDeleteAccountCard(context),

                    const SizedBox(height: 12),

                    _buildLogoutCard(context),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(
        8,
        12,
        20,
        8,
      ),
      child: Row(
        children: [
          IconButton(
            onPressed: () {
              Navigator.pop(context);
            },
            icon: const Icon(
              Icons.arrow_back_ios_new_rounded,
              size: 20,
              color: AppTheme.darkTextColor,
            ),
          ),
          const SizedBox(width: 4),
          const Text(
            'Profile',
            style: TextStyle(
              fontSize: 21,
              fontWeight: FontWeight.bold,
              color: AppTheme.darkTextColor,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildProfileCard({
    required String fullName,
    required String email,
    required String? profilePicture,
  }) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(22),
      decoration: BoxDecoration(
        color: AppTheme.primaryColor,
        borderRadius: BorderRadius.circular(22),
      ),
      child: Column(
        children: [
          Row(
            children: [
              CircleAvatar(
                radius: 33,
                backgroundColor:
                    Colors.white.withOpacity(0.18),
                backgroundImage:
                    profilePicture != null &&
                            profilePicture.isNotEmpty
                        ? NetworkImage(profilePicture)
                        : null,
                child:
                    profilePicture == null ||
                            profilePicture.isEmpty
                        ? const Icon(
                            Icons.person_rounded,
                            color: Colors.white,
                            size: 36,
                          )
                        : null,
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment:
                      CrossAxisAlignment.start,
                  children: [
                    Text(
                      fullName,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        fontSize: 19,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                    ),
                    const SizedBox(height: 5),
                    Text(
                      email,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        fontSize: 13,
                        color: Colors.white,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Container(
                      padding:
                          const EdgeInsets.symmetric(
                        horizontal: 10,
                        vertical: 5,
                      ),
                      decoration: BoxDecoration(
                        color:
                            Colors.white.withOpacity(0.18),
                        borderRadius:
                            BorderRadius.circular(20),
                      ),
                      child: const Text(
                        'Edit Profile',
                        style: TextStyle(
                          fontSize: 11,
                          color: Colors.white,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),

          const SizedBox(height: 22),

          Divider(
            color: Colors.white.withOpacity(0.22),
            thickness: 1,
          ),

          const SizedBox(height: 16),

          Row(
            children: [
              const Expanded(
                child: _ProfileStat(
                  value: '6',
                  label: 'Preferences',
                ),
              ),
              const _VerticalDivider(),
              Expanded(
                child: _ProfileStat(
                  value: _selectedCount,
                  label: 'Selected',
                ),
              ),
              const _VerticalDivider(),
              Expanded(
                child: _ProfileStat(
                  value: _savedCount,
                  label: 'Saved',
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildMenuItem({
    required IconData icon,
    required String title,
    required String subtitle,
    required VoidCallback onTap,
  }) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      child: Material(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(16),
          child: Padding(
            padding: const EdgeInsets.symmetric(
              horizontal: 14,
              vertical: 14,
            ),
            child: Row(
              children: [
                Container(
                  width: 42,
                  height: 42,
                  decoration: BoxDecoration(
                    color: AppTheme.primaryColor
                        .withOpacity(0.08),
                    shape: BoxShape.circle,
                  ),
                  child: Icon(
                    icon,
                    color: AppTheme.primaryColor,
                    size: 21,
                  ),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment:
                        CrossAxisAlignment.start,
                    children: [
                      Text(
                        title,
                        style: const TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.bold,
                          color:
                              AppTheme.darkTextColor,
                        ),
                      ),
                      const SizedBox(height: 3),
                      Text(
                        subtitle,
                        style: const TextStyle(
                          fontSize: 12,
                          color:
                              AppTheme.lightTextColor,
                        ),
                      ),
                    ],
                  ),
                ),
                const Icon(
                  Icons.arrow_forward_ios_rounded,
                  size: 15,
                  color: Color(0xFF9CA3AF),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildDeleteAccountCard(
    BuildContext context,
  ) {
    return Material(
      color: const Color(0xFFFFF7F7),
      borderRadius: BorderRadius.circular(16),
      child: InkWell(
        onTap: () {
          _showDeleteAccountDialog(context);
        },
        borderRadius: BorderRadius.circular(16),
        child: Container(
          width: double.infinity,
          padding: const EdgeInsets.symmetric(
            horizontal: 14,
            vertical: 16,
          ),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(16),
            border: Border.all(
              color: const Color(0xFFFFC7C7),
              width: 1,
            ),
          ),
          child: Row(
            children: [
              Container(
                width: 42,
                height: 42,
                decoration: const BoxDecoration(
                  color: Color(0xFFFFEEEE),
                  shape: BoxShape.circle,
                ),
                child: const Icon(
                  Icons.delete_forever_rounded,
                  color: Color(0xFFEF4444),
                  size: 21,
                ),
              ),
              const SizedBox(width: 14),
              const Expanded(
                child: Column(
                  crossAxisAlignment:
                      CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Delete Account',
                      style: TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.bold,
                        color: Color(0xFFEF4444),
                      ),
                    ),
                    SizedBox(height: 3),
                    Text(
                      'Permanently remove your account and saved data',
                      style: TextStyle(
                        fontSize: 12,
                        color:
                            AppTheme.lightTextColor,
                      ),
                    ),
                  ],
                ),
              ),
              const Icon(
                Icons.arrow_forward_ios_rounded,
                size: 15,
                color: Color(0xFFEF4444),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildLogoutCard(BuildContext context) {
    return Material(
      color: const Color(0xFFFFF7F7),
      borderRadius: BorderRadius.circular(16),
      child: InkWell(
        onTap: () => _handleLogout(context),
        borderRadius: BorderRadius.circular(16),
        child: Container(
          width: double.infinity,
          padding: const EdgeInsets.symmetric(
            horizontal: 14,
            vertical: 16,
          ),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(16),
            border: Border.all(
              color: const Color(0xFFFFC7C7),
              width: 1,
            ),
          ),
          child: Row(
            children: [
              Container(
                width: 42,
                height: 42,
                decoration: const BoxDecoration(
                  color: Color(0xFFFFEEEE),
                  shape: BoxShape.circle,
                ),
                child: const Icon(
                  Icons.logout_rounded,
                  color: Color(0xFFEF4444),
                  size: 21,
                ),
              ),
              const SizedBox(width: 14),
              const Expanded(
                child: Column(
                  crossAxisAlignment:
                      CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Logout',
                      style: TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.bold,
                        color: Color(0xFFEF4444),
                      ),
                    ),
                    SizedBox(height: 3),
                    Text(
                      'Sign out of your account',
                      style: TextStyle(
                        fontSize: 12,
                        color:
                            AppTheme.lightTextColor,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _ProfileStat extends StatelessWidget {
  final String value;
  final String label;

  const _ProfileStat({
    required this.value,
    required this.label,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(
          value,
          style: const TextStyle(
            fontSize: 19,
            fontWeight: FontWeight.bold,
            color: Colors.white,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          label,
          style: const TextStyle(
            fontSize: 11,
            color: Colors.white,
          ),
        ),
      ],
    );
  }
}

class _VerticalDivider extends StatelessWidget {
  const _VerticalDivider();

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 1,
      height: 34,
      color: Colors.white24,
    );
  }
}