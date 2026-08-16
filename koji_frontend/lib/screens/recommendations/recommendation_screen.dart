import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:google_fonts/google_fonts.dart';

import '../../models/recommendation_product_model.dart';
import '../../services/recommendation_api_service.dart';
import '../splash_screen.dart';
import 'product_detail_screen.dart';

class RecommendationScreen extends StatefulWidget {
  final List<String> selectedCategories;
  final List<String> selectedColors;
  final List<String> selectedStyles;
  final List<String> selectedOccasions;
  final List<String> selectedPriorities;
  final List<String> selectedBrands;

  const RecommendationScreen({
    super.key,
    this.selectedCategories = const ['Tops', 'Dresses'],
    this.selectedColors = const ['Black', 'Red'],
    this.selectedStyles = const ['Casual', 'Party wear'],
    this.selectedOccasions = const ['Daily wear', 'Party'],
    this.selectedPriorities = const ['Style', 'Quality'],
    this.selectedBrands = const ['Gflock', 'Carnage'],
  });

  @override
  State<RecommendationScreen> createState() => _RecommendationScreenState();
}

class _RecommendationScreenState extends State<RecommendationScreen> {
  final RecommendationApiService _apiService = RecommendationApiService();

  bool isLoading = true;
  bool isAppliedPreferencesExpanded = false;
  bool isSearchFiltersExpanded = false;
  bool isPriceFilterEnabled = false;

  String? errorMessage;

  double minPrice = 1000;
  double maxPrice = 20000;

  int maxResults = 15;
  String selectedQuickStyle = 'All';

  List<RecommendationProduct> apiProducts = [];

  @override
  void initState() {
    super.initState();
    _loadRecommendations();
  }

  Future<void> _loadRecommendations() async {
    setState(() {
      isLoading = true;
      errorMessage = null;
    });

    try {
      final List<RecommendationProduct> products =
          await _apiService.getRecommendations(
        userId: 'U001',
        preferredCategories: widget.selectedCategories,
        preferredColors: widget.selectedColors,
        preferredStyles: widget.selectedStyles,
        preferredBrands: widget.selectedBrands,
        priceMin: isPriceFilterEnabled ? minPrice : 0,
        priceMax: isPriceFilterEnabled ? maxPrice : 999999,
        maxResults: 15,
      );

      if (!mounted) return;

      setState(() {
        apiProducts = products;
        isLoading = false;
      });

      _showFeedbackMessage('Recommendations loaded successfully.');
    } catch (error) {
      if (!mounted) return;

      setState(() {
        isLoading = false;
        errorMessage =
            'Could not load recommendations. Please check backend connection.';
      });
    }
  }

  List<Map<String, dynamic>> get filteredProducts {
    final bool hasSpecificBrand =
        !widget.selectedBrands.contains('No specific brand');

    final List<Map<String, dynamic>> mappedProducts = apiProducts
        .map((product) => product.toProductDetailMap())
        .where((product) {
      final int productPrice = product['priceValue'] ?? 0;

      final bool matchesPrice = isPriceFilterEnabled
          ? productPrice >= minPrice.round() &&
              productPrice <= maxPrice.round()
          : true;

      final bool matchesCategory =
          _matchesSelectedCategory(product['category'] ?? '');

      final bool matchesBrand = hasSpecificBrand
          ? widget.selectedBrands
              .map((brand) => brand.toLowerCase())
              .contains((product['brand'] ?? '').toString().toLowerCase())
          : true;

      final bool matchesQuickStyle = selectedQuickStyle == 'All'
          ? true
          : _normalizeStyle(product['style'] ?? '') ==
              _normalizeStyle(selectedQuickStyle);

      return matchesPrice &&
          matchesCategory &&
          matchesBrand &&
          matchesQuickStyle;
    }).toList();

    return mappedProducts.take(maxResults).toList();
  }

