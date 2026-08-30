import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:google_fonts/google_fonts.dart';

import 'recommendation_screen.dart';

class PreferenceFilterScreen extends StatefulWidget {
  const PreferenceFilterScreen({super.key});

  @override
  State<PreferenceFilterScreen> createState() => _PreferenceFilterScreenState();
}

class _PreferenceFilterScreenState extends State<PreferenceFilterScreen> {
  final List<String> categories = [
    'Tops',
    'Dresses',
  ];

  final List<String> colors = [
    'Black',
    'White',
    'Red',
    'Blue',
    'Pink',
    'Green',
    'Beige',
    'Grey',
    'Navy',
    'Cream',
  ];

  final List<String> styles = [
    'Casual',
    'Formal',
    'Trendy',
    'Elegant',
    'Party wear',
    'Minimal',
  ];

  final List<String> occasions = [
    'Daily wear',
    'Office / work',
    'University / college',
    'Party',
    'Casual outing',
    'Special events',
  ];

  final List<String> priorities = [
    'Comfort',
    'Style',
    'Trendiness',
    'Price value',
    'Brand',
    'Quality',
    'Easy to match',
    'Occasion suitability',
  ];

  final List<String> brands = [
    'Gflock',
    'Carnage',
    'Kelly Felder',
    'No specific brand',
  ];

  final Set<String> selectedCategories = {'Tops', 'Dresses'};
  final Set<String> selectedColors = {'Black', 'Red'};
  final Set<String> selectedStyles = {'Casual', 'Party wear'};
  final Set<String> selectedOccasions = {'Daily wear', 'Party'};
  final Set<String> selectedPriorities = {'Style', 'Quality'};
  final Set<String> selectedBrands = {'Gflock', 'Carnage', 'Kelly Felder'};

  bool isGenerating = false;

  void _toggleSelection(Set<String> selectedSet, String value) {
    if (isGenerating) return;

    HapticFeedback.selectionClick();

    setState(() {
      if (value == 'No specific brand') {
        selectedSet.clear();
        selectedSet.add(value);
        return;
      }

      if (selectedSet.contains(value)) {
        selectedSet.remove(value);
      } else {
        selectedSet.remove('No specific brand');
        selectedSet.add(value);
      }
    });
  }

