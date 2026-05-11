import 'package:flutter/material.dart';

import '../core/theme.dart';

class ProfilePreferencesSection extends StatelessWidget {
  final bool isLoadingProfile;
  final String? profileError;
  final Map<String, dynamic>? profileData;

  const ProfilePreferencesSection({
    super.key,
    required this.isLoadingProfile,
    required this.profileError,
    required this.profileData,
  });

  @override
  Widget build(BuildContext context) {
    if (isLoadingProfile) {
      return _buildContainer(
        child: const Center(
          child: CircularProgressIndicator(
            color: AppTheme.primaryColor,
          ),
        ),
      );
    }

    if (profileError != null) {
      return _buildContainer(
        child: Text(
          profileError!,
          style: const TextStyle(
            fontSize: 13,
            color: Color(0xFFEF4444),
          ),
        ),
      );
    }

    final onboarding = profileData?['onboarding_preferences'];

    if (onboarding == null) {
      return _buildContainer(
        child: const Text(
          'No saved preferences found.',
          style: TextStyle(
            fontSize: 13,
            color: AppTheme.lightTextColor,
          ),
        ),
      );
    }

    final List<String> categories =
        List<String>.from(onboarding['preferred_categories'] ?? []);
    final List<String> colors =
        List<String>.from(onboarding['preferred_colors'] ?? []);
    final List<String> styles =
        List<String>.from(onboarding['preferred_styles'] ?? []);
    final List<String> occasions =
        List<String>.from(onboarding['occasions'] ?? []);
    final List<String> choicePriorities =
        List<String>.from(onboarding['choice_priorities'] ?? []);
    final List<String> preferredBrands =
        List<String>.from(onboarding['preferred_brands'] ?? []);

    return _buildContainer(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Saved Preferences',
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.bold,
              color: AppTheme.darkTextColor,
            ),
          ),
          const SizedBox(height: 14),
          _PreferenceGroup(
            title: 'Categories',
            values: categories,
          ),
          _PreferenceGroup(
            title: 'Colors',
            values: colors,
          ),
          _PreferenceGroup(
            title: 'Styles',
            values: styles,
          ),
          _PreferenceGroup(
            title: 'Occasions',
            values: occasions,
          ),
          _PreferenceGroup(
            title: 'What matters most',
            values: choicePriorities,
          ),
          _PreferenceGroup(
            title: 'Preferred brands',
            values: preferredBrands,
          ),
        ],
      ),
    );
  }

  Widget _buildContainer({
    required Widget child,
  }) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
      ),
      child: child,
    );
  }
}

class _PreferenceGroup extends StatelessWidget {
  final String title;
  final List<String> values;

  const _PreferenceGroup({
    required this.title,
    required this.values,
  });

  @override
  Widget build(BuildContext context) {
    if (values.isEmpty) {
      return const SizedBox.shrink();
    }

    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: const TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.bold,
              color: AppTheme.darkTextColor,
            ),
          ),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: values.map((value) {
              return Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 10,
                  vertical: 6,
                ),
                decoration: BoxDecoration(
                  color: AppTheme.primaryColor.withOpacity(0.09),
                  borderRadius: BorderRadius.circular(18),
                ),
                child: Text(
                  value,
                  style: const TextStyle(
                    fontSize: 12,
                    color: AppTheme.primaryColor,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              );
            }).toList(),
          ),
        ],
      ),
    );
  }
}