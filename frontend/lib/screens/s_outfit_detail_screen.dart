import 'package:flutter/material.dart';

import '../models/s_outfit_model.dart';
import '../models/s_product_model.dart';
import '../services/s_outfit_feedback_api_service.dart';
import '../services/s_saved_outfit_api_service.dart';

class OutfitDetailScreen extends StatefulWidget {
  final OutfitModel outfit;
  final String userId;
  final VoidCallback? onGenerateAgain;

  const OutfitDetailScreen({
    super.key,
    required this.outfit,
    this.userId = 'USR001',
    this.onGenerateAgain,
  });

  @override
  State<OutfitDetailScreen> createState() => _OutfitDetailScreenState();
}

class _OutfitDetailScreenState extends State<OutfitDetailScreen> {
  final SavedOutfitApiService _savedOutfitApiService = SavedOutfitApiService();
  final OutfitFeedbackApiService _feedbackApiService =
      OutfitFeedbackApiService();

  bool _isSaving = false;
  bool _isSaved = false;
  bool _isSubmittingFeedback = false;
  int? _submittedRating;

  Future<void> _saveOutfit() async {
    if (_isSaving || _isSaved) {
      return;
    }

    setState(() {
      _isSaving = true;
    });

    try {
      final response = await _savedOutfitApiService.saveOutfit(
        outfitId: widget.outfit.outfitId,
      );

      if (!mounted) {
        return;
      }

      setState(() {
        _isSaved = true;
      });

      _showSnackBar(response.message);
    } catch (error) {
      _showSnackBar(error.toString().replaceFirst('Exception: ', ''));
    } finally {
      if (mounted) {
        setState(() {
          _isSaving = false;
        });
      }
    }
  }

  Future<void> _submitFeedback({
    required int rating,
    required String label,
  }) async {
    if (_isSubmittingFeedback || _submittedRating != null) {
      return;
    }

    setState(() {
      _isSubmittingFeedback = true;
    });

    try {
      final message = await _feedbackApiService.submitFeedback(
        outfitId: widget.outfit.outfitId,
        userId: widget.userId,
        rating: rating,
        comment: '$label outfit match',
      );

      if (!mounted) {
        return;
      }

      setState(() {
        _submittedRating = rating;
      });

      _showSnackBar(message);
    } catch (error) {
      _showSnackBar(error.toString().replaceFirst('Exception: ', ''));
    } finally {
      if (mounted) {
        setState(() {
          _isSubmittingFeedback = false;
        });
      }
    }
  }

  void _generateAgain() {
    final onGenerateAgain = widget.onGenerateAgain;

    if (onGenerateAgain == null) {
      _showSnackBar('Go back and tap Generate to create another outfit.');
      return;
    }

    Navigator.pop(context);
    onGenerateAgain();
  }