  Future<void> _generateRecommendations() async {
    if (isGenerating) return;

    HapticFeedback.mediumImpact();

    if (selectedCategories.isEmpty) {
      _showFeedbackMessage(
        message: 'Please select at least one clothing category.',
        isError: true,
      );
      return;
    }

    if (selectedColors.isEmpty) {
      _showFeedbackMessage(
        message: 'Please select at least one color.',
        isError: true,
      );
      return;
    }

    if (selectedStyles.isEmpty) {
      _showFeedbackMessage(
        message: 'Please select at least one fashion style.',
        isError: true,
      );
      return;
    }

    if (selectedOccasions.isEmpty) {
      _showFeedbackMessage(
        message: 'Please select at least one occasion.',
        isError: true,
      );
      return;
    }

    if (selectedPriorities.isEmpty) {
      _showFeedbackMessage(
        message: 'Please select what matters most when choosing clothes.',
        isError: true,
      );
      return;
    }

    if (selectedBrands.isEmpty) {
      _showFeedbackMessage(
        message: 'Please select at least one brand option.',
        isError: true,
      );
      return;
    }

    setState(() {
      isGenerating = true;
    });

    _showFeedbackMessage(
      message: 'Preparing recommendation preferences...',
    );

    await Future.delayed(const Duration(milliseconds: 1100));

    if (!mounted) return;

    setState(() {
      isGenerating = false;
    });

    _showFeedbackMessage(
      message: 'Preferences applied successfully.',
    );

    await Future.delayed(const Duration(milliseconds: 450));

    if (!mounted) return;

    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => RecommendationScreen(
          selectedCategories: selectedCategories.toList(),
          selectedColors: selectedColors.toList(),
          selectedStyles: selectedStyles.toList(),
          selectedOccasions: selectedOccasions.toList(),
          selectedPriorities: selectedPriorities.toList(),
          selectedBrands: selectedBrands.toList(),
        ),
      ),
    );
  }

  void _showFeedbackMessage({
    required String message,
    bool isError = false,
  }) {
    ScaffoldMessenger.of(context).hideCurrentSnackBar();

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Row(
          children: [
            Icon(
              isError
                  ? Icons.error_outline_rounded
                  : Icons.check_circle_outline_rounded,
              color: Colors.white,
              size: 20,
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Text(
                message,
                style: GoogleFonts.poppins(
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                  color: Colors.white,
                ),
              ),
            ),
          ],
        ),
        backgroundColor:
            isError ? const Color(0xFFEF4444) : const Color(0xFF10231F),
        behavior: SnackBarBehavior.floating,
        margin: const EdgeInsets.all(16),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
        ),
        duration: const Duration(seconds: 2),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF6F7F9),
      body: SafeArea(
        child: Column(
          children: [
            _buildHeader(),
            Expanded(
              child: ListView(
                padding: const EdgeInsets.fromLTRB(22, 12, 22, 120),
                children: [
                  _buildHeroCard(),
                  const SizedBox(height: 16),
                  _buildInlineInfoCard(),
                  const SizedBox(height: 22),
                  _buildSection(
                    title: '1. What clothing categories are you most interested in?',
                    subtitle:
                        'These categories help the engine understand what products to recommend.',
                    options: categories,
                    selectedSet: selectedCategories,
                  ),
                  _buildSection(
                    title: '2. Which colors do you usually like wearing?',
                    subtitle:
                        'Color preferences help match products with your visual style.',
                    options: colors,
                    selectedSet: selectedColors,
                  ),
                  _buildSection(
                    title: '3. What fashion styles match you?',
                    subtitle:
                        'Style preferences support personalized fashion ranking.',
                    options: styles,
                    selectedSet: selectedStyles,
                  ),
                  _buildSection(
                    title: '4. What occasions do you usually dress for?',
                    subtitle:
                        'Occasion context helps future outfit compatibility and recommendation logic.',
                    options: occasions,
                    selectedSet: selectedOccasions,
                  ),
                  _buildSection(
                    title: '5. What matters most when choosing clothes?',
                    subtitle:
                        'This helps the system understand whether to prioritize comfort, trendiness, brand, quality, or matching.',
                    options: priorities,
                    selectedSet: selectedPriorities,
                  ),
                  _buildSection(
                    title: '6. Do you usually prefer specific fashion brands?',
                    subtitle:
                        'Brand preference can directly improve recommendation ranking.',
                    options: brands,
                    selectedSet: selectedBrands,
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
      bottomNavigationBar: _buildBottomButton(),
    );
  }

  Widget _buildHeader() {
    return Padding(
      padding: const EdgeInsets.fromLTRB(18, 12, 18, 10),
      child: Row(
        children: [
          InkWell(
            onTap: isGenerating
                ? null
                : () {
                    HapticFeedback.lightImpact();
                    Navigator.pop(context);
                  },
            borderRadius: BorderRadius.circular(18),
            child: Container(
              height: 42,
              width: 42,
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(16),
              ),
              child: const Icon(
                Icons.arrow_back_ios_new_rounded,
                size: 18,
                color: Color(0xFF111827),
              ),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              'Style Preferences',
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: GoogleFonts.poppins(
                fontSize: 22,
                fontWeight: FontWeight.w800,
                color: const Color(0xFF111827),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildHeroCard() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [
            Color(0xFF073B5A),
            Color(0xFF0E6E9E),
          ],
        ),
        borderRadius: BorderRadius.circular(26),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF073B5A).withOpacity(0.18),
            blurRadius: 22,
            offset: const Offset(0, 10),
          ),
        ],
      ),
      child: Row(
        children: [
          Container(
            height: 58,
            width: 58,
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.16),
              borderRadius: BorderRadius.circular(20),
            ),
            child: const Icon(
              Icons.person_search_rounded,
              color: Colors.white,
              size: 30,
            ),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Build your fashion profile',
                  style: GoogleFonts.poppins(
                    fontSize: 17,
                    fontWeight: FontWeight.w800,
                    color: Colors.white,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  'These choices simulate the preferences that will come from Chala’s onboarding component after integration.',
                  style: GoogleFonts.poppins(
                    fontSize: 12,
                    height: 1.5,
                    color: Colors.white.withOpacity(0.84),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInlineInfoCard() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFFE8F3F8),
        borderRadius: BorderRadius.circular(22),
        border: Border.all(
          color: const Color(0xFF0B5D85).withOpacity(0.15),
        ),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(
            Icons.info_outline_rounded,
            color: Color(0xFF0B5D85),
            size: 22,
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              'This screen contains long-term style preferences. Price range is not asked here because budget changes by situation. Price is added later as a search filter in the recommendation results screen.',
              style: GoogleFonts.poppins(
                fontSize: 12,
                height: 1.45,
                fontWeight: FontWeight.w500,
                color: const Color(0xFF0B5D85),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSection({
    required String title,
    required String subtitle,
    required List<String> options,
    required Set<String> selectedSet,
  }) {
    return Container(
      margin: const EdgeInsets.only(bottom: 18),
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(26),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _sectionTitle(title, subtitle),
          const SizedBox(height: 14),
          Wrap(
            spacing: 10,
            runSpacing: 10,
            children: options.map((option) {
              final bool isSelected = selectedSet.contains(option);

              return InkWell(
                onTap: () => _toggleSelection(selectedSet, option),
                borderRadius: BorderRadius.circular(22),
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 180),
                  padding: const EdgeInsets.symmetric(
                    horizontal: 16,
                    vertical: 11,
                  ),
                  decoration: BoxDecoration(
                    color: isSelected
                        ? const Color(0xFFE8F3F8)
                        : const Color(0xFFF9FAFB),
                    borderRadius: BorderRadius.circular(22),
                    border: Border.all(
                      color: isSelected
                          ? const Color(0xFF0B5D85)
                          : const Color(0xFFE5E7EB),
                      width: isSelected ? 1.4 : 1,
                    ),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      if (isSelected) ...[
                        const Icon(
                          Icons.check_rounded,
                          size: 16,
                          color: Color(0xFF0B5D85),
                        ),
                        const SizedBox(width: 5),
                      ],
                      Text(
                        option,
                        style: GoogleFonts.poppins(
                          fontSize: 13,
                          fontWeight:
                              isSelected ? FontWeight.w800 : FontWeight.w600,
                          color: isSelected
                              ? const Color(0xFF0B5D85)
                              : const Color(0xFF374151),
                        ),
                      ),
                    ],
                  ),
                ),
              );
            }).toList(),
          ),
        ],
      ),
    );
  }

  Widget _sectionTitle(String title, String subtitle) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: GoogleFonts.poppins(
            fontSize: 15.5,
            height: 1.35,
            fontWeight: FontWeight.w800,
            color: const Color(0xFF111827),
          ),
        ),
        const SizedBox(height: 6),
        Text(
          subtitle,
          style: GoogleFonts.poppins(
            fontSize: 12,
            height: 1.45,
            color: const Color(0xFF6B7280),
          ),
        ),
      ],
    );
  }

  Widget _buildBottomButton() {
    return Container(
      padding: const EdgeInsets.fromLTRB(22, 12, 22, 24),
      decoration: BoxDecoration(
        color: const Color(0xFFF6F7F9),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.04),
            blurRadius: 18,
            offset: const Offset(0, -8),
          ),
        ],
      ),
      child: SizedBox(
        height: 58,
        width: double.infinity,
        child: ElevatedButton(
          onPressed: isGenerating ? null : _generateRecommendations,
          style: ElevatedButton.styleFrom(
            backgroundColor:
                isGenerating ? const Color(0xFF9CA3AF) : const Color(0xFF0B5D85),
            foregroundColor: Colors.white,
            disabledBackgroundColor: const Color(0xFF9CA3AF),
            disabledForegroundColor: Colors.white,
            elevation: 0,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(30),
            ),
          ),
          child: isGenerating
              ? Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const SizedBox(
                      height: 18,
                      width: 18,
                      child: CircularProgressIndicator(
                        strokeWidth: 2.2,
                        valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Text(
                      'Preparing...',
                      style: GoogleFonts.poppins(
                        fontSize: 15,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                  ],
                )
              : Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text(
                      'Continue to Recommendations',
                      style: GoogleFonts.poppins(
                        fontSize: 15,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                    const SizedBox(width: 8),
                    const Icon(Icons.arrow_forward_rounded, size: 21),
                  ],
                ),
        ),
      ),
    );
  }
}