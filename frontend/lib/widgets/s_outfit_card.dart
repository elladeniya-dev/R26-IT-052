import 'package:flutter/material.dart';

import '../models/s_outfit_model.dart';
import '../screens/s_outfit_detail_screen.dart';
import '../services/s_outfit_feedback_api_service.dart';
import '../services/s_saved_outfit_api_service.dart';

class OutfitCard extends StatefulWidget {
  final OutfitModel outfit;
  final String userId;
  final VoidCallback? onGenerateAgain;

  const OutfitCard({
    super.key,
    required this.outfit,
    this.userId = 'USR001',
    this.onGenerateAgain,
  });

  @override
  State<OutfitCard> createState() => _OutfitCardState();
}

class _OutfitCardState extends State<OutfitCard> {
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

  void _openOutfitDetails() {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => OutfitDetailScreen(
          outfit: widget.outfit,
          userId: widget.userId,
          onGenerateAgain: widget.onGenerateAgain,
        ),
      ),
    );
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
    final int scorePercentage = (widget.outfit.compatibilityScore * 100)
        .round()
        .clamp(0, 100);

    return Container(
      margin: const EdgeInsets.only(bottom: 18),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(22),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.08),
            blurRadius: 14,
            offset: const Offset(0, 7),
          ),
        ],
      ),
      child: InkWell(
        onTap: _openOutfitDetails,
        borderRadius: BorderRadius.circular(22),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildHeader(scorePercentage),
            const SizedBox(height: 14),
            _buildItemImages(),
            const SizedBox(height: 14),
            _buildItemNames(),
            const SizedBox(height: 14),
            _buildReasonTags(),
            const SizedBox(height: 14),
            _buildFeedbackSection(),
            const SizedBox(height: 14),
            _buildScoreBreakdown(),
            const SizedBox(height: 14),
            Row(
              children: [
                Expanded(child: _buildSaveButton()),
                const SizedBox(width: 12),
                Expanded(child: _buildViewDetailsButton()),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader(int scorePercentage) {
    return Row(
      children: [
        const Expanded(
          child: Text(
            'Suggested Outfit',
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.w900,
              color: Color(0xFF111827),
            ),
          ),
        ),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 7),
          decoration: BoxDecoration(
            color: const Color(0xFFDCFCE7),
            borderRadius: BorderRadius.circular(30),
          ),
          child: Text(
            '$scorePercentage% Match',
            style: const TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w900,
              color: Color(0xFF166534),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildItemImages() {
    if (widget.outfit.items.isEmpty) {
      return Container(
        height: 120,
        alignment: Alignment.center,
        decoration: BoxDecoration(
          color: Colors.grey.shade100,
          borderRadius: BorderRadius.circular(18),
        ),
        child: const Text(
          'No items found for this outfit',
          style: TextStyle(color: Colors.grey),
        ),
      );
    }

    return SizedBox(
      height: 150,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        itemCount: widget.outfit.items.length,
        separatorBuilder: (context, index) => const SizedBox(width: 12),
        itemBuilder: (context, index) {
          final item = widget.outfit.items[index];

          final String fallbackImageUrl = _getFallbackImageUrl(
            itemId: item.itemId,
            title: item.title,
            role: item.role,
          );

          return SizedBox(
            width: 135,
            child: Column(
              children: [
                Expanded(
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(16),
                    child: Image.network(
                      item.imageUrl,
                      width: 135,
                      height: 115,
                      fit: BoxFit.cover,
                      errorBuilder: (context, error, stackTrace) {
                        return Image.network(
                          fallbackImageUrl,
                          width: 135,
                          height: 115,
                          fit: BoxFit.cover,
                          errorBuilder: (context, error, stackTrace) {
                            return Container(
                              width: 135,
                              height: 115,
                              color: Colors.grey.shade200,
                              child: const Icon(
                                Icons.image_not_supported_outlined,
                                color: Colors.grey,
                                size: 32,
                              ),
                            );
                          },
                        );
                      },
                    ),
                  ),
                ),
                const SizedBox(height: 7),
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 9,
                    vertical: 4,
                  ),
                  decoration: BoxDecoration(
                    color: const Color(0xFF111827),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Text(
                    item.role.toUpperCase(),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.w900,
                      color: Colors.white,
                    ),
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildItemNames() {
    final names = widget.outfit.items.map((item) => item.title).join(' + ');

    return Text(
      names.isEmpty ? 'No item names available' : names,
      style: const TextStyle(
        fontSize: 15,
        fontWeight: FontWeight.w900,
        color: Color(0xFF111827),
        height: 1.4,
      ),
    );
  }

  Widget _buildReasonTags() {
    final visibleReasonTags = widget.outfit.reasonTags
        .where((reason) => !reason.toLowerCase().contains('ml compatibility'))
        .toList();

    if (visibleReasonTags.isEmpty) {
      return const SizedBox.shrink();
    }

    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: visibleReasonTags.map((reason) {
        return Container(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
          decoration: BoxDecoration(
            color: const Color(0xFFF3F4F6),
            borderRadius: BorderRadius.circular(30),
          ),
          child: Text(
            reason,
            style: const TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w700,
              color: Color(0xFF374151),
            ),
          ),
        );
      }).toList(),
    );
  }

  Widget _buildFeedbackSection() {
    if (_submittedRating != null) {
      return Container(
        width: double.infinity,
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 11),
        decoration: BoxDecoration(
          color: const Color(0xFFECFDF5),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: const Color(0xFFA7F3D0)),
        ),
        child: const Text(
          'Feedback saved. Thank you for rating this outfit.',
          style: TextStyle(
            fontSize: 12,
            color: Color(0xFF047857),
            fontWeight: FontWeight.w800,
          ),
        ),
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Rate this outfit',
          style: TextStyle(
            fontSize: 14,
            color: Color(0xFF111827),
            fontWeight: FontWeight.w900,
          ),
        ),
        const SizedBox(height: 9),
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
    );
  }

  Widget _buildFeedbackButton({
    required String label,
    required int rating,
    required IconData icon,
  }) {
    return SizedBox(
      height: 40,
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

  Widget _buildScoreBreakdown() {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFFF9FAFB),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFFE5E7EB)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Score Breakdown',
            style: TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.w900,
              color: Color(0xFF111827),
            ),
          ),
          const SizedBox(height: 10),
          _buildScoreRow('Style', widget.outfit.scoreBreakdown.styleMatchScore),
          _buildScoreRow('Color', widget.outfit.scoreBreakdown.colorMatchScore),
          _buildScoreRow(
            'Category',
            widget.outfit.scoreBreakdown.categoryMatchScore,
          ),
          _buildScoreRow(
            'Occasion',
            widget.outfit.scoreBreakdown.occasionMatchScore,
          ),
        ],
      ),
    );
  }

  Widget _buildScoreRow(String label, double value) {
    final int percentage = (value * 100).round().clamp(0, 100);

    return Padding(
      padding: const EdgeInsets.only(bottom: 7),
      child: Row(
        children: [
          SizedBox(
            width: 75,
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
                minHeight: 8,
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
              fontWeight: FontWeight.w900,
              color: Color(0xFF111827),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSaveButton() {
    return SizedBox(
      height: 46,
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
              : 'Save',
          style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w900),
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
    );
  }

  Widget _buildViewDetailsButton() {
    return SizedBox(
      height: 46,
      child: OutlinedButton.icon(
        onPressed: _openOutfitDetails,
        icon: const Icon(Icons.arrow_forward_ios, size: 14),
        label: const Text(
          'Details',
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
    );
  }
}
