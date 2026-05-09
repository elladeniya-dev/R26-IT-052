import 'package:flutter/material.dart';

import '../models/outfit_model.dart';
import '../models/product_model.dart';
import '../services/outfit_api_service.dart';
import '../widgets/outfit_card.dart';
import 'saved_outfits_screen.dart';

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

  final TextEditingController _minPriceController =
      TextEditingController(text: '3000');
  final TextEditingController _maxPriceController =
      TextEditingController(text: '10000');

  final List<String> _occasions = [
    'casual',
    'formal',
    'party',
    'office',
    'sports',
  ];

  final List<String> _availableColors = [
    'white',
    'blue',
    'black',
    'red',
    'green',
    'brown',
    'pink',
  ];

  final List<String> _availableExcludedCategories = [
    'outerwear',
    'footwear',
    'accessory',
  ];

  String _selectedOccasion = 'casual';
  int _maxOutfits = 5;
  int _maxItemsPerCategory = 5;

  final List<String> _selectedPreferredColors = [
    'white',
    'blue',
    'black',
  ];

  final List<String> _selectedExcludedCategories = [];

  bool _isLoading = false;
  String? _errorMessage;
  OutfitGenerateResponse? _response;

  @override
  void dispose() {
    _minPriceController.dispose();
    _maxPriceController.dispose();
    super.dispose();
  }

  Future<void> _generateOutfits() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
      _response = null;
    });

    final double minPrice =
        double.tryParse(_minPriceController.text.trim()) ?? 3000;
    final double maxPrice =
        double.tryParse(_maxPriceController.text.trim()) ?? 10000;

    try {
      final result = await _outfitApiService.generateOutfits(
        userId: 'USR001',
        selectedItemId: widget.selectedProduct.itemId,
        occasion: _selectedOccasion,
        maxOutfits: _maxOutfits,
        minPrice: minPrice,
        maxPrice: maxPrice,
        preferredColors: _selectedPreferredColors,
        excludedCategories: _selectedExcludedCategories,
        maxItemsPerCategory: _maxItemsPerCategory,
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

  void _togglePreferredColor(String color) {
    setState(() {
      if (_selectedPreferredColors.contains(color)) {
        _selectedPreferredColors.remove(color);
      } else {
        _selectedPreferredColors.add(color);
      }
    });
  }

  void _toggleExcludedCategory(String category) {
    setState(() {
      if (_selectedExcludedCategories.contains(category)) {
        _selectedExcludedCategories.remove(category);
      } else {
        _selectedExcludedCategories.add(category);
      }
    });
  }

  @override
  void initState() {
    super.initState();

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
                    _buildFilterPanel(),
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
          Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              IconButton(
                tooltip: 'Saved Outfits',
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (context) => const SavedOutfitsScreen(),
                    ),
                  );
                },
                icon: const Icon(Icons.favorite),
              ),
              IconButton(
                tooltip: 'Refresh Outfits',
                onPressed: _generateOutfits,
                icon: const Icon(Icons.refresh),
              ),
            ],
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
          'Select the occasion to generate suitable outfit combinations.',
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

  Widget _buildFilterPanel() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: const Color(0xFFE5E7EB)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.05),
            blurRadius: 12,
            offset: const Offset(0, 6),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Row(
            children: [
              Icon(
                Icons.tune,
                color: Color(0xFF111827),
              ),
              SizedBox(width: 8),
              Text(
                'Filters',
                style: TextStyle(
                  fontSize: 19,
                  fontWeight: FontWeight.w900,
                  color: Color(0xFF111827),
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          const Text(
            'Customize the outfit generation request sent to the backend.',
            style: TextStyle(
              fontSize: 13,
              color: Color(0xFF6B7280),
              fontWeight: FontWeight.w500,
              height: 1.4,
            ),
          ),
          const SizedBox(height: 18),
          Row(
            children: [
              Expanded(
                child: _buildPriceInput(
                  label: 'Min Price',
                  controller: _minPriceController,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _buildPriceInput(
                  label: 'Max Price',
                  controller: _maxPriceController,
                ),
              ),
            ],
          ),
          const SizedBox(height: 18),
          _buildDropdownRow(
            title: 'Max Outfits',
            value: _maxOutfits,
            values: const [1, 2, 3, 4, 5],
            onChanged: (value) {
              if (value == null) {
                return;
              }

              setState(() {
                _maxOutfits = value;
              });
            },
          ),
          const SizedBox(height: 14),
          _buildDropdownRow(
            title: 'Max Items Per Category',
            value: _maxItemsPerCategory,
            values: const [1, 2, 3, 4, 5],
            onChanged: (value) {
              if (value == null) {
                return;
              }

              setState(() {
                _maxItemsPerCategory = value;
              });
            },
          ),
          const SizedBox(height: 18),
          _buildChipSection(
            title: 'Preferred Colors',
            subtitle: 'Select colors you prefer in the generated outfits.',
            options: _availableColors,
            selectedOptions: _selectedPreferredColors,
            onTap: _togglePreferredColor,
          ),
          const SizedBox(height: 18),
          _buildChipSection(
            title: 'Excluded Categories',
            subtitle: 'Avoid categories you do not want in the outfit.',
            options: _availableExcludedCategories,
            selectedOptions: _selectedExcludedCategories,
            onTap: _toggleExcludedCategory,
          ),
        ],
      ),
    );
  }

  Widget _buildPriceInput({
    required String label,
    required TextEditingController controller,
  }) {
    return TextField(
      controller: controller,
      keyboardType: TextInputType.number,
      decoration: InputDecoration(
        labelText: label,
        prefixText: 'LKR ',
        filled: true,
        fillColor: const Color(0xFFF9FAFB),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: const BorderSide(color: Color(0xFFE5E7EB)),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: const BorderSide(color: Color(0xFFE5E7EB)),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: const BorderSide(color: Color(0xFF111827), width: 1.4),
        ),
      ),
    );
  }

  Widget _buildDropdownRow({
    required String title,
    required int value,
    required List<int> values,
    required ValueChanged<int?> onChanged,
  }) {
    return Row(
      children: [
        Expanded(
          child: Text(
            title,
            style: const TextStyle(
              fontSize: 14,
              color: Color(0xFF374151),
              fontWeight: FontWeight.w800,
            ),
          ),
        ),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 12),
          decoration: BoxDecoration(
            color: const Color(0xFFF9FAFB),
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: const Color(0xFFE5E7EB)),
          ),
          child: DropdownButtonHideUnderline(
            child: DropdownButton<int>(
              value: value,
              items: values.map((item) {
                return DropdownMenuItem<int>(
                  value: item,
                  child: Text(
                    item.toString(),
                    style: const TextStyle(
                      fontWeight: FontWeight.w800,
                      color: Color(0xFF111827),
                    ),
                  ),
                );
              }).toList(),
              onChanged: onChanged,
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildChipSection({
    required String title,
    required String subtitle,
    required List<String> options,
    required List<String> selectedOptions,
    required Function(String) onTap,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: const TextStyle(
            fontSize: 15,
            color: Color(0xFF111827),
            fontWeight: FontWeight.w900,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          subtitle,
          style: const TextStyle(
            fontSize: 12,
            color: Color(0xFF6B7280),
            height: 1.4,
          ),
        ),
        const SizedBox(height: 10),
        Wrap(
          spacing: 9,
          runSpacing: 9,
          children: options.map((option) {
            final bool isSelected = selectedOptions.contains(option);

            return FilterChip(
              label: Text(
                option[0].toUpperCase() + option.substring(1),
              ),
              selected: isSelected,
              onSelected: (_) {
                onTap(option);
              },
              selectedColor: const Color(0xFF111827),
              backgroundColor: const Color(0xFFF9FAFB),
              checkmarkColor: Colors.white,
              labelStyle: TextStyle(
                color: isSelected ? Colors.white : const Color(0xFF111827),
                fontWeight: FontWeight.w800,
              ),
              side: BorderSide(
                color: isSelected
                    ? const Color(0xFF111827)
                    : const Color(0xFFE5E7EB),
              ),
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