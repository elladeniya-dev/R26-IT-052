import 'package:flutter/material.dart';

import '../../core/theme.dart';
import '../../services/profile_service.dart';
import '../../widgets/profile_preferences_section.dart';

class MyPreferencesScreen extends StatefulWidget {
  const MyPreferencesScreen({super.key});

  @override
  State<MyPreferencesScreen> createState() => _MyPreferencesScreenState();
}

class _MyPreferencesScreenState extends State<MyPreferencesScreen> {
  final ProfileService _profileService = ProfileService();

  bool _isLoadingProfile = true;
  String? _profileError;
  Map<String, dynamic>? _profileData;

  @override
  void initState() {
    super.initState();
    _loadProfile();
  }

  Future<void> _loadProfile() async {
    try {
      final profile = await _profileService.getProfile();

      if (!mounted) {
        return;
      }

      setState(() {
        _profileData = profile;
        _isLoadingProfile = false;
      });
    } catch (e) {
      if (!mounted) {
        return;
      }

      setState(() {
        _profileError = e.toString();
        _isLoadingProfile = false;
      });
    }
  }

  Future<void> _refreshProfile() async {
    setState(() {
      _isLoadingProfile = true;
      _profileError = null;
    });

    await _loadProfile();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundColor,
      body: SafeArea(
        child: Column(
          children: [
            _buildHeader(context),
            Expanded(
              child: RefreshIndicator(
                color: AppTheme.primaryColor,
                onRefresh: _refreshProfile,
                child: SingleChildScrollView(
                  physics: const AlwaysScrollableScrollPhysics(),
                  padding: const EdgeInsets.fromLTRB(20, 16, 20, 24),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      _buildInfoCard(),
                      const SizedBox(height: 18),
                      ProfilePreferencesSection(
                        isLoadingProfile: _isLoadingProfile,
                        profileError: _profileError,
                        profileData: _profileData,
                      ),
                    ],
                  ),
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
      padding: const EdgeInsets.fromLTRB(8, 12, 20, 8),
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
            'My Preferences',
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

  Widget _buildInfoCard() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: AppTheme.primaryColor,
        borderRadius: BorderRadius.circular(18),
      ),
      child: const Row(
        children: [
          Icon(
            Icons.tune_rounded,
            color: Colors.white,
            size: 30,
          ),
          SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Your Style Preferences',
                  style: TextStyle(
                    fontSize: 17,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                ),
                SizedBox(height: 5),
                Text(
                  'These preferences help Wearify personalize fashion recommendations for you.',
                  style: TextStyle(
                    fontSize: 13,
                    height: 1.4,
                    color: Colors.white,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}