  void _showSnackBar(String message) {
    if (!mounted) {
      return;
    }

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), behavior: SnackBarBehavior.floating),
    );
  }

  String _getFallbackImageUrl({
    required String itemId,
    required String title,
    required String role,
  }) {
    final String id = itemId.toLowerCase();
    final String name = title.toLowerCase();
    final String itemRole = role.toLowerCase();

    if (id.contains('p001') ||
        name.contains('crop') ||
        name.contains('top') ||
        itemRole.contains('top')) {
      return 'https://images.unsplash.com/photo-1529139574466-a303027c1d8b?w=600';
    }

    if (id.contains('p002') ||
        name.contains('jeans') ||
        name.contains('denim') ||
        itemRole.contains('bottom')) {
      return 'https://images.unsplash.com/photo-1541099649105-f69ad21f3246?w=600';
    }

    if (id.contains('p003') ||
        name.contains('jacket') ||
        itemRole.contains('outerwear')) {
      return 'https://images.unsplash.com/photo-1548624313-0396c75e4b1a?w=600';
    }

    if (id.contains('p004') ||
        name.contains('blazer') ||
        name.contains('formal')) {
      return 'https://images.unsplash.com/photo-1487222477894-8943e31ef7b2?w=600';
    }

    if (itemRole.contains('footwear') ||
        name.contains('shoe') ||
        name.contains('sneaker')) {
      return 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=600';
    }

    if (itemRole.contains('accessory') ||
        name.contains('bag') ||
        name.contains('watch')) {
      return 'https://images.unsplash.com/photo-1590874103328-eac38a683ce7?w=600';
    }

    return 'https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=600';
  }

  @override
  Widget build(BuildContext context) {
    final int matchPercentage = (widget.outfit.compatibilityScore * 100)
        .round()
        .clamp(0, 100);

    return Scaffold(
      backgroundColor: const Color(0xFFF8F8F8),
      body: SafeArea(
        child: Column(
          children: [
            _buildTopBar(context),
            Expanded(
              child: ListView(
                padding: const EdgeInsets.all(18),
                children: [
                  _buildSummaryCard(matchPercentage),
                  const SizedBox(height: 20),
                  _buildSectionTitle(
                    title: 'Outfit Items',
                    subtitle: 'Items included in this compatible outfit.',
                  ),
                  const SizedBox(height: 14),
                  ...widget.outfit.items.map(
                    (item) => _buildProductItemCard(item),
                  ),
                  const SizedBox(height: 20),
                  _buildSectionTitle(
                    title: 'Why this outfit matches',
                    subtitle:
                        'Reason tags generated by the compatibility engine.',
                  ),
                  const SizedBox(height: 14),
                  _buildReasonTags(),
                  const SizedBox(height: 20),
                  _buildFeedbackSection(),
                  const SizedBox(height: 20),
                  _buildSectionTitle(
                    title: 'Score Breakdown',
                    subtitle: 'Detailed compatibility scoring values.',
                  ),
                  const SizedBox(height: 14),
                  _buildScoreBreakdownCard(),
                  const SizedBox(height: 20),
                  _buildSectionTitle(
                    title: 'Applied Filters',
                    subtitle: 'Filters used when generating this outfit.',
                  ),
                  const SizedBox(height: 14),
                  _buildAppliedFiltersCard(),
                  const SizedBox(height: 20),
                  _buildActionButtons(),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTopBar(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      child: Row(
        children: [
          IconButton(
            onPressed: () {
              Navigator.pop(context);
            },
            icon: const Icon(Icons.arrow_back_ios_new),
          ),
          const Expanded(
            child: Text(
              'Outfit Details',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.w900,
                color: Color(0xFF111827),
              ),
            ),
          ),
          const SizedBox(width: 48),
        ],
      ),
    );
  }

  Widget _buildSummaryCard(int matchPercentage) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: const Color(0xFF111827),
        borderRadius: BorderRadius.circular(24),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.10),
            blurRadius: 14,
            offset: const Offset(0, 7),
          ),
        ],
      ),
      child: Row(
        children: [
          Container(
            width: 78,
            height: 78,
            alignment: Alignment.center,
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(22),
            ),
            child: Text(
              '$matchPercentage%',
              style: const TextStyle(
                fontSize: 22,
                fontWeight: FontWeight.w900,
                color: Color(0xFF111827),
              ),
            ),
          ),
          const SizedBox(width: 16),
          const Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Compatibility Match',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 20,
                    fontWeight: FontWeight.w900,
                  ),
                ),
                SizedBox(height: 6),
                Text(
                  'This score shows how well the selected items match together.',
                  style: TextStyle(
                    color: Color(0xFFD1D5DB),
                    fontSize: 13,
                    height: 1.5,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSectionTitle({required String title, required String subtitle}) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: const TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.w900,
            color: Color(0xFF111827),
          ),
        ),
        const SizedBox(height: 5),
        Text(
          subtitle,
          style: const TextStyle(
            fontSize: 13,
            color: Color(0xFF6B7280),
            fontWeight: FontWeight.w500,
            height: 1.4,
          ),
        ),
      ],
    );
  }

  Widget _buildProductItemCard(ProductModel item) {
    final String colorText = item.color.isEmpty ? 'N/A' : item.color.join(', ');
    final String styleText = item.style.isEmpty ? 'N/A' : item.style.join(', ');

    final String fallbackImageUrl = _getFallbackImageUrl(
      itemId: item.itemId,
      title: item.title,
      role: item.role,
    );

    return Container(
      margin: const EdgeInsets.only(bottom: 14),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: const Color(0xFFE5E7EB)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.05),
            blurRadius: 10,
            offset: const Offset(0, 5),
          ),
        ],
      ),
      child: Row(
        children: [
          ClipRRect(
            borderRadius: BorderRadius.circular(16),
            child: Image.network(
              item.imageUrl,
              width: 105,
              height: 120,
              fit: BoxFit.cover,
              errorBuilder: (context, error, stackTrace) {
                return Image.network(
                  fallbackImageUrl,
                  width: 105,
                  height: 120,
                  fit: BoxFit.cover,
                  errorBuilder: (context, error, stackTrace) {
                    return Container(
                      width: 105,
                      height: 120,
                      color: Colors.grey.shade200,
                      child: const Icon(
                        Icons.image_not_supported_outlined,
                        color: Colors.grey,
                      ),
                    );
                  },
                );
              },
            ),
          ),
          const SizedBox(width: 13),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  item.role.toUpperCase(),
                  style: const TextStyle(
                    fontSize: 11,
                    color: Color(0xFF6B7280),
                    fontWeight: FontWeight.w900,
                  ),
                ),
                const SizedBox(height: 5),
                Text(
                  item.title,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    fontSize: 15,
                    color: Color(0xFF111827),
                    fontWeight: FontWeight.w900,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  item.brand,
                  style: const TextStyle(
                    fontSize: 12,
                    color: Color(0xFF6B7280),
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 7),
                Text(
                  'Color: $colorText',
                  style: const TextStyle(
                    fontSize: 12,
                    color: Color(0xFF4B5563),
                    fontWeight: FontWeight.w500,
                  ),
                ),
                const SizedBox(height: 3),
                Text(
                  'Style: $styleText',
                  style: const TextStyle(
                    fontSize: 12,
                    color: Color(0xFF4B5563),
                    fontWeight: FontWeight.w500,
                  ),
                ),
                const SizedBox(height: 7),
                Text(
                  'LKR ${item.price.toStringAsFixed(0)}',
                  style: const TextStyle(
                    fontSize: 14,
                    color: Color(0xFF111827),
                    fontWeight: FontWeight.w900,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildReasonTags() {
    final visibleReasonTags = widget.outfit.reasonTags
        .where((reason) => !reason.toLowerCase().contains('ml compatibility'))
        .toList();

    if (visibleReasonTags.isEmpty) {
      return _buildEmptyCard('No reason tags available.');
    }

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: const Color(0xFFE5E7EB)),
      ),
      child: Wrap(
        spacing: 8,
        runSpacing: 8,
        children: visibleReasonTags.map((reason) {
          return Container(
            padding: const EdgeInsets.symmetric(horizontal: 11, vertical: 8),
            decoration: BoxDecoration(
              color: const Color(0xFFF3F4F6),
              borderRadius: BorderRadius.circular(30),
            ),
            child: Text(
              reason,
              style: const TextStyle(
                fontSize: 12,
                color: Color(0xFF374151),
                fontWeight: FontWeight.w700,
              ),
            ),
          );
        }).toList(),
      ),
    );
  }

  Widget _buildFeedbackSection() {
    if (_submittedRating != null) {
      return Container(
        width: double.infinity,
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: const Color(0xFFECFDF5),
          borderRadius: BorderRadius.circular(18),
          border: Border.all(color: const Color(0xFFA7F3D0)),
        ),
        child: const Text(
          'Feedback saved. This rating can be used in your evaluation results.',
          style: TextStyle(
            fontSize: 13,
            color: Color(0xFF047857),
            fontWeight: FontWeight.w800,
            height: 1.4,
          ),
        ),
      );
    }

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: const Color(0xFFE5E7EB)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Rate this outfit',
            style: TextStyle(
              fontSize: 16,
              color: Color(0xFF111827),
              fontWeight: FontWeight.w900,
            ),
          ),
          const SizedBox(height: 11),
          Row(
            children: [
              Expanded(
                child: _buildFeedbackButton(
                  label: 'Good',
                  rating: 5,
                  icon: Icons.thumb_up_alt_outlined,
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: _buildFeedbackButton(
                  label: 'Okay',
                  rating: 3,
                  icon: Icons.thumbs_up_down_outlined,
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: _buildFeedbackButton(
                  label: 'Bad',
                  rating: 1,
                  icon: Icons.thumb_down_alt_outlined,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildFeedbackButton({
    required String label,
    required int rating,
    required IconData icon,
  }) {
    return SizedBox(
      height: 42,
      child: OutlinedButton.icon(
        onPressed: _isSubmittingFeedback
            ? null
            : () {
                _submitFeedback(rating: rating, label: label);
              },
        icon: _isSubmittingFeedback
            ? const SizedBox(
                width: 14,
                height: 14,
                child: CircularProgressIndicator(strokeWidth: 2),
              )
            : Icon(icon, size: 15),
        label: Text(
          label,
          style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w900),
        ),
        style: OutlinedButton.styleFrom(
          foregroundColor: const Color(0xFF111827),
          side: const BorderSide(color: Color(0xFFD1D5DB)),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(14),
          ),
        ),
      ),
    );
  }

  Widget _buildScoreBreakdownCard() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: const Color(0xFFE5E7EB)),
      ),
      child: Column(
        children: [
          _buildScoreRow(
            label: 'Style Match',
            value: widget.outfit.scoreBreakdown.styleMatchScore,
          ),
          _buildScoreRow(
            label: 'Color Match',
            value: widget.outfit.scoreBreakdown.colorMatchScore,
          ),
          _buildScoreRow(
            label: 'Category Match',
            value: widget.outfit.scoreBreakdown.categoryMatchScore,
          ),
          _buildScoreRow(
            label: 'Occasion Match',
            value: widget.outfit.scoreBreakdown.occasionMatchScore,
          ),
        ],
      ),
    );
  }

  Widget _buildScoreRow({required String label, required double value}) {
    final int percentage = (value * 100).round().clamp(0, 100);

    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        children: [
          SizedBox(
            width: 120,
            child: Text(
              label,
              style: const TextStyle(
                fontSize: 13,
                color: Color(0xFF4B5563),
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
          Expanded(
            child: ClipRRect(
              borderRadius: BorderRadius.circular(20),
              child: LinearProgressIndicator(
                value: percentage / 100,
                minHeight: 9,
                backgroundColor: const Color(0xFFE5E7EB),
                valueColor: const AlwaysStoppedAnimation<Color>(
                  Color(0xFF111827),
                ),
              ),
            ),
          ),
          const SizedBox(width: 10),
          Text(
            '$percentage%',
            style: const TextStyle(
              fontSize: 13,
              color: Color(0xFF111827),
              fontWeight: FontWeight.w900,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildAppliedFiltersCard() {
    final filters = widget.outfit.appliedFilters;
    final preferredColors = filters.preferredColors.isEmpty
        ? 'N/A'
        : filters.preferredColors.join(', ');
    final excludedCategories = filters.excludedCategories.isEmpty
        ? 'None'
        : filters.excludedCategories.join(', ');

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: const Color(0xFFE5E7EB)),
      ),
      child: Column(
        children: [
          _buildFilterRow(
            label: 'Minimum Price',
            value: 'LKR ${filters.minPrice.toStringAsFixed(0)}',
          ),
          _buildFilterRow(
            label: 'Maximum Price',
            value: 'LKR ${filters.maxPrice.toStringAsFixed(0)}',
          ),
          _buildFilterRow(label: 'Preferred Colors', value: preferredColors),
          _buildFilterRow(
            label: 'Excluded Categories',
            value: excludedCategories,
          ),
          _buildFilterRow(
            label: 'Max Items / Category',
            value: filters.maxItemsPerCategory.toString(),
          ),
        ],
      ),
    );
  }

  Widget _buildFilterRow({required String label, required String value}) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 11),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 145,
            child: Text(
              label,
              style: const TextStyle(
                fontSize: 13,
                color: Color(0xFF6B7280),
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
          Expanded(
            child: Text(
              value,
              textAlign: TextAlign.right,
              style: const TextStyle(
                fontSize: 13,
                color: Color(0xFF111827),
                fontWeight: FontWeight.w900,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildActionButtons() {
    return Row(
      children: [
        Expanded(
          child: SizedBox(
            height: 50,
            child: ElevatedButton.icon(
              onPressed: _isSaving || _isSaved ? null : _saveOutfit,
              icon: _isSaving
                  ? const SizedBox(
                      width: 17,
                      height: 17,
                      child: CircularProgressIndicator(
                        strokeWidth: 2.2,
                        color: Colors.white,
                      ),
                    )
                  : Icon(_isSaved ? Icons.favorite : Icons.favorite_border),
              label: Text(
                _isSaving
                    ? 'Saving...'
                    : _isSaved
                    ? 'Saved'
                    : 'Save Outfit',
                style: const TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w900,
                ),
              ),
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF111827),
                disabledBackgroundColor: _isSaved
                    ? const Color(0xFF16A34A)
                    : const Color(0xFF6B7280),
                foregroundColor: Colors.white,
                disabledForegroundColor: Colors.white,
                elevation: 0,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(16),
                ),
              ),
            ),
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: SizedBox(
            height: 50,
            child: OutlinedButton.icon(
              onPressed: _generateAgain,
              icon: const Icon(Icons.refresh),
              label: const Text(
                'Generate Again',
                style: TextStyle(fontSize: 14, fontWeight: FontWeight.w900),
              ),
              style: OutlinedButton.styleFrom(
                foregroundColor: const Color(0xFF111827),
                side: const BorderSide(color: Color(0xFF111827)),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(16),
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildEmptyCard(String message) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: const Color(0xFFE5E7EB)),
      ),
      child: Text(
        message,
        style: const TextStyle(
          fontSize: 13,
          color: Color(0xFF6B7280),
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }
}
