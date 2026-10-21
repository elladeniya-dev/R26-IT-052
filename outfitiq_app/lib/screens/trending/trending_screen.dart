import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';

import '../../core/responsive.dart';
import '../../models/recommendation_product_model.dart';
import '../../providers/auth_provider.dart';
import '../../services/recommendation_api_service.dart';
import '../../services/trend_api_service.dart';
import '../recommendations/product_detail_screen.dart';
import 'trend_matching.dart';

/// Trending products: real Koji catalog items (the only allowed product
/// source), personalized to the signed-in user's Chala preferences via
/// Koji's existing /recommendations/from-chala endpoint, then scored by
/// Givi's trend engine.
///
/// A cloth counts as trending only when it carries both parts of a rising
/// attribute combination (for example white AND dress), as decided by the
/// engine. One rising attribute, such as white, never makes a cloth trending.
///
/// Deliberately never touches Givi's own product database — that
/// catalog exists only to feed Givi's trend-scoring analysis, not to
/// be shown to end users.
class TrendingScreen extends StatefulWidget {
  const TrendingScreen({super.key});

  @override
  State<TrendingScreen> createState() => _TrendingScreenState();
}

class _TrendingScreenState extends State<TrendingScreen> {
  final RecommendationApiService _recommendationService =
      RecommendationApiService();
  final TrendApiService _trendService = TrendApiService();

  // How many rising combinations the "What is trending" strip lists.
  static const int _maxSegmentChips = 12;

  // Confidence sections the user expanded with "Show all".
  final Set<String> _expandedLevels = {};

  bool isLoading = true;
  String? errorMessage;
  List<ConfidenceSection> personalSections = [];
  List<TrendSegment> topSegments = [];

  // Personalized (Chala-matched) is the default view. The catalog-wide
  // view is lazy-loaded only when the user actually asks for it.
  bool showPersonalized = true;
  bool isLoadingOverall = false;
  String? overallErrorMessage;
  List<ConfidenceSection> overallSections = [];

  @override
  void initState() {
    super.initState();
    _loadTrendingProducts();
  }

  Future<void> _loadTrendingProducts() async {
    setState(() {
      isLoading = true;
      errorMessage = null;
    });

    final int? userId =
        Provider.of<AuthProvider>(context, listen: false).currentUser?.userId;

    if (userId == null) {
      setState(() {
        isLoading = false;
        errorMessage = 'You need to be signed in to see trending picks.';
      });
      return;
    }

    try {
      final results = await Future.wait([
        _recommendationService.getRecommendationsFromChala(
          userId: userId,
          priceMin: 0,
          priceMax: 999999,
          maxResults: 50,
        ),
        _trendService.getTrendingSegments(),
      ]);

      final List<RecommendationProduct> recommended =
          results[0] as List<RecommendationProduct>;
      final List<TrendSegment> segments = results[1] as List<TrendSegment>;

      final Map<String, ProductTrend> trends = await _trendService
          .scoreProducts([for (final p in recommended) trendScoringPayload(p)]);

      if (!mounted) return;

      setState(() {
        personalSections = sectionsFromTrends(recommended, trends);
        topSegments = segments.take(_maxSegmentChips).toList();
        isLoading = false;
      });
    } catch (error) {
      if (!mounted) return;

      setState(() {
        isLoading = false;
        errorMessage =
            'Could not load trending picks. Please check your connection '
            'and try again.';
      });
    }
  }

