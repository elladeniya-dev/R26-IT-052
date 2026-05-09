import 'package:flutter/material.dart';

import '../models/outfit_model.dart';
import '../screens/outfit_detail_screen.dart';
import '../services/saved_outfit_api_service.dart';

class OutfitCard extends StatefulWidget {
  final OutfitModel outfit;

  const OutfitCard({
    super.key,
    required this.outfit,
  });

  @override
  State<OutfitCard> createState() => _OutfitCardState();
}

class _OutfitCardState extends State<OutfitCard> {
  final SavedOutfitApiService _savedOutfitApiService = SavedOutfitApiService();

  bool _isSaving = false;
  bool _isSaved = false;

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

  void _openOutfitDetails() {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => OutfitDetailScreen(
          outfit: widget.outfit,
        ),
      ),
    );
  }

  void _showSnackBar(String message) {
    if (!mounted) {
      return;
    }

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final int scorePercentage =
        (widget.outfit.compatibilityScore * 100).round().clamp(0, 100);

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
            _buildScoreBreakdown(),
            const SizedBox(height: 14),
            Row(
              children: [
                Expanded(
                  child: _buildSaveButton(),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _buildViewDetailsButton(),
                ),
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
              fontWeight: FontWeight.w800,
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
              fontWeight: FontWeight.w800,
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
      height: 125,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        itemCount: widget.outfit.items.length,
        separatorBuilder: (context, index) => const SizedBox(width: 12),
        itemBuilder: (context, index) {
          final item = widget.outfit.items[index];

          return SizedBox(
            width: 105,
            child: Column(
              children: [
                Expanded(
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(16),
                    child: Image.network(
                      item.imageUrl,
                      width: 105,
                      height: 95,
                      fit: BoxFit.cover,
                      errorBuilder: (context, error, stackTrace) {
                        return Container(
                          width: 105,
                          height: 95,
                          color: Colors.grey.shade200,
                          child: const Icon(
                            Icons.image_not_supported_outlined,
                            color: Colors.grey,
                            size: 32,
                          ),
                        );
                      },
                    ),
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  item.role.toUpperCase(),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w800,
                    color: Color(0xFF6B7280),
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
        fontWeight: FontWeight.w700,
        color: Color(0xFF111827),
        height: 1.4,
      ),
    );
  }

  Widget _buildReasonTags() {
    if (widget.outfit.reasonTags.isEmpty) {
      return const SizedBox.shrink();
    }

    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: widget.outfit.reasonTags.map((reason) {
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
              fontWeight: FontWeight.w600,
              color: Color(0xFF374151),
            ),
          ),
        );
      }).toList(),
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
              fontWeight: FontWeight.w800,
              color: Color(0xFF111827),
            ),
          ),
          const SizedBox(height: 10),
          _buildScoreRow(
            'Style',
            widget.outfit.scoreBreakdown.styleMatchScore,
          ),
          _buildScoreRow(
            'Color',
            widget.outfit.scoreBreakdown.colorMatchScore,
          ),
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
                fontWeight: FontWeight.w600,
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
              fontWeight: FontWeight.w700,
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
            : Icon(
                _isSaved ? Icons.favorite : Icons.favorite_border,
              ),
        label: Text(
          _isSaving
              ? 'Saving...'
              : _isSaved
                  ? 'Saved'
                  : 'Save',
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
          style: TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w900,
          ),
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