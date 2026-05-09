import 'package:flutter/material.dart';

import '../../core/theme.dart';
import '../../services/profile_service.dart';

class MyLearningProfileScreen extends StatefulWidget {
  const MyLearningProfileScreen({super.key});

  @override
  State<MyLearningProfileScreen> createState() =>
      _MyLearningProfileScreenState();
}

class _MyLearningProfileScreenState extends State<MyLearningProfileScreen> {
  final ProfileService _profileService = ProfileService();

  bool _isLoading = true;
  String? _errorMessage;
  Map<String, dynamic>? _profileData;

  @override
  void initState() {
    super.initState();
    _loadLearningProfile();
  }

  Future<void> _loadLearningProfile() async {
    try {
      final profile = await _profileService.getProfile();

      if (!mounted) {
        return;
      }

      setState(() {
        _profileData = profile;
        _isLoading = false;
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

  Future<void> _refreshLearningProfile() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    await _loadLearningProfile();
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
                onRefresh: _refreshLearningProfile,
                child: SingleChildScrollView(
                  physics: const AlwaysScrollableScrollPhysics(),
                  padding: const EdgeInsets.fromLTRB(20, 16, 20, 24),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      _buildInfoCard(),
                      const SizedBox(height: 18),
                      _buildLearningContent(),
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
          const Expanded(
            child: Text(
              'My Learning Profile',
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
            Icons.psychology_alt_rounded,
            color: Colors.white,
            size: 32,
          ),
          SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Learned Style Profile',
                  style: TextStyle(
                    fontSize: 17,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                ),
                SizedBox(height: 5),
                Text(
                  'These values are learned from your clicks, saves, selections and dislikes.',
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

  Widget _buildLearningContent() {
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

    final learnedPreferences = _profileData?['learned_preferences'];

    if (learnedPreferences == null) {
      return _buildContainer(
        child: const Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'No learned preferences yet',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
                color: AppTheme.darkTextColor,
              ),
            ),
            SizedBox(height: 8),
            Text(
              'Interact with products on the Home screen. Save, select or dislike items to help the app learn your fashion taste.',
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

    final Map<String, dynamic> categoryWeights =
        _toMap(learnedPreferences['category_weights']);
    final Map<String, dynamic> colorWeights =
        _toMap(learnedPreferences['color_weights']);
    final Map<String, dynamic> styleWeights =
        _toMap(learnedPreferences['style_weights']);
    final Map<String, dynamic> brandWeights =
        _toMap(learnedPreferences['brand_weights']);

    return Column(
      children: [
        _buildSummaryCard(
          categoryWeights: categoryWeights,
          colorWeights: colorWeights,
          styleWeights: styleWeights,
          brandWeights: brandWeights,
        ),
        const SizedBox(height: 14),
        _LearningWeightSection(
          title: 'Category Learning',
          icon: Icons.category_outlined,
          weights: categoryWeights,
        ),
        const SizedBox(height: 14),
        _LearningWeightSection(
          title: 'Color Learning',
          icon: Icons.palette_outlined,
          weights: colorWeights,
        ),
        const SizedBox(height: 14),
        _LearningWeightSection(
          title: 'Style Learning',
          icon: Icons.checkroom_outlined,
          weights: styleWeights,
        ),
        const SizedBox(height: 14),
        _LearningWeightSection(
          title: 'Brand Learning',
          icon: Icons.local_offer_outlined,
          weights: brandWeights,
        ),
      ],
    );
  }

  Widget _buildSummaryCard({
    required Map<String, dynamic> categoryWeights,
    required Map<String, dynamic> colorWeights,
    required Map<String, dynamic> styleWeights,
    required Map<String, dynamic> brandWeights,
  }) {
    final String topCategory = _getTopValue(categoryWeights);
    final String topColor = _getTopValue(colorWeights);
    final String topStyle = _getTopValue(styleWeights);
    final String topBrand = _getTopValue(brandWeights);

    return _buildContainer(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Learning Summary',
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
            value: topCategory,
          ),
          _SummaryRow(
            icon: Icons.palette_outlined,
            label: 'Top color',
            value: topColor,
          ),
          _SummaryRow(
            icon: Icons.checkroom_outlined,
            label: 'Top style',
            value: topStyle,
          ),
          _SummaryRow(
            icon: Icons.local_offer_outlined,
            label: 'Top brand',
            value: topBrand,
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

  String _getTopValue(Map<String, dynamic> weights) {
    if (weights.isEmpty) {
      return 'Not learned yet';
    }

    final entries = weights.entries.toList();

    entries.sort((a, b) {
      final double firstValue = _toDouble(a.value);
      final double secondValue = _toDouble(b.value);

      return secondValue.compareTo(firstValue);
    });

    return entries.first.key;
  }
}

class _LearningWeightSection extends StatelessWidget {
  final String title;
  final IconData icon;
  final Map<String, dynamic> weights;

  const _LearningWeightSection({
    required this.title,
    required this.icon,
    required this.weights,
  });

  @override
  Widget build(BuildContext context) {
    if (weights.isEmpty) {
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
                  color: AppTheme.lightTextColor,
                ),
              ),
            ),
          ],
        ),
      );
    }

    final entries = weights.entries.toList();

    entries.sort((a, b) {
      final double firstValue = _toDouble(a.value);
      final double secondValue = _toDouble(b.value);

      return secondValue.compareTo(firstValue);
    });

    final double maxValue = entries
        .map((entry) => _toDouble(entry.value).abs())
        .fold<double>(0, (previous, current) {
      return current > previous ? current : previous;
    });

    return _buildContainer(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
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
                  color: AppTheme.darkTextColor,
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          ...entries.map((entry) {
            final double value = _toDouble(entry.value);
            final double progress =
                maxValue == 0 ? 0 : (value.abs() / maxValue).clamp(0.0, 1.0);

            return _WeightRow(
              label: entry.key,
              value: value,
              progress: progress,
            );
          }),
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
      padding: const EdgeInsets.only(bottom: 11),
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
                color: AppTheme.lightTextColor,
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

class _WeightRow extends StatelessWidget {
  final String label;
  final double value;
  final double progress;

  const _WeightRow({
    required this.label,
    required this.value,
    required this.progress,
  });

  @override
  Widget build(BuildContext context) {
    final bool isNegative = value < 0;

    return Padding(
      padding: const EdgeInsets.only(bottom: 13),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  label,
                  style: const TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                    color: AppTheme.darkTextColor,
                  ),
                ),
              ),
              Text(
                value.toStringAsFixed(2),
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.bold,
                  color: isNegative
                      ? const Color(0xFFEF4444)
                      : AppTheme.primaryColor,
                ),
              ),
            ],
          ),
          const SizedBox(height: 7),
          ClipRRect(
            borderRadius: BorderRadius.circular(20),
            child: LinearProgressIndicator(
              value: progress,
              minHeight: 7,
              backgroundColor: const Color(0xFFE5E7EB),
              valueColor: AlwaysStoppedAnimation<Color>(
                isNegative ? const Color(0xFFEF4444) : AppTheme.primaryColor,
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