  // Catalog-wide trending: same trend scoring, but run against Koji's full
  // available catalog (GET /products/) instead of this user's Chala-
  // personalized recommendations. Still only ever a real Koji product —
  // same rule as the personalized view.
  Future<void> _loadOverallTrending() async {
    setState(() {
      isLoadingOverall = true;
      overallErrorMessage = null;
    });

    final int? userId =
        Provider.of<AuthProvider>(context, listen: false).currentUser?.userId;

    try {
      final results = await Future.wait([
        _recommendationService.getAllProducts(),
        _trendService.getTrendingSegments(),
        _fetchScoreLookup(userId),
      ]);

      final List<RecommendationProduct> allProducts =
          results[0] as List<RecommendationProduct>;
      final List<TrendSegment> segments = results[1] as List<TrendSegment>;
      final Map<String, RecommendationProduct> scores =
          results[2] as Map<String, RecommendationProduct>;

      final Map<String, ProductTrend> trends = await _trendService.scoreProducts(
          [for (final p in allProducts) trendScoringPayload(p)]);

      if (!mounted) return;

      setState(() {
        overallSections = sectionsFromTrends(
          allProducts,
          trends,
          cardFor: (product) => _overallCard(product, scores[product.itemId]),
        );
        topSegments = segments.take(_maxSegmentChips).toList();
        isLoadingOverall = false;
      });
    } catch (error) {
      if (!mounted) return;

      setState(() {
        isLoadingOverall = false;
        overallErrorMessage =
            'Could not load catalog-wide trending picks. Please check your '
            'connection and try again.';
      });
    }
  }

  Map<String, dynamic> _overallCard(
    RecommendationProduct product,
    RecommendationProduct? scored,
  ) {
    final Map<String, dynamic> card = (scored ?? product).toProductDetailMap();
    if (scored != null) {
      // Koji scored this cloth for the user: keep its real reasons.
      card['tags'] = [...scored.reasonTags, 'Trending across the whole catalog'];
    } else {
      // Koji did not score it (below its relevance bar), so say so instead of
      // letting generic fallback tags imply a match, and let the detail screen
      // show dashes rather than 0%.
      card['tags'] = [
        'Trending across the whole catalog',
        'Not scored against your profile',
      ];
      card['scoresAvailable'] = false;
    }
    return card;
  }

  // The plain catalog list (GET /products/) carries no scores: Koji only
  // scores products against a signed-in user's profile. So the catalog-wide
  // view makes one extra scoring call over the whole catalog and attaches the
  // result to every cloth. Items below Koji's relevance bar come back
  // unscored and show dashes instead of a made-up number.
  Future<Map<String, RecommendationProduct>> _fetchScoreLookup(
    int? userId,
  ) async {
    if (userId == null) return {};

    try {
      final List<RecommendationProduct> scored =
          await _recommendationService.getRecommendationsFromChala(
        userId: userId,
        priceMin: 0,
        priceMax: 999999,
        maxResults: 500,
      );

      return {for (final product in scored) product.itemId: product};
    } catch (_) {
      // Scores are a nice-to-have here; the trend shelves still load.
      return {};
    }
  }

  void _toggleMode() {
    HapticFeedback.selectionClick();

    setState(() {
      showPersonalized = !showPersonalized;
    });

    // Refetch every time the user switches tabs, not just the first
    // time — trending signals and confidence are meant to feel live,
    // and this screen can realistically stay open (toggling back and
    // forth) across a recompute run on the backend. Only guarded by
    // isLoading so a rapid double-toggle doesn't fire overlapping
    // requests for the same tab.
    if (showPersonalized && !isLoading) {
      _loadTrendingProducts();
    } else if (!showPersonalized && !isLoadingOverall) {
      _loadOverallTrending();
    }
  }

  String _capitalizeTrendLabel(String value) {
    if (value.isEmpty) return value;

    return value
        .split(' ')
        .map((word) => word.isEmpty
            ? word
            : '${word[0].toUpperCase()}${word.substring(1)}')
        .join(' ');
  }

