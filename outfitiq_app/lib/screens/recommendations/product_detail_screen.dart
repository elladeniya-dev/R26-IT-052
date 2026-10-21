import 'dart:async';

import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../core/responsive.dart';
import '../../models/s_product_model.dart';
import '../../services/interaction_history_service.dart';
import '../../services/interaction_service.dart';
import '../../services/learning_service.dart';
import '../outfit/s_complete_the_look_screen.dart';

class ProductDetailScreen extends StatefulWidget {
  final Map<String, dynamic> product;

  const ProductDetailScreen({
    super.key,
    required this.product,
  });

  @override
  State<ProductDetailScreen> createState() => _ProductDetailScreenState();
}

class _ProductDetailScreenState extends State<ProductDetailScreen> {
  final InteractionService _interactionService = InteractionService();
  final LearningService _learningService = LearningService();

  bool _isSendingInteraction = false;

  // Latest explicit reaction to this product. Save and dislike replace each
  // other, matching how the learning engine reads the newest signal.
  bool _isSaved = false;
  bool _isDisliked = false;

  Map<String, dynamic> get product => widget.product;

  @override
  void initState() {
    super.initState();
    _recordSilentInteraction('view');
    _loadExistingReaction();
  }

  // Shows the save/dislike state from an earlier visit. History is
  // newest-first, so the first save/dislike for this item is the current one.
  Future<void> _loadExistingReaction() async {
    final String itemId = product['itemId']?.toString() ?? '';
    if (itemId.isEmpty) return;

    try {
      final Map<String, dynamic> history =
          await InteractionHistoryService().getInteractionHistory();
      final List<dynamic> interactions = history['interactions'] ?? [];

      for (final dynamic entry in interactions) {
        if (entry is! Map || entry['item_id']?.toString() != itemId) continue;

        final String type =
            (entry['interaction_type'] ?? '').toString().toLowerCase();
        if (type != 'save' && type != 'dislike') continue;

        if (!mounted) return;
        setState(() {
          _isSaved = type == 'save';
          _isDisliked = type == 'dislike';
        });
        return;
      }
    } catch (_) {
      // Purely cosmetic; the buttons still work without it.
    }
  }

  // Passive signal fired when the detail page opens. Unlike
  // Save/Select/Dislike (explicit user actions with feedback and a
  // busy state), this is fire-and-forget with no snackbar — matching
  // how the recommendation grid's 'click' interaction already behaves.
  void _recordSilentInteraction(String interactionType) {
    final String itemId = product['itemId']?.toString() ?? '';
    if (itemId.isEmpty) return;

    () async {
      try {
        await _interactionService.sendInteraction(
          itemId: itemId,
          interactionType: interactionType,
        );
        await _learningService.updateLearningPreferences();
      } catch (_) {
        // Silently ignored: passive background signal.
      }
    }();
  }

  // False for items shown without any recommendation scoring (e.g. the
  // catalog-wide trending view). The card still shows for them, but the
  // personalization rows read "—" instead of a misleading 0%.
  bool get _hasPersonalScores => product['scoresAvailable'] != false;

  String _scoreText(double value) =>
      _hasPersonalScores ? '${(value * 100).round()}%' : '—';

  // Bar length for the trend row: the cloth's segment score (about 0 to 3
  // for the strongest looks) scaled to 0..1.
  double get _trendStrength {
    final dynamic raw = product['trendScore'];
    final double score = raw is num ? raw.toDouble() : 0.0;
    return (score / 3.0).clamp(0.0, 1.0);
  }

  String _capitalizeWord(String value) =>
      value.isEmpty ? value : '${value[0].toUpperCase()}${value.substring(1)}';

  double get _matchValue {
    final dynamic directScore = product['finalScore'];

    if (directScore is double) return directScore.clamp(0.0, 1.0);
    if (directScore is int) return directScore.toDouble().clamp(0.0, 1.0);

    final String matchText = product['match'] ?? '0%';
    final String cleaned = matchText.replaceAll('%', '');
    return ((double.tryParse(cleaned) ?? 0) / 100).clamp(0.0, 1.0);
  }

