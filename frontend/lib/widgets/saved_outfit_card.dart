import 'package:flutter/material.dart';

import '../models/saved_outfit_model.dart';

class SavedOutfitCard extends StatelessWidget {
  final SavedOutfitModel savedOutfit;
  final VoidCallback onReuse;
  final VoidCallback onRemove;

  const SavedOutfitCard({
    super.key,
    required this.savedOutfit,
    required this.onReuse,
    required this.onRemove,
  });

  @override
  Widget build(BuildContext context) {
    final int scorePercentage =
        (savedOutfit.compatibilityScore * 100).round().clamp(0, 100);

    return Container(
      margin: const EdgeInsets.only(bottom: 18),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: const Color(0xFFE5E7EB)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.06),
            blurRadius: 12,
            offset: const Offset(0, 6),
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
          _buildItemTitleText(),
          const SizedBox(height: 14),
          _buildReasonTags(),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: _buildReuseButton(),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _buildRemoveButton(),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildHeader(int scorePercentage) {
    return Row(
      children: [
        const Expanded(
          child: Text(
            'Saved Outfit',
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
    if (savedOutfit.items.isEmpty) {
      return Container(
        height: 120,
        alignment: Alignment.center,
        decoration: BoxDecoration(
          color: Colors.grey.shade100,
          borderRadius: BorderRadius.circular(18),
        ),
        child: const Text(
          'No items found',
          style: TextStyle(color: Colors.grey),
        ),
      );
    }

    return SizedBox(
      height: 125,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        itemCount: savedOutfit.items.length,
        separatorBuilder: (context, index) => const SizedBox(width: 12),
        itemBuilder: (context, index) {
          final item = savedOutfit.items[index];

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
                    fontWeight: FontWeight.w900,
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

  Widget _buildItemTitleText() {
    final itemNames = savedOutfit.items.map((item) => item.title).join(' + ');

    return Text(
      itemNames.isEmpty ? 'No item names available' : itemNames,
      style: const TextStyle(
        fontSize: 15,
        height: 1.4,
        fontWeight: FontWeight.w800,
        color: Color(0xFF111827),
      ),
    );
  }

  Widget _buildReasonTags() {
    if (savedOutfit.reasonTags.isEmpty) {
      return const SizedBox.shrink();
    }

    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: savedOutfit.reasonTags.map((reason) {
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

  Widget _buildReuseButton() {
    return SizedBox(
      height: 46,
      child: ElevatedButton.icon(
        onPressed: onReuse,
        icon: const Icon(Icons.replay),
        label: const Text(
          'Reuse',
          style: TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w900,
          ),
        ),
        style: ElevatedButton.styleFrom(
          backgroundColor: const Color(0xFF111827),
          foregroundColor: Colors.white,
          elevation: 0,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
          ),
        ),
      ),
    );
  }

  Widget _buildRemoveButton() {
    return SizedBox(
      height: 46,
      child: OutlinedButton.icon(
        onPressed: onRemove,
        icon: const Icon(Icons.delete_outline),
        label: const Text(
          'Remove',
          style: TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w900,
          ),
        ),
        style: OutlinedButton.styleFrom(
          foregroundColor: const Color(0xFFB91C1C),
          side: const BorderSide(color: Color(0xFFB91C1C)),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
          ),
        ),
      ),
    );
  }
}