  bool _matchesSelectedCategory(String productCategory) {
    final String normalizedProductCategory = _normalizeCategory(productCategory);

    final List<String> selected = widget.selectedCategories
        .map((category) => _normalizeCategory(category))
        .toList();

    return selected.contains(normalizedProductCategory);
  }

  String _normalizeCategory(String value) {
    final String normalized = value.trim().toLowerCase();

    if (normalized.contains('dress')) return 'dress';
    if (normalized.contains('top')) return 'top';

    return normalized;
  }

  String _normalizeStyle(String value) {
    final String normalized = value.trim().toLowerCase();

    if (normalized.contains('party')) return 'party';
    if (normalized.contains('casual')) return 'casual';
    if (normalized.contains('formal')) return 'formal';
    if (normalized.contains('trendy')) return 'trendy';
    if (normalized.contains('elegant')) return 'elegant';
    if (normalized.contains('minimal')) return 'minimal';

    return normalized;
  }

  void _showFeedbackMessage(String message) {
    ScaffoldMessenger.of(context).hideCurrentSnackBar();

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Row(
          children: [
            const Icon(
              Icons.check_circle_outline_rounded,
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
        backgroundColor: const Color(0xFF10231F),
        behavior: SnackBarBehavior.floating,
        margin: const EdgeInsets.all(16),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
        ),
        duration: const Duration(seconds: 2),
      ),
    );
  }

  void _changeQuickStyle(String style) {
    HapticFeedback.selectionClick();

    setState(() {
      selectedQuickStyle = style;
    });

    _showFeedbackMessage(
      style == 'All'
          ? 'Showing all matching styles.'
          : 'Showing $style style recommendations.',
    );
  }

  void _goToSplashScreen() {
    HapticFeedback.lightImpact();

    Navigator.pushAndRemoveUntil(
      context,
      MaterialPageRoute(
        builder: (context) => const SplashScreen(),
      ),
      (route) => false,
    );
  }

  void _toggleAppliedPreferences() {
    HapticFeedback.selectionClick();

    setState(() {
      isAppliedPreferencesExpanded = !isAppliedPreferencesExpanded;
    });
  }

  void _toggleSearchFilters() {
    HapticFeedback.selectionClick();

    setState(() {
      isSearchFiltersExpanded = !isSearchFiltersExpanded;
    });
  }

  void _togglePriceFilter(bool value) {
    HapticFeedback.selectionClick();

    setState(() {
      isPriceFilterEnabled = value;
    });

    _showFeedbackMessage(
      value
          ? 'Price range filter enabled.'
          : 'Price range filter disabled. Showing any price.',
    );
  }

