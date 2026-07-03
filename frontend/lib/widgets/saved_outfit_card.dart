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
      height: 150,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        itemCount: savedOutfit.items.length,
        separatorBuilder: (context, index) => const SizedBox(width: 12),
        itemBuilder: (context, index) {
          final item = savedOutfit.items[index];

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

  Widget _buildItemTitleText() {
    final itemNames = savedOutfit.items.map((item) => item.title).join(' + ');

    return Text(
      itemNames.isEmpty ? 'No item names available' : itemNames,
      style: const TextStyle(
        fontSize: 15,
        height: 1.4,
        fontWeight: FontWeight.w900,
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