  double get _userMatchScore {
    final dynamic score = product['userMatchScore'];

    if (score is double) return score.clamp(0.0, 1.0);
    if (score is int) return score.toDouble().clamp(0.0, 1.0);

    return 0.0;
  }

  double get _mlSimilarityScore {
    final dynamic score = product['mlSimilarityScore'];

    if (score is double) return score.clamp(0.0, 1.0);
    if (score is int) return score.toDouble().clamp(0.0, 1.0);

    return 0.0;
  }

  double get _productQualityScore {
    final dynamic score = product['productQualityScore'];

    if (score is double) return score.clamp(0.0, 1.0);
    if (score is int) return score.toDouble().clamp(0.0, 1.0);

    return 0.0;
  }

  List<String> get _reasonTags {
    final dynamic tags = product['tags'];

    if (tags is List) {
      return tags.map((tag) => tag.toString()).toList();
    }

    return [
      'matches your selected preferences',
      'ML similarity checked',
      'recommended by OutfitIQ engine',
    ];
  }

  double _detailImageHeight(BuildContext context) {
    final Size size = MediaQuery.of(context).size;

    if (size.width >= 900) {
      return (size.height * 0.78).clamp(560.0, 820.0).toDouble();
    }

    return (size.height * 0.50).clamp(380.0, 560.0).toDouble();
  }