  @override
  Widget build(BuildContext context) {
    final List<Map<String, dynamic>> visibleProducts = filteredProducts;

    return Scaffold(
      backgroundColor: const Color(0xFFF6F7F9),
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: _loadRecommendations,
          color: const Color(0xFF0B5D85),
          child: ListView(
            padding: const EdgeInsets.fromLTRB(18, 14, 18, 24),
            children: [
              _buildHeader(),
              const SizedBox(height: 18),
              _buildStatusCard(),
              const SizedBox(height: 18),
              _buildAppliedPreferencesCard(),
              const SizedBox(height: 18),
              _buildSearchFiltersCard(),
              const SizedBox(height: 20),
              _buildExploreStyles(),
              const SizedBox(height: 22),
              _buildSectionTitle(visibleProducts.length),
              const SizedBox(height: 14),
              if (isLoading)
                _buildLoadingState()
              else if (errorMessage != null)
                _buildErrorState()
              else if (visibleProducts.isEmpty)
                _buildEmptyState()
              else
                _buildProductGrid(visibleProducts),
            ],
          ),
        ),
      ),
      bottomNavigationBar: _buildBottomNav(),
    );
  }

  Widget _buildHeader() {
    return Row(
      children: [
        InkWell(
          onTap: _goToSplashScreen,
          borderRadius: BorderRadius.circular(16),
          child: Row(
            children: [
              Container(
                height: 42,
                width: 42,
                decoration: BoxDecoration(
                  color: const Color(0xFF0B5D85),
                  borderRadius: BorderRadius.circular(14),
                ),
                child: const Icon(
                  Icons.auto_awesome_rounded,
                  color: Colors.white,
                  size: 23,
                ),
              ),
              const SizedBox(width: 10),
              Text(
                'OutfitIQ',
                style: GoogleFonts.poppins(
                  fontSize: 23,
                  fontWeight: FontWeight.w800,
                  color: const Color(0xFF111827),
                ),
              ),
            ],
          ),
        ),
        const Spacer(),
        InkWell(
          onTap: () {
            HapticFeedback.lightImpact();
            Navigator.pop(context);
          },
          borderRadius: BorderRadius.circular(16),
          child: _circleIcon(Icons.tune_rounded),
        ),
      ],
    );
  }

  Widget _circleIcon(IconData icon) {
    return Container(
      height: 42,
      width: 42,
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
      ),
      child: Icon(
        icon,
        color: const Color(0xFF111827),
        size: 21,
      ),
    );
  }

  Widget _buildStatusCard() {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(24),
        gradient: const LinearGradient(
          colors: [
            Color(0xFF073B5A),
            Color(0xFF0E6E9E),
          ],
        ),
      ),
      child: Row(
        children: [
          Container(
            height: 52,
            width: 52,
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.16),
              borderRadius: BorderRadius.circular(18),
            ),
            child: Icon(
              isLoading
                  ? Icons.hourglass_top_rounded
                  : Icons.recommend_rounded,
              color: Colors.white,
              size: 28,
            ),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  isLoading
                      ? 'Generating recommendations...'
                      : 'Smart recommendations generated',
                  style: GoogleFonts.poppins(
                    fontSize: 16,
                    fontWeight: FontWeight.w800,
                    color: Colors.white,
                  ),
                ),
                const SizedBox(height: 5),
                Text(
                  'Results are loaded from your FastAPI recommendation backend.',
                  style: GoogleFonts.poppins(
                    fontSize: 11.5,
                    height: 1.4,
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

  Widget _buildAppliedPreferencesCard() {
    final String summaryText =
        '${widget.selectedCategories.join(', ')} • ${widget.selectedColors.join(', ')} • ${widget.selectedStyles.join(', ')}';

    return AnimatedContainer(
      duration: const Duration(milliseconds: 220),
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(24),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          InkWell(
            onTap: _toggleAppliedPreferences,
            borderRadius: BorderRadius.circular(16),
            child: Row(
              children: [
                const Icon(
                  Icons.fact_check_rounded,
                  size: 20,
                  color: Color(0xFF0B5D85),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'Applied style preferences',
                    style: GoogleFonts.poppins(
                      fontSize: 16,
                      fontWeight: FontWeight.w800,
                      color: const Color(0xFF111827),
                    ),
                  ),
                ),
                AnimatedRotation(
                  turns: isAppliedPreferencesExpanded ? 0.5 : 0,
                  duration: const Duration(milliseconds: 220),
                  child: const Icon(
                    Icons.keyboard_arrow_down_rounded,
                    color: Color(0xFF111827),
                    size: 26,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 8),
          Text(
            summaryText,
            maxLines: isAppliedPreferencesExpanded ? 3 : 1,
            overflow: TextOverflow.ellipsis,
            style: GoogleFonts.poppins(
              fontSize: 12,
              fontWeight: FontWeight.w600,
              color: const Color(0xFF6B7280),
            ),
          ),
          AnimatedCrossFade(
            firstChild: const SizedBox.shrink(),
            secondChild: _buildExpandedAppliedPreferences(),
            crossFadeState: isAppliedPreferencesExpanded
                ? CrossFadeState.showSecond
                : CrossFadeState.showFirst,
            duration: const Duration(milliseconds: 220),
          ),
        ],
      ),
    );
  }

  Widget _buildExpandedAppliedPreferences() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SizedBox(height: 14),
        _summaryRow('Categories', widget.selectedCategories),
        _summaryRow('Colors', widget.selectedColors),
        _summaryRow('Styles', widget.selectedStyles),
        _summaryRow('Occasions', widget.selectedOccasions),
        _summaryRow('Priority', widget.selectedPriorities),
        _summaryRow('Brands', widget.selectedBrands),
      ],
    );
  }

  Widget _buildSearchFiltersCard() {
    return AnimatedContainer(
      duration: const Duration(milliseconds: 220),
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(24),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          InkWell(
            onTap: _toggleSearchFilters,
            borderRadius: BorderRadius.circular(16),
            child: Row(
              children: [
                const Icon(
                  Icons.filter_alt_rounded,
                  size: 20,
                  color: Color(0xFF0B5D85),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'Current search filters',
                    style: GoogleFonts.poppins(
                      fontSize: 16,
                      fontWeight: FontWeight.w800,
                      color: const Color(0xFF111827),
                    ),
                  ),
                ),
                AnimatedRotation(
                  turns: isSearchFiltersExpanded ? 0.5 : 0,
                  duration: const Duration(milliseconds: 220),
                  child: const Icon(
                    Icons.keyboard_arrow_down_rounded,
                    color: Color(0xFF111827),
                    size: 26,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 8),
          Text(
            isPriceFilterEnabled
                ? 'LKR ${minPrice.round()} - LKR ${maxPrice.round()} • $maxResults maximum results'
                : 'Any price • $maxResults maximum results',
            style: GoogleFonts.poppins(
              fontSize: 12,
              fontWeight: FontWeight.w600,
              color: const Color(0xFF6B7280),
            ),
          ),
          AnimatedCrossFade(
            firstChild: const SizedBox.shrink(),
            secondChild: _buildExpandedSearchFilters(),
            crossFadeState: isSearchFiltersExpanded
                ? CrossFadeState.showSecond
                : CrossFadeState.showFirst,
            duration: const Duration(milliseconds: 220),
          ),
        ],
      ),
    );
  }

  Widget _buildExpandedSearchFilters() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SizedBox(height: 18),
        Text(
          'Price range is optional and only used for the current search. It is not saved as a permanent onboarding preference.',
          style: GoogleFonts.poppins(
            fontSize: 12,
            height: 1.4,
            color: const Color(0xFF6B7280),
          ),
        ),
        const SizedBox(height: 14),
        InkWell(
          onTap: () => _togglePriceFilter(!isPriceFilterEnabled),
          borderRadius: BorderRadius.circular(18),
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 13),
            decoration: BoxDecoration(
              color: isPriceFilterEnabled
                  ? const Color(0xFFE8F3F8)
                  : const Color(0xFFF9FAFB),
              borderRadius: BorderRadius.circular(18),
              border: Border.all(
                color: isPriceFilterEnabled
                    ? const Color(0xFF0B5D85)
                    : const Color(0xFFE5E7EB),
              ),
            ),
            child: Row(
              children: [
                Icon(
                  isPriceFilterEnabled
                      ? Icons.check_circle_rounded
                      : Icons.radio_button_unchecked_rounded,
                  color: isPriceFilterEnabled
                      ? const Color(0xFF0B5D85)
                      : const Color(0xFF9CA3AF),
                  size: 20,
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    isPriceFilterEnabled
                        ? 'Price range filter enabled'
                        : 'Any price selected by default',
                    style: GoogleFonts.poppins(
                      fontSize: 13,
                      fontWeight: FontWeight.w700,
                      color: isPriceFilterEnabled
                          ? const Color(0xFF0B5D85)
                          : const Color(0xFF374151),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
        if (isPriceFilterEnabled) ...[
          const SizedBox(height: 16),
          Row(
            children: [
              _priceBox('Min', 'LKR ${minPrice.round()}'),
              const SizedBox(width: 12),
              _priceBox('Max', 'LKR ${maxPrice.round()}'),
            ],
          ),
          const SizedBox(height: 14),
          RangeSlider(
            min: 1000,
            max: 20000,
            divisions: 19,
            activeColor: const Color(0xFF0B5D85),
            inactiveColor: const Color(0xFFE5E7EB),
            values: RangeValues(minPrice, maxPrice),
            onChanged: (values) {
              HapticFeedback.selectionClick();

              setState(() {
                minPrice = values.start;
                maxPrice = values.end;
              });
            },
          ),
        ],
        const SizedBox(height: 18),
        Text(
          'Maximum results',
          style: GoogleFonts.poppins(
            fontSize: 13,
            fontWeight: FontWeight.w800,
            color: const Color(0xFF111827),
          ),
        ),
        const SizedBox(height: 6),
        Text(
          'The highest option is selected by default to show more recommended products.',
          style: GoogleFonts.poppins(
            fontSize: 11.5,
            height: 1.4,
            color: const Color(0xFF6B7280),
          ),
        ),
        const SizedBox(height: 12),
        Row(
          children: [5, 10, 15].map((value) {
            final bool isSelected = maxResults == value;
            final bool isLast = value == 15;

            return Expanded(
              child: Padding(
                padding: EdgeInsets.only(right: isLast ? 0 : 10),
                child: InkWell(
                  onTap: () {
                    HapticFeedback.selectionClick();

                    setState(() {
                      maxResults = value;
                    });

                    _showFeedbackMessage(
                      'Showing up to $value recommendations.',
                    );
                  },
                  borderRadius: BorderRadius.circular(18),
                  child: AnimatedContainer(
                    duration: const Duration(milliseconds: 180),
                    padding: const EdgeInsets.symmetric(vertical: 13),
                    decoration: BoxDecoration(
                      color: isSelected
                          ? const Color(0xFFE8F3F8)
                          : const Color(0xFFF9FAFB),
                      borderRadius: BorderRadius.circular(18),
                      border: Border.all(
                        color: isSelected
                            ? const Color(0xFF0B5D85)
                            : const Color(0xFFE5E7EB),
                      ),
                    ),
                    child: Center(
                      child: Text(
                        value == 15 ? '15 Max' : value.toString(),
                        style: GoogleFonts.poppins(
                          fontSize: 14,
                          fontWeight: FontWeight.w800,
                          color: isSelected
                              ? const Color(0xFF0B5D85)
                              : const Color(0xFF374151),
                        ),
                      ),
                    ),
                  ),
                ),
              ),
            );
          }).toList(),
        ),
      ],
    );
  }

  Widget _buildExploreStyles() {
    final List<String> quickStyles = [
      'All',
      'Casual',
      'Formal',
      'Trendy',
      'Elegant',
      'Party wear',
      'Minimal',
    ];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Explore styles',
          style: GoogleFonts.poppins(
            fontSize: 18,
            fontWeight: FontWeight.w800,
            color: const Color(0xFF111827),
          ),
        ),
        const SizedBox(height: 12),
        SizedBox(
          height: 42,
          child: ListView.separated(
            scrollDirection: Axis.horizontal,
            itemCount: quickStyles.length,
            separatorBuilder: (context, index) => const SizedBox(width: 10),
            itemBuilder: (context, index) {
              final String style = quickStyles[index];
              final bool isSelected = selectedQuickStyle == style;

              return InkWell(
                onTap: () => _changeQuickStyle(style),
                borderRadius: BorderRadius.circular(22),
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 180),
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  decoration: BoxDecoration(
                    color: isSelected
                        ? const Color(0xFF0B5D85)
                        : Colors.white,
                    borderRadius: BorderRadius.circular(22),
                    border: Border.all(
                      color: isSelected
                          ? const Color(0xFF0B5D85)
                          : const Color(0xFFE5E7EB),
                    ),
                  ),
                  child: Center(
                    child: Text(
                      style,
                      style: GoogleFonts.poppins(
                        fontSize: 13,
                        fontWeight: FontWeight.w700,
                        color:
                            isSelected ? Colors.white : const Color(0xFF374151),
                      ),
                    ),
                  ),
                ),
              );
            },
          ),
        ),
      ],
    );
  }

  Widget _buildSectionTitle(int count) {
    return Row(
      children: [
        Text(
          'Recommended For You',
          style: GoogleFonts.poppins(
            fontSize: 18,
            fontWeight: FontWeight.w800,
            color: const Color(0xFF111827),
          ),
        ),
        const Spacer(),
        Text(
          isLoading ? 'Loading...' : '$count results',
          style: GoogleFonts.poppins(
            fontSize: 12,
            fontWeight: FontWeight.w600,
            color: const Color(0xFF0B5D85),
          ),
        ),
      ],
    );
  }

  Widget _buildProductGrid(List<Map<String, dynamic>> visibleProducts) {
    return GridView.builder(
      itemCount: visibleProducts.length,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 2,
        crossAxisSpacing: 14,
        mainAxisSpacing: 16,
        childAspectRatio: 0.63,
      ),
      itemBuilder: (context, index) {
        final product = visibleProducts[index];

        return InkWell(
          onTap: () {
            HapticFeedback.lightImpact();

            Navigator.push(
              context,
              MaterialPageRoute(
                builder: (context) => ProductDetailScreen(product: product),
              ),
            );
          },
          borderRadius: BorderRadius.circular(22),
          child: Container(
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(22),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Stack(
                    children: [
                      ClipRRect(
                        borderRadius: const BorderRadius.vertical(
                          top: Radius.circular(22),
                        ),
                        child: CachedNetworkImage(
                          imageUrl: product['image'],
                          width: double.infinity,
                          height: double.infinity,
                          fit: BoxFit.cover,
                          placeholder: (context, url) => Container(
                            color: const Color(0xFFE5E7EB),
                            child: const Center(
                              child: CircularProgressIndicator(strokeWidth: 2),
                            ),
                          ),
                          errorWidget: (context, url, error) => Container(
                            color: const Color(0xFFE5E7EB),
                            child: const Icon(Icons.image_not_supported),
                          ),
                        ),
                      ),
                      Positioned(
                        top: 10,
                        right: 10,
                        child: Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 9,
                            vertical: 5,
                          ),
                          decoration: BoxDecoration(
                            color: Colors.black.withOpacity(0.65),
                            borderRadius: BorderRadius.circular(14),
                          ),
                          child: Text(
                            product['match'],
                            style: GoogleFonts.poppins(
                              color: Colors.white,
                              fontSize: 11,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                Padding(
                  padding: const EdgeInsets.fromLTRB(12, 10, 12, 12),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        product['title'],
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: GoogleFonts.poppins(
                          fontSize: 13,
                          fontWeight: FontWeight.w700,
                          color: const Color(0xFF111827),
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        '${product['brand']} • ${product['category']}',
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: GoogleFonts.poppins(
                          fontSize: 11,
                          color: const Color(0xFF6B7280),
                        ),
                      ),
                      const SizedBox(height: 6),
                      Text(
                        product['price'],
                        style: GoogleFonts.poppins(
                          fontSize: 13,
                          fontWeight: FontWeight.w800,
                          color: const Color(0xFF0B5D85),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildLoadingState() {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(24),
      ),
      child: Column(
        children: [
          const CircularProgressIndicator(
            color: Color(0xFF0B5D85),
            strokeWidth: 2.5,
          ),
          const SizedBox(height: 16),
          Text(
            'Loading recommendations from backend...',
            textAlign: TextAlign.center,
            style: GoogleFonts.poppins(
              fontSize: 13,
              fontWeight: FontWeight.w600,
              color: const Color(0xFF6B7280),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildErrorState() {
    return Container(
      padding: const EdgeInsets.all(22),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(24),
      ),
      child: Column(
        children: [
          const Icon(
            Icons.wifi_off_rounded,
            size: 42,
            color: Color(0xFFEF4444),
          ),
          const SizedBox(height: 12),
          Text(
            'Backend connection failed',
            style: GoogleFonts.poppins(
              fontSize: 16,
              fontWeight: FontWeight.w800,
              color: const Color(0xFF111827),
            ),
          ),
          const SizedBox(height: 6),
          Text(
            errorMessage ?? 'Could not load recommendations.',
            textAlign: TextAlign.center,
            style: GoogleFonts.poppins(
              fontSize: 12,
              height: 1.5,
              color: const Color(0xFF6B7280),
            ),
          ),
          const SizedBox(height: 16),
          SizedBox(
            height: 44,
            child: ElevatedButton(
              onPressed: _loadRecommendations,
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF0B5D85),
                foregroundColor: Colors.white,
                elevation: 0,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(22),
                ),
              ),
              child: Text(
                'Try Again',
                style: GoogleFonts.poppins(
                  fontSize: 13,
                  fontWeight: FontWeight.w800,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildEmptyState() {
    return Container(
      padding: const EdgeInsets.all(22),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(24),
      ),
      child: Column(
        children: [
          const Icon(
            Icons.search_off_rounded,
            size: 42,
            color: Color(0xFF9CA3AF),
          ),
          const SizedBox(height: 12),
          Text(
            'No matching products found',
            style: GoogleFonts.poppins(
              fontSize: 16,
              fontWeight: FontWeight.w800,
              color: const Color(0xFF111827),
            ),
          ),
          const SizedBox(height: 6),
          Text(
            'Try changing the price range, brand, category, or quick style filter.',
            textAlign: TextAlign.center,
            style: GoogleFonts.poppins(
              fontSize: 12,
              height: 1.5,
              color: const Color(0xFF6B7280),
            ),
          ),
        ],
      ),
    );
  }

  Widget cardTitle({
    required IconData icon,
    required String title,
  }) {
    return Row(
      children: [
        Icon(
          icon,
          size: 20,
          color: const Color(0xFF0B5D85),
        ),
        const SizedBox(width: 8),
        Text(
          title,
          style: GoogleFonts.poppins(
            fontSize: 16,
            fontWeight: FontWeight.w800,
            color: const Color(0xFF111827),
          ),
        ),
      ],
    );
  }

  Widget _summaryRow(String label, List<String> values) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 9),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 92,
            child: Text(
              label,
              style: GoogleFonts.poppins(
                fontSize: 12,
                color: const Color(0xFF6B7280),
              ),
            ),
          ),
          Expanded(
            child: Text(
              values.join(', '),
              style: GoogleFonts.poppins(
                fontSize: 12,
                fontWeight: FontWeight.w700,
                color: const Color(0xFF111827),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _priceBox(String label, String value) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 13),
        decoration: BoxDecoration(
          color: const Color(0xFFF9FAFB),
          borderRadius: BorderRadius.circular(18),
          border: Border.all(
            color: const Color(0xFFE5E7EB),
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              label,
              style: GoogleFonts.poppins(
                fontSize: 11,
                fontWeight: FontWeight.w600,
                color: const Color(0xFF6B7280),
              ),
            ),
            const SizedBox(height: 4),
            Text(
              value,
              style: GoogleFonts.poppins(
                fontSize: 14,
                fontWeight: FontWeight.w800,
                color: const Color(0xFF111827),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildBottomNav() {
    return Container(
      height: 72,
      margin: const EdgeInsets.fromLTRB(18, 0, 18, 18),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(28),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.06),
            blurRadius: 20,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: const Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          Icon(Icons.home_rounded, color: Color(0xFF0B5D85)),
          Icon(Icons.favorite_border_rounded, color: Color(0xFF9CA3AF)),
          Icon(Icons.shopping_bag_outlined, color: Color(0xFF9CA3AF)),
          Icon(Icons.person_outline_rounded, color: Color(0xFF9CA3AF)),
        ],
      ),
    );
  }
}