  @override
  Widget build(BuildContext context) {
    final bool loading = showPersonalized ? isLoading : isLoadingOverall;
    final String? currentError =
        showPersonalized ? errorMessage : overallErrorMessage;
    final List<ConfidenceSection> sections =
        showPersonalized ? personalSections : overallSections;
    final int pickCount =
        sections.fold<int>(0, (total, section) => total + section.products.length);
    final Future<void> Function() currentLoader =
        showPersonalized ? _loadTrendingProducts : _loadOverallTrending;

    return Scaffold(
      backgroundColor: const Color(0xFFF6F7F9),
      body: SafeArea(
        child: ResponsiveCenter(
          maxWidth: 1400,
          // Lets a mouse or trackpad drag the sideways rows (the trend chips
          // and the product shelves). By default only touch can, so on
          // desktop/web those rows looked stuck.
          child: ScrollConfiguration(
            behavior: ScrollConfiguration.of(context).copyWith(
              dragDevices: {
                PointerDeviceKind.touch,
                PointerDeviceKind.mouse,
                PointerDeviceKind.trackpad,
                PointerDeviceKind.stylus,
              },
            ),
            child: RefreshIndicator(
            onRefresh: currentLoader,
            color: const Color(0xFF0B5D85),
            child: ListView(
              padding: const EdgeInsets.fromLTRB(18, 14, 18, 24),
              children: [
                _buildHeader(context),
                const SizedBox(height: 18),
                _buildStatusCard(loading: loading),
                if (!loading && currentError == null && topSegments.isNotEmpty) ...[
                  const SizedBox(height: 18),
                  _buildTrendingAttributesSection(),
                ],
                const SizedBox(height: 18),
                _buildModeToggleButton(),
                const SizedBox(height: 22),
                _buildSectionTitle(pickCount, loading: loading),
                const SizedBox(height: 14),
                if (loading)
                  _buildLoadingState()
                else if (currentError != null)
                  _buildErrorState(currentError, currentLoader)
                else if (sections.isEmpty)
                  _buildEmptyState()
                else
                  _buildConfidenceSections(sections),
              ],
            ),
          ),
          ),
        ),
      ),
    );
  }

