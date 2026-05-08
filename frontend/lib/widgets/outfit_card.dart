import 'package:flutter/material.dart';

import '../models/outfit_model.dart';

class OutfitCard extends StatelessWidget {
  final OutfitModel outfit;

  const OutfitCard({
    super.key,
    required this.outfit,
  });

  @override
  Widget build(BuildContext context) {
    final int scorePercentage =
        (outfit.compatibilityScore * 100).round().clamp(0, 100);

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
        ],
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
    if (outfit.items.isEmpty) {
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
        itemCount: outfit.items.length,
        separatorBuilder: (context, index) => const SizedBox(width: 12),
        itemBuilder: (context, index) {
          final item = outfit.items[index];

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
    final names = outfit.items.map((item) => item.title).join(' + ');

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
    if (outfit.reasonTags.isEmpty) {
      return const SizedBox.shrink();
    }

    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: outfit.reasonTags.map((reason) {
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
            outfit.scoreBreakdown.styleMatchScore,
          ),
          _buildScoreRow(
            'Color',
            outfit.scoreBreakdown.colorMatchScore,
          ),
          _buildScoreRow(
            'Category',
            outfit.scoreBreakdown.categoryMatchScore,
          ),
          _buildScoreRow(
            'Occasion',
            outfit.scoreBreakdown.occasionMatchScore,
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
}