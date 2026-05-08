import 'package:flutter/material.dart';

import '../models/outfit_model.dart';
import '../models/product_model.dart';
import '../services/outfit_api_service.dart';
import '../widgets/outfit_card.dart';

class CompleteTheLookScreen extends StatefulWidget {
  final ProductModel selectedProduct;

  const CompleteTheLookScreen({
    super.key,
    required this.selectedProduct,
  });

  @override
  State<CompleteTheLookScreen> createState() => _CompleteTheLookScreenState();
}

class _CompleteTheLookScreenState extends State<CompleteTheLookScreen> {
  final OutfitApiService _outfitApiService = OutfitApiService();

  final List<String> _occasions = [
    'casual',
    'formal',
    'party',
    'office',
    'sports',
  ];

  String _selectedOccasion = 'casual';
  bool _isLoading = false;
  String? _errorMessage;
  OutfitGenerateResponse? _response;

  Future<void> _generateOutfits() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
      _response = null;
    });

    try {
      final result = await _outfitApiService.generateOutfits(
        userId: 'USR001',
        selectedItemId: widget.selectedProduct.itemId,
        occasion: _selectedOccasion,
        maxOutfits: 5,
        minPrice: 3000,
        maxPrice: 10000,
        preferredColors: ['white', 'blue', 'black'],
        excludedCategories: [],
        maxItemsPerCategory: 5,
      );

      setState(() {
        _response = result;
      });
    } catch (error) {
      setState(() {
        _errorMessage = error.toString().replaceFirst('Exception: ', '');
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  @override
  void initState() {
    super.initState();

    // Auto-generate outfits when screen opens.
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _generateOutfits();
    });
  }

  @override
  Widget build(BuildContext context) {
    final outfits = _response?.outfits ?? [];

    return Scaffold(
      backgroundColor: const Color(0xFFF8F8F8),
      body: SafeArea(
        child: Column(
          children: [
            _buildTopBar(context),
            Expanded(
              child: RefreshIndicator(
                onRefresh: _generateOutfits,
                child: ListView(
                  padding: const EdgeInsets.all(18),
                  children: [
                    _buildSelectedProductCard(),
                    const SizedBox(height: 20),
                    _buildOccasionSection(),
                    const SizedBox(height: 20),
                    _buildGenerateButton(),
                    const SizedBox(height: 22),
                    _buildStatusSection(outfits.length),
                    const SizedBox(height: 16),
                    if (_isLoading) _buildLoadingSection(),
                    if (_errorMessage != null) _buildErrorSection(),
                    if (!_isLoading && _errorMessage == null && outfits.isEmpty)
                      _buildEmptySection(),
                    if (!_isLoading && _errorMessage == null)
                      ...outfits.map(
                        (outfit) => OutfitCard(outfit: outfit),
                      ),
                  ],
                ),
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
              'Complete the Look',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.w900,
                color: Color(0xFF111827),
              ),
            ),
          ),
          IconButton(
            onPressed: _generateOutfits,
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
    );
  }

  Widget _buildSelectedProductCard() {
    final product = widget.selectedProduct;
    final colorText = product.color.isEmpty ? 'N/A' : product.color.join(', ');
    final styleText = product.style.isEmpty ? 'N/A' : product.style.join(', ');

    return Container(
      padding: const EdgeInsets.all(14),
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
          ClipRRect(
            borderRadius: BorderRadius.circular(18),
            child: Image.network(
              product.imageUrl,
              width: 95,
              height: 110,
              fit: BoxFit.cover,
              errorBuilder: (context, error, stackTrace) {
                return Container(
                  width: 95,
                  height: 110,
                  color: Colors.grey.shade300,
                  child: const Icon(
                    Icons.image_not_supported_outlined,
                    color: Colors.grey,
                  ),
                );
              },
            ),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Selected Item',
                  style: TextStyle(
                    color: Color(0xFFD1D5DB),
                    fontSize: 12,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  product.title,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 17,
                    fontWeight: FontWeight.w900,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  product.brand,
                  style: const TextStyle(
                    color: Color(0xFFE5E7EB),
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  'Role: ${product.role} | Color: $colorText | Style: $styleText',
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    color: Color(0xFFD1D5DB),
                    fontSize: 12,
                    height: 1.4,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildOccasionSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Choose Occasion',
          style: TextStyle(
            fontSize: 19,
            fontWeight: FontWeight.w900,
            color: Color(0xFF111827),
          ),
        ),
        const SizedBox(height: 6),
        const Text(
          'Select the occasion to generate more suitable outfit combinations.',
          style: TextStyle(
            fontSize: 13,
            color: Color(0xFF6B7280),
            fontWeight: FontWeight.w500,
          ),
        ),
        const SizedBox(height: 14),
        Wrap(
          spacing: 10,
          runSpacing: 10,
          children: _occasions.map((occasion) {
            final bool isSelected = _selectedOccasion == occasion;

            return ChoiceChip(
              label: Text(
                occasion[0].toUpperCase() + occasion.substring(1),
              ),
              selected: isSelected,
              onSelected: (selected) {
                if (!selected) {
                  return;
                }

                setState(() {
                  _selectedOccasion = occasion;
                });

                _generateOutfits();
              },
              selectedColor: const Color(0xFF111827),
              backgroundColor: Colors.white,
              labelStyle: TextStyle(
                color: isSelected ? Colors.white : const Color(0xFF111827),
                fontWeight: FontWeight.w800,
              ),
              side: BorderSide(
                color: isSelected
                    ? const Color(0xFF111827)
                    : const Color(0xFFE5E7EB),
              ),
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(30),
              ),
            );
          }).toList(),
        ),
      ],
    );
  }

  Widget _buildGenerateButton() {
    return SizedBox(
      width: double.infinity,
      height: 56,
      child: ElevatedButton.icon(
        onPressed: _isLoading ? null : _generateOutfits,
        icon: _isLoading
            ? const SizedBox(
                width: 18,
                height: 18,
                child: CircularProgressIndicator(
                  strokeWidth: 2.4,
                  color: Colors.white,
                ),
              )
            : const Icon(Icons.auto_awesome),
        label: Text(
          _isLoading ? 'Generating Outfits...' : 'Generate Compatible Outfits',
          style: const TextStyle(
            fontSize: 15,
            fontWeight: FontWeight.w900,
          ),
        ),
        style: ElevatedButton.styleFrom(
          backgroundColor: const Color(0xFF111827),
          disabledBackgroundColor: const Color(0xFF6B7280),
          foregroundColor: Colors.white,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(18),
          ),
          elevation: 0,
        ),
      ),
    );
  }

  Widget _buildStatusSection(int outfitCount) {
    String title = 'Outfit Suggestions';
    String subtitle = 'Tap generate to create compatible outfits.';

    if (_isLoading) {
      title = 'Generating...';
      subtitle = 'Please wait while we find the best matching outfits.';
    } else if (_errorMessage != null) {
      title = 'Could not generate outfits';
      subtitle = 'Check backend connection and try again.';
    } else if (_response != null) {
      title = 'Found $outfitCount outfits for you';
      subtitle = _response!.message;
    }

    return Row(
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: const TextStyle(
                  fontSize: 21,
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
          ),
        ),
      ],
    );
  }

  Widget _buildLoadingSection() {
    return Container(
      padding: const EdgeInsets.all(22),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: const Color(0xFFE5E7EB)),
      ),
      child: const Column(
        children: [
          CircularProgressIndicator(
            color: Color(0xFF111827),
          ),
          SizedBox(height: 14),
          Text(
            'Generating compatible outfits...',
            style: TextStyle(
              fontSize: 14,
              color: Color(0xFF4B5563),
              fontWeight: FontWeight.w700,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildErrorSection() {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: const Color(0xFFFEF2F2),
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: const Color(0xFFFECACA)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Row(
            children: [
              Icon(
                Icons.error_outline,
                color: Color(0xFFB91C1C),
              ),
              SizedBox(width: 8),
              Text(
                'Backend Connection Error',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w900,
                  color: Color(0xFFB91C1C),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Text(
            _errorMessage ?? 'Unknown error occurred',
            style: const TextStyle(
              fontSize: 13,
              color: Color(0xFF7F1D1D),
              height: 1.5,
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(height: 14),
          SizedBox(
            width: double.infinity,
            child: OutlinedButton.icon(
              onPressed: _generateOutfits,
              icon: const Icon(Icons.refresh),
              label: const Text('Try Again'),
              style: OutlinedButton.styleFrom(
                foregroundColor: const Color(0xFFB91C1C),
                side: const BorderSide(color: Color(0xFFB91C1C)),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(14),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildEmptySection() {
    return Container(
      padding: const EdgeInsets.all(22),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: const Color(0xFFE5E7EB)),
      ),
      child: const Column(
        children: [
          Icon(
            Icons.checkroom_outlined,
            size: 44,
            color: Color(0xFF9CA3AF),
          ),
          SizedBox(height: 12),
          Text(
            'No outfits available yet',
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.w900,
              color: Color(0xFF111827),
            ),
          ),
          SizedBox(height: 6),
          Text(
            'Try another occasion or check whether matching products exist in the backend database.',
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 13,
              color: Color(0xFF6B7280),
              height: 1.5,
            ),
          ),
        ],
      ),
    );
  }
}