  // On = trends matched to the signed-in user's preferences (default).
  // Off = trends across Koji's whole catalog. The switch is disabled while
  // either view is loading so a quick double-flip can't leave the screen
  // showing one mode's data under the other mode's label.
  Widget _buildModeToggleButton() {
    final bool busy = isLoading || isLoadingOverall;

    return Semantics(
      container: true,
      toggled: showPersonalized,
      label: 'Personalized trends',
      child: Material(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        child: InkWell(
          borderRadius: BorderRadius.circular(20),
          onTap: busy ? null : _toggleMode,
          child: Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 10, 12),
            child: Row(
              children: [
                Icon(
                  showPersonalized
                      ? Icons.person_rounded
                      : Icons.public_rounded,
                  size: 22,
                  color: const Color(0xFF0B5D85),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Personalized for you',
                        style: GoogleFonts.poppins(
                          fontSize: 14,
                          fontWeight: FontWeight.w700,
                          color: const Color(0xFF111827),
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        showPersonalized
                            ? 'Matched to your style and preferences'
                            : 'Off — showing trends across the whole catalog',
                        style: GoogleFonts.poppins(
                          fontSize: 11.5,
                          color: const Color(0xFF6B7280),
                        ),
                      ),
                    ],
                  ),
                ),
                Switch(
                  value: showPersonalized,
                  onChanged: busy ? null : (_) => _toggleMode(),
                  activeThumbColor: Colors.white,
                  activeTrackColor: const Color(0xFF0B5D85),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildHeader(BuildContext context) {
    return Row(
      children: [
        // A tab's first page has nothing to go back to (popping it would
        // empty the tab), so the arrow only shows on pushed pages.
        if (Navigator.canPop(context)) ...[
          InkWell(
            onTap: () {
              HapticFeedback.lightImpact();
              Navigator.pop(context);
            },
            borderRadius: BorderRadius.circular(16),
            child: Container(
              height: 42,
              width: 42,
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(16),
              ),
              child: const Icon(
                Icons.arrow_back_ios_new_rounded,
                color: Color(0xFF111827),
                size: 18,
              ),
            ),
          ),
          const SizedBox(width: 12),
        ],
        Text(
          'Trending Now',
          style: GoogleFonts.poppins(
            fontSize: 20,
            fontWeight: FontWeight.w800,
            color: const Color(0xFF111827),
          ),
        ),
      ],
    );
  }

  Widget _buildStatusCard({required bool loading}) {
    final String title = loading
        ? (showPersonalized
            ? 'Finding what\'s trending for you...'
            : 'Scanning the whole catalog for trends...')
        : (showPersonalized
            ? 'Trending picks, matched to your style'
            : 'Trending across the whole catalog');

    final String subtitle = showPersonalized
        ? 'Real products from your personalized recommendations, '
            'currently trending up.'
        : 'Real products from the full catalog, currently trending up — '
            'not filtered to your preferences.';

    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(24),
        gradient: const LinearGradient(
          colors: [Color(0xFF073B5A), Color(0xFF0E6E9E)],
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
              loading
                  ? Icons.hourglass_top_rounded
                  : (showPersonalized
                      ? Icons.trending_up_rounded
                      : Icons.public_rounded),
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
                  title,
                  style: GoogleFonts.poppins(
                    fontSize: 16,
                    fontWeight: FontWeight.w800,
                    color: Colors.white,
                  ),
                ),
                const SizedBox(height: 5),
                Text(
                  subtitle,
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

  Widget _buildTrendingAttributesSection() {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(24),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(
                Icons.auto_awesome_motion_rounded,
                size: 20,
                color: Color(0xFF0B5D85),
              ),
              const SizedBox(width: 8),
              Text(
                'What\'s trending right now',
                style: GoogleFonts.poppins(
                  fontSize: 16,
                  fontWeight: FontWeight.w800,
                  color: const Color(0xFF111827),
                ),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            'Looks that are rising together across Sri Lanka\'s top fashion '
            'retailers. A cloth is only trending when it has the whole look.',
            style: GoogleFonts.poppins(
              fontSize: 11.5,
              height: 1.4,
              color: const Color(0xFF6B7280),
            ),
          ),
          const SizedBox(height: 14),
          SizedBox(
            height: 76,
            child: ListView.separated(
              scrollDirection: Axis.horizontal,
              itemCount: topSegments.length,
              separatorBuilder: (context, index) => const SizedBox(width: 10),
              itemBuilder: (context, index) {
                return _buildTrendSegmentChip(topSegments[index]);
              },
            ),
          ),
        ],
      ),
    );
  }

  // "color · category" for a colour x category segment.
  String _segmentKindLabel(TrendSegment segment) {
    final String kind = segment.parts
        .map((p) => p.attributeType.replaceAll('_', ' '))
        .join(' · ');
    return _capitalizeTrendLabel(kind.isEmpty ? 'combination' : kind);
  }

  Widget _buildTrendSegmentChip(TrendSegment segment) {
    final Color confidenceColor = _confidenceColor(segment.confidence);

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
      decoration: BoxDecoration(
        color: const Color(0xFFF9FAFB),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: const Color(0xFFE5E7EB)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Row(
            children: [
              Icon(
                _attributeTypeIcon(segment.parts.isEmpty
                    ? ''
                    : segment.parts.first.attributeType),
                size: 11,
                color: const Color(0xFF0B5D85),
              ),
              const SizedBox(width: 4),
              Text(
                _segmentKindLabel(segment),
                style: GoogleFonts.poppins(
                  fontSize: 9.5,
                  fontWeight: FontWeight.w600,
                  color: const Color(0xFF0B5D85),
                  letterSpacing: 0.2,
                ),
              ),
            ],
          ),
          const SizedBox(height: 2),
          Text(
            titleCaseSegment(segment.segment),
            style: GoogleFonts.poppins(
              fontSize: 12.5,
              fontWeight: FontWeight.w700,
              color: const Color(0xFF111827),
            ),
          ),
          const SizedBox(height: 3),
          Row(
            children: [
              Container(
                width: 6,
                height: 6,
                decoration: BoxDecoration(
                  color: confidenceColor,
                  shape: BoxShape.circle,
                ),
              ),
              const SizedBox(width: 5),
              Text(
                '${_capitalizeTrendLabel(segment.confidence)} confidence',
                style: GoogleFonts.poppins(
                  fontSize: 10,
                  fontWeight: FontWeight.w600,
                  color: const Color(0xFF6B7280),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  IconData _attributeTypeIcon(String attributeType) {
    switch (attributeType) {
      case 'color':
        return Icons.palette_rounded;
      case 'fabric':
        return Icons.texture_rounded;
      case 'category':
        return Icons.checkroom_rounded;
      case 'neckline':
      case 'sleeve_length':
      case 'pattern':
        return Icons.style_rounded;
      default:
        return Icons.trending_up_rounded;
    }
  }

  Color _confidenceColor(String confidence) {
    switch (confidence.toLowerCase()) {
      case 'high':
        return const Color(0xFF16A34A);
      case 'medium':
        return const Color(0xFF2563EB);
      case 'low':
        return const Color(0xFFF59E0B);
      default:
        return const Color(0xFF9CA3AF);
    }
  }

  Widget _buildSectionTitle(int count, {required bool loading}) {
    return Row(
      children: [
        Text(
          showPersonalized ? 'Trending For You' : 'Trending Overall',
          style: GoogleFonts.poppins(
            fontSize: 18,
            fontWeight: FontWeight.w800,
            color: const Color(0xFF111827),
          ),
        ),
        const Spacer(),
        Text(
          loading ? 'Loading...' : '$count picks',
          style: GoogleFonts.poppins(
            fontSize: 12,
            fontWeight: FontWeight.w600,
            color: const Color(0xFF0B5D85),
          ),
        ),
      ],
    );
  }

  static const Map<String, String> _levelBlurb = {
    'high': 'Strongest signals right now',
    'medium': 'Clear signals, a little less certain',
    'low': 'Early signals, treat as a hint',
  };

  // Cards shown per section before "Show all".
  static const int _collapsedCount = 8;

  Widget _buildConfidenceSections(List<ConfidenceSection> sections) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        for (int i = 0; i < sections.length; i++) ...[
          if (i > 0) const SizedBox(height: 28),
          _buildConfidenceSection(sections[i]),
        ],
      ],
    );
  }

  Widget _buildConfidenceSection(ConfidenceSection section) {
    final bool expanded = _expandedLevels.contains(section.level);
    final int total = section.products.length;
    final List<Map<String, dynamic>> shown =
        expanded || total <= _collapsedCount
            ? section.products
            : section.products.take(_collapsedCount).toList();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Container(
              width: 9,
              height: 9,
              decoration: BoxDecoration(
                color: _confidenceColor(section.level),
                shape: BoxShape.circle,
              ),
            ),
            const SizedBox(width: 8),
            Text(
              '${_capitalizeTrendLabel(section.level)} confidence',
              style: GoogleFonts.poppins(
                fontSize: 16,
                fontWeight: FontWeight.w800,
                color: const Color(0xFF111827),
              ),
            ),
            const Spacer(),
            Text(
              '$total ${total == 1 ? 'pick' : 'picks'}',
              style: GoogleFonts.poppins(
                fontSize: 12,
                fontWeight: FontWeight.w600,
                color: const Color(0xFF6B7280),
              ),
            ),
          ],
        ),
        const SizedBox(height: 2),
        Padding(
          padding: const EdgeInsets.only(left: 17),
          child: Text(
            _levelBlurb[section.level] ?? '',
            style: GoogleFonts.poppins(
              fontSize: 12,
              color: const Color(0xFF6B7280),
            ),
          ),
        ),
        const SizedBox(height: 14),
        GridView.builder(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          itemCount: shown.length,
          // As many columns as fit: 2 on phones, more on wide web/tablet.
          gridDelegate: const SliverGridDelegateWithMaxCrossAxisExtent(
            maxCrossAxisExtent: 200,
            crossAxisSpacing: 12,
            mainAxisSpacing: 12,
            childAspectRatio: 0.62,
          ),
          itemBuilder: (context, index) =>
              _buildProductCard(shown[index], inGrid: true),
        ),
        if (total > _collapsedCount)
          Align(
            alignment: Alignment.center,
            child: TextButton(
              onPressed: () {
                setState(() {
                  if (expanded) {
                    _expandedLevels.remove(section.level);
                  } else {
                    _expandedLevels.add(section.level);
                  }
                });
              },
              child: Text(expanded ? 'Show fewer' : 'Show all $total'),
            ),
          ),
      ],
    );
  }

  Widget _buildProductCard(Map<String, dynamic> product, {bool inGrid = false}) {
    return SizedBox(
      width: inGrid ? null : 165,
      child: InkWell(
        onTap: () {
          HapticFeedback.lightImpact();

          // Trending is discovery/inspiration, not a personal-preference
          // signal, so browsing it doesn't teach Chala's learning engine.
          // Explicit Save/Select/Dislike on the detail screen still do.
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
                        memCacheWidth: 600,
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
                      left: 10,
                      right: 10,
                      // Two rows, not two corners. Sharing one row (with
                      // Flexible + ellipsis) technically stopped the two
                      // badges overlapping, but it meant "Medium
                      // confidence" routinely got clipped to "Medium
                      // co..." — unreadable to the customer. Stacking
                      // gives each badge the full card width to itself.
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 9,
                              vertical: 5,
                            ),
                            decoration: BoxDecoration(
                              color: const Color(0xFF0B5D85).withOpacity(0.92),
                              borderRadius: BorderRadius.circular(14),
                            ),
                            child: Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                const Icon(
                                  Icons.trending_up_rounded,
                                  color: Colors.white,
                                  size: 12,
                                ),
                                const SizedBox(width: 3),
                                Flexible(
                                  child: Text(
                                    _capitalizeTrendLabel(
                                      product['trendingLabel']?.toString() ??
                                          'Trending',
                                    ),
                                    maxLines: 1,
                                    overflow: TextOverflow.ellipsis,
                                    style: GoogleFonts.poppins(
                                      color: Colors.white,
                                      fontSize: 10,
                                      fontWeight: FontWeight.w700,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ),
                          if (!inGrid) ...[
                            const SizedBox(height: 6),
                            Container(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 8,
                                vertical: 5,
                              ),
                              decoration: BoxDecoration(
                                color: Colors.black.withOpacity(0.65),
                                borderRadius: BorderRadius.circular(14),
                              ),
                              child: Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  Container(
                                    width: 6,
                                    height: 6,
                                    decoration: BoxDecoration(
                                      color: _confidenceColor(
                                        product['trendingConfidence']
                                                ?.toString() ??
                                            '',
                                      ),
                                      shape: BoxShape.circle,
                                    ),
                                  ),
                                  const SizedBox(width: 5),
                                  Flexible(
                                    child: Text(
                                      '${_capitalizeTrendLabel(product['trendingConfidence']?.toString() ?? 'Unknown')} confidence',
                                      maxLines: 1,
                                      overflow: TextOverflow.ellipsis,
                                      style: GoogleFonts.poppins(
                                        color: Colors.white,
                                        fontSize: 9,
                                        fontWeight: FontWeight.w600,
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ],
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
      ),
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
            'Loading trending picks...',
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

  Widget _buildErrorState(
    String message,
    Future<void> Function() onRetry,
  ) {
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
            'Trending connection failed',
            style: GoogleFonts.poppins(
              fontSize: 16,
              fontWeight: FontWeight.w800,
              color: const Color(0xFF111827),
            ),
          ),
          const SizedBox(height: 6),
          Text(
            message,
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
              onPressed: onRetry,
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
            Icons.trending_flat_rounded,
            size: 42,
            color: Color(0xFF9CA3AF),
          ),
          const SizedBox(height: 12),
          Text(
            showPersonalized
                ? 'Nothing trending in your style right now'
                : 'Nothing trending in the catalog right now',
            textAlign: TextAlign.center,
            style: GoogleFonts.poppins(
              fontSize: 16,
              fontWeight: FontWeight.w800,
              color: const Color(0xFF111827),
            ),
          ),
          const SizedBox(height: 6),
          Text(
            showPersonalized
                ? 'Check back later as trends update, or explore your full '
                    'personalized recommendations on Home.'
                : 'Check back later as trends update.',
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
}
