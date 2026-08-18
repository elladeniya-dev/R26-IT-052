import 'package:flutter/material.dart';

import '../../core/theme.dart';
import '../../services/profile_service.dart';

class MyCurrentPreferencesScreen extends StatefulWidget {
  const MyCurrentPreferencesScreen({super.key});

  @override
  State<MyCurrentPreferencesScreen> createState() =>
      _MyCurrentPreferencesScreenState();
}

class _MyCurrentPreferencesScreenState
    extends State<MyCurrentPreferencesScreen> {
  final ProfileService _profileService = ProfileService();

  bool _isLoading = true;
  String? _errorMessage;

  Map<String, dynamic> _categoryScores = {};
  Map<String, dynamic> _colorScores = {};
  Map<String, dynamic> _styleScores = {};
  Map<String, dynamic> _brandScores = {};

  @override
  void initState() {
    super.initState();
    _loadCurrentPreferences();
  }

  Future<void> _loadCurrentPreferences() async {
    try {
      final Map<String, dynamic> data =
          await _profileService.getCurrentPreferences();

      if (!mounted) {
        return;
      }

      setState(() {
        _categoryScores =
            _toMap(data['category_scores']);

        _colorScores =
            _toMap(data['color_scores']);

        _styleScores =
            _toMap(data['style_scores']);

        _brandScores =
            _toMap(data['brand_scores']);

        _isLoading = false;
        _errorMessage = null;
      });
    } catch (e) {
      if (!mounted) {
        return;
      }

      setState(() {
        _errorMessage = e.toString();
        _isLoading = false;
      });
    }
  }

  Future<void> _refresh() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    await _loadCurrentPreferences();
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
                onRefresh: _refresh,
                child: SingleChildScrollView(
                  physics:
                      const AlwaysScrollableScrollPhysics(),
                  padding:
                      const EdgeInsets.fromLTRB(
                    20,
                    16,
                    20,
                    24,
                  ),
                  child: Column(
                    crossAxisAlignment:
                        CrossAxisAlignment.start,
                    children: [
                      _buildInfoCard(),

                      const SizedBox(height: 18),

                      _buildContent(),
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
      padding:
          const EdgeInsets.fromLTRB(8, 12, 20, 8),
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

          const Expanded(
            child: Text(
              'My Current Preferences',
              style: TextStyle(
                fontSize: 21,
                fontWeight: FontWeight.bold,
                color: AppTheme.darkTextColor,
              ),
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
            Icons.auto_awesome_rounded,
            color: Colors.white,
            size: 32,
          ),

          SizedBox(width: 14),

          Expanded(
            child: Column(
              crossAxisAlignment:
                  CrossAxisAlignment.start,
              children: [
                Text(
                  'Your Current Fashion Likes',
                  style: TextStyle(
                    fontSize: 17,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                ),

                SizedBox(height: 5),

                Text(
                  'These preferences combine your onboarding choices with what OutfitIQ has learned from your activity.',
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

  Widget _buildContent() {
    if (_isLoading) {
      return _buildContainer(
        child: const Center(
          child: CircularProgressIndicator(
            color: AppTheme.primaryColor,
          ),
        ),
      );
    }

    if (_errorMessage != null) {
      return _buildContainer(
        child: Text(
          _errorMessage!,
          style: const TextStyle(
            fontSize: 13,
            color: Color(0xFFEF4444),
          ),
        ),
      );
    }

    final bool hasAnyData =
        _categoryScores.isNotEmpty ||
        _colorScores.isNotEmpty ||
        _styleScores.isNotEmpty ||
        _brandScores.isNotEmpty;

    if (!hasAnyData) {
      return _buildContainer(
        child: const Column(
          crossAxisAlignment:
              CrossAxisAlignment.start,
          children: [
            Text(
              'No current preferences yet',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
                color: AppTheme.darkTextColor,
              ),
            ),

            SizedBox(height: 8),

            Text(
              'Complete onboarding and interact with fashion items to build your current preference profile.',
              style: TextStyle(
                fontSize: 13,
                height: 1.45,
                color: AppTheme.lightTextColor,
              ),
            ),
          ],
        ),
      );
    }

    return Column(
      children: [
        _buildSummaryCard(),

        const SizedBox(height: 14),

        _CurrentPreferenceSection(
          title: 'Current Categories',
          icon: Icons.category_outlined,
          scores: _categoryScores,
        ),

        const SizedBox(height: 14),

        _CurrentPreferenceSection(
          title: 'Current Colors',
          icon: Icons.palette_outlined,
          scores: _colorScores,
        ),

        const SizedBox(height: 14),

        _CurrentPreferenceSection(
          title: 'Current Styles',
          icon: Icons.checkroom_outlined,
          scores: _styleScores,
        ),

        const SizedBox(height: 14),

        _CurrentPreferenceSection(
          title: 'Current Brands',
          icon: Icons.local_offer_outlined,
          scores: _brandScores,
        ),
      ],
    );
  }

  Widget _buildSummaryCard() {
    return _buildContainer(
      child: Column(
        crossAxisAlignment:
            CrossAxisAlignment.start,
        children: [
          const Text(
            'Current Preference Summary',
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.bold,
              color: AppTheme.darkTextColor,
            ),
          ),

          const SizedBox(height: 14),

          _SummaryRow(
            icon: Icons.category_outlined,
            label: 'Top category',
            value: _getTopValue(
              _categoryScores,
            ),
          ),

          _SummaryRow(
            icon: Icons.palette_outlined,
            label: 'Top color',
            value: _getTopValue(
              _colorScores,
            ),
          ),

          _SummaryRow(
            icon: Icons.checkroom_outlined,
            label: 'Top style',
            value: _getTopValue(
              _styleScores,
            ),
          ),

          _SummaryRow(
            icon: Icons.local_offer_outlined,
            label: 'Top brand',
            value: _getTopValue(
              _brandScores,
            ),
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

  Map<String, dynamic> _toMap(dynamic value) {
    if (value == null) {
      return {};
    }

    if (value is Map<String, dynamic>) {
      return value;
    }

    if (value is Map) {
      return Map<String, dynamic>.from(value);
    }

    return {};
  }

  String _getTopValue(
    Map<String, dynamic> scores,
  ) {
    if (scores.isEmpty) {
      return 'Not available';
    }

    final entries = scores.entries.toList();

    entries.sort(
      (a, b) => _toDouble(b.value)
          .compareTo(
        _toDouble(a.value),
      ),
    );

    return entries.first.key;
  }
}

class _CurrentPreferenceSection
    extends StatelessWidget {
  final String title;
  final IconData icon;
  final Map<String, dynamic> scores;

  const _CurrentPreferenceSection({
    required this.title,
    required this.icon,
    required this.scores,
  });

  @override
  Widget build(BuildContext context) {
    if (scores.isEmpty) {
      return _buildContainer(
        child: Row(
          children: [
            Icon(
              icon,
              color: AppTheme.primaryColor,
              size: 22,
            ),

            const SizedBox(width: 10),

            Expanded(
              child: Text(
                '$title: No data yet',
                style: const TextStyle(
                  fontSize: 13,
                  color:
                      AppTheme.lightTextColor,
                ),
              ),
            ),
          ],
        ),
      );
    }

    final entries = scores.entries.toList();

    entries.sort(
      (a, b) => _toDouble(b.value)
          .compareTo(
        _toDouble(a.value),
      ),
    );

    return _buildContainer(
      child: Column(
        crossAxisAlignment:
            CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                icon,
                color: AppTheme.primaryColor,
                size: 22,
              ),

              const SizedBox(width: 9),

              Text(
                title,
                style: const TextStyle(
                  fontSize: 15,
                  fontWeight: FontWeight.bold,
                  color:
                      AppTheme.darkTextColor,
                ),
              ),
            ],
          ),

          const SizedBox(height: 14),

          ...entries.map(
            (entry) {
              final double value =
                  _toDouble(entry.value);

              return _PreferenceRow(
                label: entry.key,
                value: value,
              );
            },
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
        borderRadius:
            BorderRadius.circular(18),
      ),
      child: child,
    );
  }
}

class _SummaryRow extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;

  const _SummaryRow({
    required this.icon,
    required this.label,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding:
          const EdgeInsets.only(bottom: 11),
      child: Row(
        children: [
          Icon(
            icon,
            size: 19,
            color: AppTheme.primaryColor,
          ),

          const SizedBox(width: 9),

          Expanded(
            child: Text(
              label,
              style: const TextStyle(
                fontSize: 13,
                color:
                    AppTheme.lightTextColor,
              ),
            ),
          ),

          Text(
            value,
            style: const TextStyle(
              fontSize: 13,
              color: AppTheme.darkTextColor,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }
}

class _PreferenceRow extends StatelessWidget {
  final String label;
  final double value;

  const _PreferenceRow({
    required this.label,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding:
          const EdgeInsets.only(bottom: 13),
      child: Column(
        crossAxisAlignment:
            CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  label,
                  style: const TextStyle(
                    fontSize: 13,
                    fontWeight:
                        FontWeight.w600,
                    color:
                        AppTheme.darkTextColor,
                  ),
                ),
              ),

              Text(
                value.toStringAsFixed(2),
                style: const TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.bold,
                  color:
                      AppTheme.primaryColor,
                ),
              ),
            ],
          ),

          const SizedBox(height: 7),

          ClipRRect(
            borderRadius:
                BorderRadius.circular(20),
            child: LinearProgressIndicator(
              value:
                  value.clamp(0.0, 1.0),
              minHeight: 7,
              backgroundColor:
                  const Color(0xFFE5E7EB),
              valueColor:
                  const AlwaysStoppedAnimation<Color>(
                AppTheme.primaryColor,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

double _toDouble(dynamic value) {
  if (value == null) {
    return 0;
  }

  if (value is int) {
    return value.toDouble();
  }

  if (value is double) {
    return value;
  }

  if (value is String) {
    return double.tryParse(value) ?? 0;
  }

  return 0;
}