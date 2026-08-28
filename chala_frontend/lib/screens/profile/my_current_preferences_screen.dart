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

  // =========================================================
  // CURRENT DYNAMIC PREFERENCE SCORES
  // =========================================================

  Map<String, dynamic> _categoryScores = {};
  Map<String, dynamic> _colorScores = {};
  Map<String, dynamic> _styleScores = {};
  Map<String, dynamic> _brandScores = {};

  // =========================================================
  // ML EXPANSIONS
  // =========================================================

  List<Map<String, dynamic>> _mlColors = [];
  List<Map<String, dynamic>> _mlCategories = [];
  List<Map<String, dynamic>> _mlStyles = [];

  // =========================================================
  // FINAL ENRICHED PREFERENCES
  // =========================================================

  List<String> _enrichedColors = [];
  List<String> _enrichedCategories = [];
  List<String> _enrichedStyles = [];
  List<String> _occasions = [];
  List<String> _choicePriorities = [];
  List<String> _preferredBrands = [];

  @override
  void initState() {
    super.initState();
    _loadCurrentPreferences();
  }

  // =========================================================
  // LOAD CURRENT + ML-ENRICHED PROFILE
  // =========================================================

  Future<void> _loadCurrentPreferences() async {
    try {
      final Map<String, dynamic> data =
          await _profileService
              .getEnrichedCurrentPreferences();

      final Map<String, dynamic> currentPreferences =
          _toMap(
        data['current_preferences'],
      );

      final Map<String, dynamic> mlExpansions =
          _toMap(
        data['ml_expansions'],
      );

      final Map<String, dynamic> enrichedPreferences =
          _toMap(
        data['enriched_preferences'],
      );

      if (!mounted) {
        return;
      }

      setState(() {
        // -------------------------------------------------
        // Dynamic preferences
        // -------------------------------------------------

        _categoryScores = _toMap(
          currentPreferences['category_scores'],
        );

        _colorScores = _toMap(
          currentPreferences['color_scores'],
        );

        _styleScores = _toMap(
          currentPreferences['style_scores'],
        );

        _brandScores = _toMap(
          currentPreferences['brand_scores'],
        );

        // -------------------------------------------------
        // ML additions
        // -------------------------------------------------

        _mlColors = _toListOfMaps(
          mlExpansions['colors'],
        );

        _mlCategories = _toListOfMaps(
          mlExpansions['categories'],
        );

        _mlStyles = _toListOfMaps(
          mlExpansions['styles'],
        );

        // -------------------------------------------------
        // Final enriched profile
        // -------------------------------------------------

        _enrichedColors = _toStringList(
          enrichedPreferences['preferred_colors'],
        );

        _enrichedCategories = _toStringList(
          enrichedPreferences[
              'preferred_categories'],
        );

        _enrichedStyles = _toStringList(
          enrichedPreferences['preferred_styles'],
        );

        _occasions = _toStringList(
          enrichedPreferences['occasions'],
        );

       // _choicePriorities = _toStringList(
       //   enrichedPreferences['choice_priorities'],
       // );

        _preferredBrands = _toStringList(
          enrichedPreferences['preferred_brands'],
        );

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

  // =========================================================
  // BUILD SCREEN
  // =========================================================

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
                  padding: const EdgeInsets.fromLTRB(
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

  // =========================================================
  // HEADER
  // =========================================================

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

  // =========================================================
  // TOP INFORMATION CARD
  // =========================================================

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
                  'Your Dynamic Fashion Profile',
                  style: TextStyle(
                    fontSize: 17,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                ),

                SizedBox(height: 5),

                Text(
                  'Your onboarding choices and activity are continuously combined, then enriched using the OutfitIQ preference model.',
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

  // =========================================================
  // MAIN CONTENT
  // =========================================================

  Widget _buildContent() {
    if (_isLoading) {
      return _buildContainer(
        child: const Center(
          child: Padding(
            padding: EdgeInsets.all(20),
            child: CircularProgressIndicator(
              color: AppTheme.primaryColor,
            ),
          ),
        ),
      );
    }

    if (_errorMessage != null) {
      return _buildContainer(
        child: Column(
          children: [
            const Icon(
              Icons.error_outline_rounded,
              color: Color(0xFFEF4444),
              size: 30,
            ),

            const SizedBox(height: 10),

            Text(
              _errorMessage!,
              textAlign: TextAlign.center,
              style: const TextStyle(
                fontSize: 13,
                color: Color(0xFFEF4444),
              ),
            ),
          ],
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
      crossAxisAlignment:
          CrossAxisAlignment.start,
      children: [
        // -------------------------------------------------
        // CURRENT DYNAMIC PROFILE
        // -------------------------------------------------

        _buildSectionTitle(
          'Current Learned Profile',
          'Built from onboarding and your interactions.',
        ),

        const SizedBox(height: 12),

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

        const SizedBox(height: 24),

        // -------------------------------------------------
        // ML EXPANSION
        // -------------------------------------------------

        _buildSectionTitle(
          'ML Preference Expansion',
          'New preferences predicted from your current profile.',
        ),

        const SizedBox(height: 12),

        _buildMLExpansionCard(),

        const SizedBox(height: 24),

        // -------------------------------------------------
        // FINAL ENRICHED PROFILE
        // -------------------------------------------------

        _buildSectionTitle(
          'Final Enriched Profile',
          'The final preference profile that can be used by the recommendation system.',
        ),

        const SizedBox(height: 12),

        _buildEnrichedProfileCard(),
      ],
    );
  }

  // =========================================================
  // SECTION HEADING
  // =========================================================

  Widget _buildSectionTitle(
    String title,
    String subtitle,
  ) {
    return Column(
      crossAxisAlignment:
          CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: const TextStyle(
            fontSize: 17,
            fontWeight: FontWeight.bold,
            color: AppTheme.darkTextColor,
          ),
        ),

        const SizedBox(height: 4),

        Text(
          subtitle,
          style: const TextStyle(
            fontSize: 12,
            height: 1.4,
            color: AppTheme.lightTextColor,
          ),
        ),
      ],
    );
  }

  // =========================================================
  // CURRENT PREFERENCE SUMMARY
  // =========================================================

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

  // =========================================================
  // ML EXPANSION CARD
  // =========================================================

  Widget _buildMLExpansionCard() {
    final bool hasMLData =
        _mlColors.isNotEmpty ||
        _mlCategories.isNotEmpty ||
        _mlStyles.isNotEmpty;

    return _buildContainer(
      child: Column(
        crossAxisAlignment:
            CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(
                Icons.psychology_alt_outlined,
                color: AppTheme.primaryColor,
                size: 24,
              ),

              const SizedBox(width: 10),

              const Expanded(
                child: Text(
                  'Model-Added Preferences',
                  style: TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.bold,
                    color: AppTheme.darkTextColor,
                  ),
                ),
              ),

              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 9,
                  vertical: 5,
                ),
                decoration: BoxDecoration(
                  color: const Color(0xFFE8F5F2),
                  borderRadius:
                      BorderRadius.circular(20),
                ),
                child: const Text(
                  'ML',
                  style: TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.bold,
                    color: AppTheme.primaryColor,
                  ),
                ),
              ),
            ],
          ),

          const SizedBox(height: 15),

          if (!hasMLData)
            const Text(
              'No additional ML preferences were added.',
              style: TextStyle(
                fontSize: 13,
                color: AppTheme.lightTextColor,
              ),
            ),

          if (_mlCategories.isNotEmpty)
            _buildMLGroup(
              title: 'Categories',
              items: _mlCategories,
            ),

          if (_mlColors.isNotEmpty)
            _buildMLGroup(
              title: 'Colors',
              items: _mlColors,
            ),

          if (_mlStyles.isNotEmpty)
            _buildMLGroup(
              title: 'Styles',
              items: _mlStyles,
            ),
        ],
      ),
    );
  }

  Widget _buildMLGroup({
    required String title,
    required List<Map<String, dynamic>> items,
  }) {
    return Padding(
      padding: const EdgeInsets.only(
        bottom: 14,
      ),
      child: Column(
        crossAxisAlignment:
            CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: const TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w600,
              color: AppTheme.lightTextColor,
            ),
          ),

          const SizedBox(height: 8),

          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: items.map(
              (item) {
                final String preference =
                    item['preference']
                            ?.toString() ??
                        '';

                return Container(
                  padding:
                      const EdgeInsets.symmetric(
                    horizontal: 11,
                    vertical: 7,
                  ),
                  decoration: BoxDecoration(
                    color:
                        const Color(0xFFE8F5F2),
                    borderRadius:
                        BorderRadius.circular(20),
                    border: Border.all(
                      color:
                          const Color(0xFFB2DFDB),
                    ),
                  ),
                  child: Row(
                    mainAxisSize:
                        MainAxisSize.min,
                    children: [
                      const Icon(
                        Icons.auto_awesome_rounded,
                        size: 14,
                        color:
                            AppTheme.primaryColor,
                      ),

                      const SizedBox(width: 5),

                      Text(
                        preference,
                        style: const TextStyle(
                          fontSize: 12,
                          fontWeight:
                              FontWeight.w600,
                          color:
                              AppTheme.primaryColor,
                        ),
                      ),
                    ],
                  ),
                );
              },
            ).toList(),
          ),
        ],
      ),
    );
  }

  // =========================================================
  // FINAL ENRICHED PROFILE
  // =========================================================

  Widget _buildEnrichedProfileCard() {
    return _buildContainer(
      child: Column(
        crossAxisAlignment:
            CrossAxisAlignment.start,
        children: [
          const Row(
            children: [
              Icon(
                Icons.auto_awesome_rounded,
                color: AppTheme.primaryColor,
                size: 23,
              ),

              SizedBox(width: 9),

              Expanded(
                child: Text(
                  'Final Preference Profile',
                  style: TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.bold,
                    color: AppTheme.darkTextColor,
                  ),
                ),
              ),
            ],
          ),

          const SizedBox(height: 16),

          _buildPreferenceChipGroup(
            title: 'Categories',
            values: _enrichedCategories,
          ),

          _buildPreferenceChipGroup(
            title: 'Colors',
            values: _enrichedColors,
          ),

          _buildPreferenceChipGroup(
            title: 'Styles',
            values: _enrichedStyles,
          ),

          _buildPreferenceChipGroup(
            title: 'Occasions',
            values: _occasions,
          ),

          _buildPreferenceChipGroup(
            title: 'Choice Priorities',
            values: _choicePriorities,
          ),

          _buildPreferenceChipGroup(
            title: 'Preferred Brands',
            values: _preferredBrands,
            showBottomSpacing: false,
          ),
        ],
      ),
    );
  }

  Widget _buildPreferenceChipGroup({
    required String title,
    required List<String> values,
    bool showBottomSpacing = true,
  }) {
    if (values.isEmpty) {
      return const SizedBox.shrink();
    }

    return Padding(
      padding: EdgeInsets.only(
        bottom: showBottomSpacing ? 16 : 0,
      ),
      child: Column(
        crossAxisAlignment:
            CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: const TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w600,
              color: AppTheme.lightTextColor,
            ),
          ),

          const SizedBox(height: 8),

          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: values.map(
              (value) {
                return Container(
                  padding:
                      const EdgeInsets.symmetric(
                    horizontal: 11,
                    vertical: 7,
                  ),
                  decoration: BoxDecoration(
                    color:
                        const Color(0xFFF3F4F6),
                    borderRadius:
                        BorderRadius.circular(20),
                  ),
                  child: Text(
                    value,
                    style: const TextStyle(
                      fontSize: 12,
                      fontWeight:
                          FontWeight.w600,
                      color:
                          AppTheme.darkTextColor,
                    ),
                  ),
                );
              },
            ).toList(),
          ),
        ],
      ),
    );
  }

  // =========================================================
  // COMMON CONTAINER
  // =========================================================

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

  // =========================================================
  // CONVERSION HELPERS
  // =========================================================

  Map<String, dynamic> _toMap(
    dynamic value,
  ) {
    if (value == null) {
      return {};
    }

    if (value is Map<String, dynamic>) {
      return value;
    }

    if (value is Map) {
      return Map<String, dynamic>.from(
        value,
      );
    }

    return {};
  }

  List<Map<String, dynamic>>
      _toListOfMaps(
    dynamic value,
  ) {
    if (value is! List) {
      return [];
    }

    return value
        .whereType<Map>()
        .map(
          (item) =>
              Map<String, dynamic>.from(
            item,
          ),
        )
        .toList();
  }

  List<String> _toStringList(
    dynamic value,
  ) {
    if (value is! List) {
      return [];
    }

    return value
        .map(
          (item) => item.toString(),
        )
        .toList();
  }

  String _getTopValue(
    Map<String, dynamic> scores,
  ) {
    if (scores.isEmpty) {
      return 'Not available';
    }

    final entries =
        scores.entries.toList();

    entries.sort(
      (a, b) => _toDouble(
        b.value,
      ).compareTo(
        _toDouble(
          a.value,
        ),
      ),
    );

    return entries.first.key;
  }
}

// ===========================================================
// CURRENT PREFERENCE SCORE SECTION
// ===========================================================

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

    final entries =
        scores.entries.toList();

    entries.sort(
      (a, b) => _toDouble(
        b.value,
      ).compareTo(
        _toDouble(
          a.value,
        ),
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

// ===========================================================
// SUMMARY ROW
// ===========================================================

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

// ===========================================================
// SCORE ROW
// ===========================================================

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
                  const AlwaysStoppedAnimation<
                      Color>(
                AppTheme.primaryColor,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ===========================================================
// NUMBER HELPER
// ===========================================================

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

  if (value is num) {
    return value.toDouble();
  }

  if (value is String) {
    return double.tryParse(value) ?? 0;
  }

  return 0;
}