  void _showFeedbackMessage(String message, {bool isError = false}) {
    if (!mounted) return;

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
            isError ? const Color(0xFFB91C1C) : const Color(0xFF10231F),
        behavior: SnackBarBehavior.floating,
        margin: const EdgeInsets.all(16),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
        ),
        duration: const Duration(seconds: 2),
      ),
    );
  }

  // Records a real interaction against Chala's learning engine
  // (view/click/save/select/dislike), same pattern as the original
  // Chala home screen's interaction handling.
  Future<void> _handleInteraction(String interactionType) async {
    if (_isSendingInteraction) return;

    final String itemId = product['itemId']?.toString() ?? '';

    if (itemId.isEmpty) {
      _showFeedbackMessage('Missing product id for this item.', isError: true);
      return;
    }

    if ((interactionType == 'save' && _isSaved) ||
        (interactionType == 'dislike' && _isDisliked)) {
      _showFeedbackMessage(
        interactionType == 'save' ? 'Already saved.' : 'Already disliked.',
      );
      return;
    }

    // Instant feedback (Save/Dislike light up on tap); undone if the call fails.
    final bool wasSaved = _isSaved;
    final bool wasDisliked = _isDisliked;

    setState(() {
      _isSendingInteraction = true;
      if (interactionType == 'save') {
        _isSaved = true;
        _isDisliked = false;
      } else if (interactionType == 'dislike') {
        _isDisliked = true;
        _isSaved = false;
      }
    });

    try {
      await _interactionService.sendInteraction(
        itemId: itemId,
        interactionType: interactionType,
      );

      final Map<String, dynamic> learningResponse =
          await _learningService.updateLearningPreferences();

      final String learningMessage =
          learningResponse['message'] ?? 'Learning updated successfully';

      _showFeedbackMessage('$interactionType saved. $learningMessage');
    } catch (error) {
      if (mounted) {
        setState(() {
          _isSaved = wasSaved;
          _isDisliked = wasDisliked;
        });
      }
      _showFeedbackMessage(error.toString(), isError: true);
    } finally {
      if (mounted) {
        setState(() {
          _isSendingInteraction = false;
        });
      }
    }
  }

  Future<void> _openStorePage() async {
    HapticFeedback.mediumImpact();

    final String productUrl = product['productUrl'] ?? '';

    // Selecting through to the store is the strongest positive
    // signal in Chala's interaction vocabulary.
    unawaited(_handleInteraction('select'));

    if (productUrl.isEmpty) {
      _showFeedbackMessage('Product store link is not available yet.');
      return;
    }

    final Uri url = Uri.parse(productUrl);

    final bool opened = await launchUrl(
      url,
      mode: LaunchMode.externalApplication,
    );

    if (!opened && mounted) {
      _showFeedbackMessage('Could not open the store page.', isError: true);
    }
  }

  void _openCompleteTheLook() {
    HapticFeedback.lightImpact();

    final List<String> colorList = (product['color'] as String? ?? '')
        .split(',')
        .map((value) => value.trim())
        .where((value) => value.isNotEmpty)
        .toList();

    final List<String> styleList = (product['style'] as String? ?? '')
        .split(',')
        .map((value) => value.trim())
        .where((value) => value.isNotEmpty)
        .toList();

    final ProductModel selectedProduct = ProductModel(
      itemId: product['itemId']?.toString() ?? '',
      title: product['title']?.toString() ?? '',
      role: product['category']?.toString() ?? '',
      color: colorList,
      style: styleList,
      imageUrl: product['image']?.toString() ?? '',
      productUrl: product['productUrl']?.toString() ?? '',
      price: (product['priceValue'] as num?)?.toDouble() ?? 0.0,
      brand: product['brand']?.toString() ?? '',
      description: '',
    );

    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) =>
            CompleteTheLookScreen(selectedProduct: selectedProduct),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final String title = product['title'] ?? 'Fashion Product';
    final String brand = product['brand'] ?? 'Unknown Brand';
    final String category = product['category'] ?? 'Fashion';
    final String price = product['price'] ?? 'LKR 0';
    final String image = product['image'] ?? '';
    final String match = product['match'] ?? '0%';
    final String style = product['style'] ?? 'Smart Match';
    final String color = product['color'] ?? 'Preferred Color';
    final String source = product['source'] ?? 'product source';

    final List<Widget> detailCards = [
      _buildProductHeader(
        title: title,
        brand: brand,
        category: category,
        price: price,
      ),
      const SizedBox(height: 14),
      _buildActionChips(),
      const SizedBox(height: 18),
      _buildQuickInfoCard(
        brand: brand,
        category: category,
        style: style,
        color: color,
        source: source,
      ),
      const SizedBox(height: 18),
      _buildRecommendationScoreCard(match),
      const SizedBox(height: 18),
      _buildWhyRecommendedCard(),
      const SizedBox(height: 18),
      _buildEngineProofCard(),
    ];

    return ResponsiveCenter(
      maxWidth: 1200,
      child: LayoutBuilder(
        builder: (context, constraints) {
          // Wide screens: image on the left, details and actions on the right.
          final bool sideBySide = constraints.maxWidth >= 900;

          return Scaffold(
            backgroundColor: const Color(0xFFF6F7F9),
            body: SafeArea(
              child: sideBySide
                  ? Padding(
                      padding: const EdgeInsets.all(20),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          Expanded(
                            flex: 5,
                            child: ClipRRect(
                              borderRadius: BorderRadius.circular(24),
                              child: _buildImageSection(context, image, match),
                            ),
                          ),
                          const SizedBox(width: 28),
                          Expanded(
                            flex: 6,
                            child: Column(
                              children: [
                                Expanded(
                                  child: ListView(
                                    padding: EdgeInsets.zero,
                                    children: detailCards,
                                  ),
                                ),
                                const SizedBox(height: 12),
                                _buildBottomAction(context),
                              ],
                            ),
                          ),
                        ],
                      ),
                    )
                  : ListView(
                      padding: EdgeInsets.zero,
                      children: [
                        _buildImageSection(context, image, match),
                        Padding(
                          padding: const EdgeInsets.fromLTRB(18, 20, 18, 24),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: detailCards,
                          ),
                        ),
                      ],
                    ),
            ),
            bottomNavigationBar:
                sideBySide ? null : _buildBottomAction(context),
          );
        },
      ),
    );
  }

  Widget _buildImageSection(BuildContext context, String image, String match) {
    final double imageHeight = _detailImageHeight(context);

    return Container(
      height: imageHeight,
      width: double.infinity,
      color: Colors.white,
      child: Stack(
        children: [
          Positioned.fill(
            child: Container(
              color: Colors.white,
              child: image.isEmpty
                  ? const Center(
                      child: Icon(
                        Icons.image_not_supported_rounded,
                        size: 48,
                        color: Color(0xFF9CA3AF),
                      ),
                    )
                  : CachedNetworkImage(
                      imageUrl: image,
                      memCacheWidth: 1200,
                      width: double.infinity,
                      height: double.infinity,
                      fit: BoxFit.contain,
                      alignment: Alignment.center,
                      placeholder: (context, url) => Container(
                        color: const Color(0xFFE5E7EB),
                        child: const Center(
                          child: CircularProgressIndicator(strokeWidth: 2),
                        ),
                      ),
                      errorWidget: (context, url, error) => Container(
                        color: const Color(0xFFE5E7EB),
                        child: const Center(
                          child: Icon(
                            Icons.image_not_supported_rounded,
                            size: 48,
                            color: Color(0xFF9CA3AF),
                          ),
                        ),
                      ),
                    ),
            ),
          ),
          Positioned(
            top: 18,
            left: 18,
            child: InkWell(
              onTap: () {
                HapticFeedback.lightImpact();
                Navigator.pop(context);
              },
              borderRadius: BorderRadius.circular(18),
              child: Container(
                height: 44,
                width: 44,
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.94),
                  borderRadius: BorderRadius.circular(16),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withOpacity(0.08),
                      blurRadius: 14,
                      offset: const Offset(0, 5),
                    ),
                  ],
                ),
                child: const Icon(
                  Icons.arrow_back_ios_new_rounded,
                  size: 18,
                  color: Color(0xFF111827),
                ),
              ),
            ),
          ),
          Positioned(
            left: 20,
            bottom: 22,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 9),
              decoration: BoxDecoration(
                color: const Color(0xFF0B5D85),
                borderRadius: BorderRadius.circular(20),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.12),
                    blurRadius: 14,
                    offset: const Offset(0, 5),
                  ),
                ],
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(
                    Icons.auto_awesome_rounded,
                    color: Colors.white,
                    size: 17,
                  ),
                  const SizedBox(width: 6),
                  Text(
                    '$match Match',
                    style: GoogleFonts.poppins(
                      fontSize: 13,
                      fontWeight: FontWeight.w800,
                      color: Colors.white,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildProductHeader({
    required String title,
    required String brand,
    required String category,
    required String price,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          brand,
          style: GoogleFonts.poppins(
            fontSize: 13,
            fontWeight: FontWeight.w700,
            color: const Color(0xFF0B5D85),
          ),
        ),
        const SizedBox(height: 6),
        Text(
          title,
          style: GoogleFonts.poppins(
            fontSize: 25,
            height: 1.2,
            fontWeight: FontWeight.w800,
            color: const Color(0xFF111827),
          ),
        ),
        const SizedBox(height: 8),
        Row(
          children: [
            Expanded(
              child: Text(
                price,
                style: GoogleFonts.poppins(
                  fontSize: 20,
                  fontWeight: FontWeight.w800,
                  color: const Color(0xFF0B5D85),
                ),
              ),
            ),
            const SizedBox(width: 12),
            Flexible(
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 7),
                decoration: BoxDecoration(
                  color: const Color(0xFFE8F3F8),
                  borderRadius: BorderRadius.circular(18),
                ),
                child: Text(
                  category,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: GoogleFonts.poppins(
                    fontSize: 12,
                    fontWeight: FontWeight.w700,
                    color: const Color(0xFF0B5D85),
                  ),
                ),
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildQuickInfoCard({
    required String brand,
    required String category,
    required String style,
    required String color,
    required String source,
  }) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(24),
      ),
      child: Column(
        children: [
          _infoRow(Icons.storefront_rounded, 'Brand', brand),
          _infoRow(Icons.category_rounded, 'Category', category),
          _infoRow(Icons.style_rounded, 'Style', style),
          _infoRow(Icons.palette_rounded, 'Color', color),
          _infoRow(Icons.public_rounded, 'Source', source),
        ],
      ),
    );
  }

  Widget _buildRecommendationScoreCard(String match) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [
            Color(0xFF073B5A),
            Color(0xFF0E6E9E),
          ],
        ),
        borderRadius: BorderRadius.circular(24),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _whiteCardTitle(
            icon: Icons.analytics_rounded,
            title: 'Recommendation scores',
          ),
          const SizedBox(height: 16),
          _scoreRow(
            title: 'Final hybrid match score',
            valueText: _hasPersonalScores ? match : '—',
            value: _hasPersonalScores ? _matchValue : 0,
          ),
          const SizedBox(height: 14),
          _scoreRow(
            title: 'User preference match',
            valueText: _scoreText(_userMatchScore),
            value: _hasPersonalScores ? _userMatchScore : 0,
          ),
          const SizedBox(height: 14),
          _scoreRow(
            title: 'ML similarity score',
            valueText: _scoreText(_mlSimilarityScore),
            value: _hasPersonalScores ? _mlSimilarityScore : 0,
          ),
          const SizedBox(height: 14),
          _scoreRow(
            title: 'Product quality score',
            valueText: _scoreText(_productQualityScore),
            value: _hasPersonalScores ? _productQualityScore : 0,
          ),
          if (product['trendingLabel'] != null) ...[
            const SizedBox(height: 14),
            _scoreRow(
              title: 'Trend signal: ${product['trendingLabel']}',
              valueText:
                  '${_capitalizeWord((product['trendingConfidence'] ?? '').toString())} confidence',
              value: _trendStrength,
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildWhyRecommendedCard() {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(24),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _cardTitle(
            icon: Icons.lightbulb_rounded,
            title: 'Why recommended?',
          ),
          const SizedBox(height: 14),
          Wrap(
            spacing: 10,
            runSpacing: 10,
            children: _reasonTags.map((tag) {
              return _buildReasonTag(tag);
            }).toList(),
          ),
        ],
      ),
    );
  }

  Widget _buildReasonTag(String tag) {
    return Container(
      constraints: const BoxConstraints(maxWidth: 280),
      padding: const EdgeInsets.symmetric(
        horizontal: 13,
        vertical: 9,
      ),
      decoration: BoxDecoration(
        color: const Color(0xFFE8F3F8),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(
          color: const Color(0xFF0B5D85).withOpacity(0.14),
        ),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(
            Icons.check_rounded,
            size: 15,
            color: Color(0xFF0B5D85),
          ),
          const SizedBox(width: 5),
          Flexible(
            child: Text(
              tag,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: GoogleFonts.poppins(
                fontSize: 12,
                fontWeight: FontWeight.w700,
                color: const Color(0xFF0B5D85),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildEngineProofCard() {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: const Color(0xFFE8F3F8),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(
          color: const Color(0xFF0B5D85).withOpacity(0.14),
        ),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(
            Icons.verified_rounded,
            color: Color(0xFF0B5D85),
            size: 24,
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              _hasPersonalScores
                  ? 'This product is recommended using OutfitIQ’s hybrid recommendation engine. The final score combines rule-based user preference matching, ML-based semantic similarity, and product quality signals.'
                  : 'Shown because it carries a rising trend across the whole catalog. Personal scores are not calculated for it, since it was not matched to your profile.',
              style: GoogleFonts.poppins(
                fontSize: 12,
                height: 1.5,
                fontWeight: FontWeight.w500,
                color: const Color(0xFF0B5D85),
              ),
            ),
          ),
        ],
      ),
    );
  }

  // The only fixed action: opening the store (also the strongest "select"
  // signal for the learning engine). Save, Dislike and Complete the Look
  // live in a chip row under the price, so they no longer eat the screen.
  Widget _buildBottomAction(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(18, 10, 18, 10),
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
        height: 50,
        width: double.infinity,
        child: ElevatedButton(
          onPressed: _isSendingInteraction ? null : _openStorePage,
          style: ElevatedButton.styleFrom(
            backgroundColor: const Color(0xFF0B5D85),
            foregroundColor: Colors.white,
            disabledBackgroundColor: const Color(0xFF0B5D85).withOpacity(0.6),
            elevation: 0,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(28),
            ),
          ),
          child: _isSendingInteraction
              ? const SizedBox(
                  width: 22,
                  height: 22,
                  child: CircularProgressIndicator(
                    strokeWidth: 2.4,
                    color: Colors.white,
                  ),
                )
              : Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Flexible(
                      child: Text(
                        'Open store page',
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: GoogleFonts.poppins(
                          fontSize: 15,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    const Icon(Icons.open_in_new_rounded, size: 20),
                  ],
                ),
        ),
      ),
    );
  }

  Widget _buildActionChips() {
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: [
        _actionChip(
          icon: _isSaved
              ? Icons.bookmark_rounded
              : Icons.bookmark_border_rounded,
          label: _isSaved ? 'Saved' : 'Save',
          color: const Color(0xFF0B5D85),
          filled: _isSaved,
          onTap: () => _handleInteraction('save'),
        ),
        _actionChip(
          icon: _isDisliked
              ? Icons.thumb_down_alt_rounded
              : Icons.thumb_down_alt_outlined,
          label: _isDisliked ? 'Disliked' : 'Dislike',
          color: const Color(0xFFB91C1C),
          filled: _isDisliked,
          tint: true,
          onTap: () => _handleInteraction('dislike'),
        ),
        _actionChip(
          icon: Icons.checkroom_rounded,
          label: 'Complete the look',
          color: const Color(0xFF0B5D85),
          onTap: _openCompleteTheLook,
        ),
      ],
    );
  }

  // Compact pill. [filled] = the active state (solid for Save, soft tint for
  // Dislike). _handleInteraction ignores taps while a request is in flight, so
  // the chips never flicker into a disabled look.
  Widget _actionChip({
    required IconData icon,
    required String label,
    required Color color,
    required VoidCallback onTap,
    bool filled = false,
    bool tint = false,
  }) {
    final Color background = !filled
        ? Colors.white
        : tint
            ? const Color(0xFFFEE2E2)
            : color;
    final Color foreground = filled && !tint ? Colors.white : color;

    return Material(
      color: background,
      shape: StadiumBorder(
        side: BorderSide(
          color: filled ? color : const Color(0xFFE5E7EB),
        ),
      ),
      child: InkWell(
        customBorder: const StadiumBorder(),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 9),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(icon, size: 17, color: foreground),
              const SizedBox(width: 6),
              Text(
                label,
                style: GoogleFonts.poppins(
                  fontSize: 12.5,
                  fontWeight: FontWeight.w700,
                  color: foreground,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _infoRow(IconData icon, String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 13),
      child: Row(
        children: [
          Icon(
            icon,
            color: const Color(0xFF0B5D85),
            size: 20,
          ),
          const SizedBox(width: 10),
          SizedBox(
            width: 82,
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
              value,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: GoogleFonts.poppins(
                fontSize: 12,
                fontWeight: FontWeight.w800,
                color: const Color(0xFF111827),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _scoreRow({
    required String title,
    required String valueText,
    required double value,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Expanded(
              child: Text(
                title,
                style: GoogleFonts.poppins(
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                  color: Colors.white.withOpacity(0.86),
                ),
              ),
            ),
            const SizedBox(width: 10),
            Text(
              valueText,
              style: GoogleFonts.poppins(
                fontSize: 13,
                fontWeight: FontWeight.w800,
                color: Colors.white,
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),
        ClipRRect(
          borderRadius: BorderRadius.circular(20),
          child: LinearProgressIndicator(
            value: value,
            minHeight: 8,
            backgroundColor: Colors.white.withOpacity(0.18),
            valueColor: const AlwaysStoppedAnimation<Color>(Colors.white),
          ),
        ),
      ],
    );
  }

  Widget _cardTitle({
    required IconData icon,
    required String title,
  }) {
    return Row(
      children: [
        Icon(
          icon,
          color: const Color(0xFF0B5D85),
          size: 21,
        ),
        const SizedBox(width: 8),
        Flexible(
          child: Text(
            title,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: GoogleFonts.poppins(
              fontSize: 16,
              fontWeight: FontWeight.w800,
              color: const Color(0xFF111827),
            ),
          ),
        ),
      ],
    );
  }

  Widget _whiteCardTitle({
    required IconData icon,
    required String title,
  }) {
    return Row(
      children: [
        Icon(
          icon,
          color: Colors.white,
          size: 21,
        ),
        const SizedBox(width: 8),
        Flexible(
          child: Text(
            title,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: GoogleFonts.poppins(
              fontSize: 16,
              fontWeight: FontWeight.w800,
              color: Colors.white,
            ),
          ),
        ),
      ],
    );
  }
}
