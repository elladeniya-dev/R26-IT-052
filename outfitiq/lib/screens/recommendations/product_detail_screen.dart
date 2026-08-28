import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:url_launcher/url_launcher.dart';

class ProductDetailScreen extends StatelessWidget {
  final Map<String, dynamic> product;

  const ProductDetailScreen({
    super.key,
    required this.product,
  });

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

  void _showFeedbackMessage(BuildContext context, String message) {
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

  Future<void> _openStorePage(BuildContext context) async {
    HapticFeedback.mediumImpact();

    final String productUrl = product['productUrl'] ?? '';

    if (productUrl.isEmpty) {
      _showFeedbackMessage(
        context,
        'Product store link is not available yet.',
      );
      return;
    }

    final Uri url = Uri.parse(productUrl);

    final bool opened = await launchUrl(
      url,
      mode: LaunchMode.externalApplication,
    );

    if (!opened && context.mounted) {
      _showFeedbackMessage(
        context,
        'Could not open the store page.',
      );
    }
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

    return Scaffold(
      backgroundColor: const Color(0xFFF6F7F9),
      body: SafeArea(
        child: ListView(
          padding: EdgeInsets.zero,
          children: [
            _buildImageSection(context, image, match),
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 20, 20, 120),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _buildProductHeader(
                    title: title,
                    brand: brand,
                    category: category,
                    price: price,
                  ),
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
                ],
              ),
            ),
          ],
        ),
      ),
      bottomNavigationBar: _buildBottomAction(context),
    );
  }

  Widget _buildImageSection(BuildContext context, String image, String match) {
    return SizedBox(
      height: 430,
      child: Stack(
        children: [
          Positioned.fill(
            child: CachedNetworkImage(
              imageUrl: image,
              fit: BoxFit.cover,
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
          Positioned.fill(
            child: DecoratedBox(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                  colors: [
                    Colors.black.withOpacity(0.25),
                    Colors.transparent,
                    Colors.black.withOpacity(0.45),
                  ],
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
                  color: Colors.white.withOpacity(0.92),
                  borderRadius: BorderRadius.circular(16),
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
            top: 18,
            right: 18,
            child: InkWell(
              onTap: () {
                HapticFeedback.lightImpact();
                _showFeedbackMessage(context, 'Product saved to favorites.');
              },
              borderRadius: BorderRadius.circular(18),
              child: Container(
                height: 44,
                width: 44,
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.92),
                  borderRadius: BorderRadius.circular(16),
                ),
                child: const Icon(
                  Icons.favorite_border_rounded,
                  size: 22,
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
              ),
              child: Row(
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
            Text(
              price,
              style: GoogleFonts.poppins(
                fontSize: 20,
                fontWeight: FontWeight.w800,
                color: const Color(0xFF0B5D85),
              ),
            ),
            const Spacer(),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 7),
              decoration: BoxDecoration(
                color: const Color(0xFFE8F3F8),
                borderRadius: BorderRadius.circular(18),
              ),
              child: Text(
                category,
                style: GoogleFonts.poppins(
                  fontSize: 12,
                  fontWeight: FontWeight.w700,
                  color: const Color(0xFF0B5D85),
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
            valueText: match,
            value: _matchValue,
          ),
          const SizedBox(height: 14),
          _scoreRow(
            title: 'User preference match',
            valueText: '${(_userMatchScore * 100).round()}%',
            value: _userMatchScore,
          ),
          const SizedBox(height: 14),
          _scoreRow(
            title: 'ML similarity score',
            valueText: '${(_mlSimilarityScore * 100).round()}%',
            value: _mlSimilarityScore,
          ),
          const SizedBox(height: 14),
          _scoreRow(
            title: 'Product quality score',
            valueText: '${(_productQualityScore * 100).round()}%',
            value: _productQualityScore,
          ),
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
              return Container(
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
                    Text(
                      tag,
                      style: GoogleFonts.poppins(
                        fontSize: 12,
                        fontWeight: FontWeight.w700,
                        color: const Color(0xFF0B5D85),
                      ),
                    ),
                  ],
                ),
              );
            }).toList(),
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
              'This product is recommended using OutfitIQ’s hybrid recommendation engine. The final score combines rule-based user preference matching, ML-based semantic similarity, and product quality signals.',
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

  Widget _buildBottomAction(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(20, 12, 20, 24),
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
          onPressed: () => _openStorePage(context),
          style: ElevatedButton.styleFrom(
            backgroundColor: const Color(0xFF0B5D85),
            foregroundColor: Colors.white,
            elevation: 0,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(30),
            ),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(
                'Open Store Page',
                style: GoogleFonts.poppins(
                  fontSize: 15,
                  fontWeight: FontWeight.w800,
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
        Text(
          title,
          style: GoogleFonts.poppins(
            fontSize: 16,
            fontWeight: FontWeight.w800,
            color: Colors.white,
          ),
        ),
      ],
    );
  }
}