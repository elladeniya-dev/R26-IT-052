import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import '../models/s_product_model.dart';
import '../widgets/s_nav_bar.dart';
import '../widgets/s_product_card.dart';
import 's_evaluation_summary_screen.dart';
import 's_notifications_screen.dart';
import 's_product_detail_screen.dart';
import 's_saved_outfits_screen.dart';
import 's_search_screen.dart';

class ProductListScreen extends StatefulWidget {
  const ProductListScreen({super.key});

  @override
  State<ProductListScreen> createState() => _ProductListScreenState();
}

class _ProductListScreenState extends State<ProductListScreen> {
  static String _lastSearchQuery = '';
  static List<ProductModel> _lastSearchProducts = [];
  static List<String> _persistedHistory = [];

  int _selectedBottomIndex = BottomNavTab.home;
  int _unreadNotifications = 2; // matches sample data unread count

  String _selectedStyleFilter = 'All';
  final ImagePicker _imagePicker = ImagePicker();

  String _searchQuery = _lastSearchQuery;
  List<ProductModel> _cachedSearchProducts = List<ProductModel>.from(
    _lastSearchProducts,
  );
  List<String> _searchHistory = List<String>.from(_persistedHistory);

  static final List<ProductModel> sampleProducts = [
    ProductModel(
      itemId: 'P001',
      title: 'Black Casual Crop Top',
      role: 'top',
      color: ['black'],
      style: ['casual'],
      imageUrl:
          'https://images.unsplash.com/photo-1529139574466-a303027c1d8b?w=600',
      productUrl: 'https://example.com/products/black-crop-top',
      price: 3500,
      brand: 'Gflock',
      description:
          'A stylish black casual crop top suitable for daily wear and casual outfits.',
    ),
    ProductModel(
      itemId: 'P002',
      title: 'Blue Denim Jeans',
      role: 'bottom',
      color: ['blue'],
      style: ['casual'],
      imageUrl:
          'https://images.unsplash.com/photo-1541099649105-f69ad21f3246?w=600',
      productUrl: 'https://example.com/products/blue-jeans',
      price: 6200,
      brand: 'Kelly Felder',
      description:
          'Comfortable blue denim jeans that match well with casual tops and jackets.',
    ),
    ProductModel(
      itemId: 'P003',
      title: 'White Casual Jacket',
      role: 'outerwear',
      color: ['white'],
      style: ['casual'],
      imageUrl:
          'https://images.unsplash.com/photo-1548624313-0396c75e4b1a?w=600',
      productUrl: 'https://example.com/products/white-jacket',
      price: 7500,
      brand: 'Gflock',
      description:
          'A clean white casual jacket that can complete a simple everyday outfit.',
    ),
    ProductModel(
      itemId: 'P004',
      title: 'Brown Formal Blazer',
      role: 'outerwear',
      color: ['brown'],
      style: ['formal'],
      imageUrl:
          'https://images.unsplash.com/photo-1487222477894-8943e31ef7b2?w=600',
      productUrl: 'https://example.com/products/brown-formal-blazer',
      price: 9500,
      brand: 'Fashion Bug',
      description:
          'A formal blazer suitable for office, presentations, and smart casual events.',
    ),
  ];

  List<ProductModel> get _filteredProducts {
    final products = _hasActiveSearch ? _cachedSearchProducts : sampleProducts;

    if (_selectedStyleFilter.toLowerCase() == 'all') {
      return products;
    }

    return products.where((product) {
      return product.style.any(
        (style) => style.toLowerCase() == _selectedStyleFilter.toLowerCase(),
      );
    }).toList();
  }

  bool get _hasActiveSearch => _searchQuery.isNotEmpty;

  @override
  void dispose() {
    super.dispose();
  }

  void _openNotifications() {
    Navigator.push(
      context,
      MaterialPageRoute(builder: (_) => const NotificationsScreen()),
    ).then((_) {
      // When returning, clear the badge (user has seen notifications)
      if (mounted) {
        setState(() => _unreadNotifications = 0);
      }
    });
  }

  void _openProductDetails(BuildContext context, ProductModel product) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => ProductDetailScreen(product: product),
      ),
    );
  }

  Future<void> _onBottomNavTap(int index) async {
    if (index == BottomNavTab.home) {
      setState(() {
        _selectedBottomIndex = index;
      });

      Navigator.popUntil(context, (route) => route.isFirst);
      return;
    }

    if (index == BottomNavTab.search) {
      setState(() {
        _selectedBottomIndex = index;
      });

      await _openSearchScreen();

      if (!mounted) {
        return;
      }

      setState(() {
        _selectedBottomIndex = _hasActiveSearch
            ? BottomNavTab.search
            : BottomNavTab.home;
      });
      return;
    }

    if (index == BottomNavTab.camera) {
      _openCamera();
      return;
    }

    if (index == BottomNavTab.saved) {
      setState(() {
        _selectedBottomIndex = index;
      });

      Navigator.push(
        context,
        MaterialPageRoute(builder: (context) => const SavedOutfitsScreen()),
      ).then((_) {
        if (mounted) {
          setState(() {
            _selectedBottomIndex = BottomNavTab.home;
          });
        }
      });

      return;
    }

    if (index == BottomNavTab.profile) {
      setState(() {
        _selectedBottomIndex = index;
      });

      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (context) => const EvaluationSummaryScreen(),
        ),
      ).then((_) {
        if (mounted) {
          setState(() {
            _selectedBottomIndex = BottomNavTab.home;
          });
        }
      });

      return;
    }

    setState(() {
      _selectedBottomIndex = index;
    });

    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('This section will be added next.'),
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  Future<void> _openSearchScreen() async {
    await Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => SearchScreen(
          allProducts: sampleProducts,
          searchHistory: _searchHistory,
          onSearch: (query, results, updatedHistory) {
            _searchProducts(query, precomputedResults: results);
            setState(() {
              _searchHistory = updatedHistory;
              _persistedHistory = updatedHistory;
            });
          },
        ),
      ),
    );
  }

  void _searchProducts(
    String rawQuery, {
    List<ProductModel>? precomputedResults,
  }) {
    final query = rawQuery.trim();

    if (query.isEmpty) {
      _clearSearch(showMessage: true);
      return;
    }

    final searchResults =
        precomputedResults ??
        sampleProducts.where((product) {
          final searchableText = [
            product.itemId,
            product.title,
            product.role,
            product.brand,
            product.description,
            ...product.color,
            ...product.style,
          ].join(' ').toLowerCase();
          return searchableText.contains(query.toLowerCase());
        }).toList();

    setState(() {
      _searchQuery = query;
      _cachedSearchProducts = searchResults;
      _lastSearchQuery = query;
      _lastSearchProducts = searchResults;
      _selectedBottomIndex = BottomNavTab.search;
    });

    if (searchResults.isEmpty) {
      _showSnackBar('Search unsuccessful: no products found for "$query".');
      return;
    }

    _showSnackBar(
      'Search successful: ${searchResults.length} product${searchResults.length == 1 ? '' : 's'} found.',
    );
  }

  void _clearSearch({bool showMessage = false}) {
    setState(() {
      _searchQuery = '';
      _cachedSearchProducts = [];
      _lastSearchQuery = '';
      _lastSearchProducts = [];
      _selectedBottomIndex = BottomNavTab.home;
    });

    if (showMessage) {
      _showSnackBar('Search cleared.');
    }
  }

  void _showSnackBar(String message) {
    if (!mounted) {
      return;
    }

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), behavior: SnackBarBehavior.floating),
    );
  }

  Future<void> _openCamera() async {
    setState(() {
      _selectedBottomIndex = BottomNavTab.camera;
    });

    try {
      final XFile? photo = await _imagePicker.pickImage(
        source: ImageSource.camera,
        imageQuality: 85,
        maxWidth: 1600,
      );

      if (!mounted) {
        return;
      }

      setState(() {
        _selectedBottomIndex = BottomNavTab.home;
      });

      if (photo == null) {
        return;
      }

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Photo captured successfully.'),
          behavior: SnackBarBehavior.floating,
        ),
      );
    } catch (error) {
      if (!mounted) {
        return;
      }

      setState(() {
        _selectedBottomIndex = BottomNavTab.home;
      });

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Camera unavailable: $error'),
          behavior: SnackBarBehavior.floating,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final double screenWidth = MediaQuery.sizeOf(context).width;
    final bool isCompact = screenWidth <= 360;
    final double pagePadding = isCompact ? 12 : 18;

    return Scaffold(
      backgroundColor: const Color(0xFFF8F8F8),
      appBar: AppBar(
        elevation: 0,
        backgroundColor: const Color(0xFFF8F8F8),
        toolbarHeight: isCompact ? 48 : kToolbarHeight,
        title: const Text(
          'OutfitIQ',
          style: TextStyle(
            color: Color(0xFF111827),
            fontSize: 22,
            fontWeight: FontWeight.w900,
          ),
        ),
        actions: [
          // Notification bell with unread badge
          Stack(
            alignment: Alignment.center,
            children: [
              IconButton(
                tooltip: 'Notifications',
                onPressed: _openNotifications,
                icon: const Icon(
                  Icons.notifications_outlined,
                  color: Color(0xFF111827),
                ),
              ),
              if (_unreadNotifications > 0)
                Positioned(
                  top: 8,
                  right: 8,
                  child: Container(
                    width: 17,
                    height: 17,
                    decoration: BoxDecoration(
                      color: const Color(0xFFEF4444),
                      shape: BoxShape.circle,
                      border: Border.all(color: Colors.white, width: 1.5),
                    ),
                    child: Center(
                      child: Text(
                        _unreadNotifications > 9
                            ? '9+'
                            : '$_unreadNotifications',
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 9,
                          fontWeight: FontWeight.w800,
                          height: 1,
                        ),
                      ),
                    ),
                  ),
                ),
            ],
          ),
        ],
      ),
      body: SafeArea(
        top: false,
        child: ListView(
          padding: EdgeInsets.fromLTRB(
            pagePadding,
            isCompact ? 8 : 18,
            pagePadding,
            18,
          ),
          children: [
            _buildWelcomeSection(isCompact: isCompact),
            SizedBox(height: isCompact ? 14 : 20),
            _buildBrandSection(isCompact: isCompact),
            SizedBox(height: isCompact ? 14 : 18),

            _buildExploreStylesSection(isCompact: isCompact),
            SizedBox(height: isCompact ? 16 : 22),
            _buildSectionHeader(
              title: _hasActiveSearch ? 'Search Results' : 'Flash Sale',
              subtitle: _hasActiveSearch
                  ? '${_filteredProducts.length} cached result${_filteredProducts.length == 1 ? '' : 's'} for "$_searchQuery"'
                  : 'Choose an item and complete the look',
              isCompact: isCompact,
              trailingLabel: _hasActiveSearch ? 'Clear' : 'See All',
              onTrailingTap: _hasActiveSearch ? () => _clearSearch() : null,
            ),
            SizedBox(height: isCompact ? 10 : 16),
            if (_filteredProducts.isEmpty)
              _buildEmptySearchState(isCompact: isCompact)
            else
              GridView.builder(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                itemCount: _filteredProducts.length,
                gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: 2,
                  crossAxisSpacing: isCompact ? 8 : 14,
                  mainAxisSpacing: isCompact ? 10 : 14,
                  childAspectRatio: isCompact ? 0.52 : 0.51,
                ),
                itemBuilder: (context, index) {
                  final product = _filteredProducts[index];

                  return ProductCard(
                    product: product,
                    onTap: () {
                      _openProductDetails(context, product);
                    },
                  );
                },
              ),
          ],
        ),
      ),
      bottomNavigationBar: CustomBottomNavBar(
        selectedIndex: _selectedBottomIndex,
        onItemSelected: _onBottomNavTap,
      ),
    );
  }

  Widget _buildWelcomeSection({required bool isCompact}) {
    return Container(
      padding: EdgeInsets.all(isCompact ? 14 : 18),
      decoration: BoxDecoration(
        color: const Color(0xFF111827),
        borderRadius: BorderRadius.circular(isCompact ? 18 : 24),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Find your best outfit',
            style: TextStyle(
              color: Colors.white,
              fontSize: isCompact ? 18 : 22,
              fontWeight: FontWeight.w900,
            ),
          ),
          SizedBox(height: isCompact ? 6 : 8),
          Text(
            'Select a fashion item and generate compatible outfit suggestions.',
            style: TextStyle(
              color: const Color(0xFFD1D5DB),
              fontSize: isCompact ? 12 : 14,
              height: 1.35,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildExploreStylesSection({required bool isCompact}) {
    final styles = ['All', 'Casual', 'Formal', 'Trendy'];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Explore styles',
          style: TextStyle(
            fontSize: isCompact ? 18 : 21,
            color: const Color(0xFF111827),
            fontWeight: FontWeight.w900,
          ),
        ),
        const SizedBox(height: 12),
        SizedBox(
          height: 43,
          child: ListView.separated(
            scrollDirection: Axis.horizontal,
            itemCount: styles.length,
            separatorBuilder: (context, index) => const SizedBox(width: 10),
            itemBuilder: (context, index) {
              final style = styles[index];
              final isSelected = _selectedStyleFilter == style;

              return ChoiceChip(
                label: Text(style),
                selected: isSelected,
                onSelected: (_) {
                  setState(() {
                    _selectedStyleFilter = style;
                  });
                },
                selectedColor: const Color(0xFF0B5D85),
                backgroundColor: Colors.white,
                showCheckmark: false,
                side: BorderSide(
                  color: isSelected
                      ? const Color(0xFF0B5D85)
                      : const Color(0xFFE5E7EB),
                ),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(22),
                ),
                labelStyle: TextStyle(
                  color: isSelected ? Colors.white : const Color(0xFF111827),
                  fontSize: isCompact ? 12 : 13,
                  fontWeight: FontWeight.w800,
                ),
                padding: EdgeInsets.symmetric(
                  horizontal: isCompact ? 12 : 16,
                  vertical: 10,
                ),
              );
            },
          ),
        ),
      ],
    );
  }

  Widget _buildBrandSection({required bool isCompact}) {
    final brands = ['Gflock', 'Kelly Felder', 'Fashion Bug', 'Carnage'];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildSectionHeader(
          title: 'Popular Brand',
          subtitle: 'Brands used in sample products',
          isCompact: isCompact,
        ),
        SizedBox(height: isCompact ? 8 : 12),
        SizedBox(
          height: isCompact ? 36 : 42,
          child: ListView.separated(
            scrollDirection: Axis.horizontal,
            itemCount: brands.length,
            separatorBuilder: (context, index) =>
                SizedBox(width: isCompact ? 7 : 10),
            itemBuilder: (context, index) {
              return Container(
                padding: EdgeInsets.symmetric(horizontal: isCompact ? 12 : 16),
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(22),
                  border: Border.all(color: const Color(0xFFE5E7EB)),
                ),
                child: Text(
                  brands[index],
                  style: TextStyle(
                    fontSize: isCompact ? 11 : 13,
                    fontWeight: FontWeight.w700,
                    color: const Color(0xFF111827),
                  ),
                ),
              );
            },
          ),
        ),
      ],
    );
  }

  Widget _buildSectionHeader({
    required String title,
    required String subtitle,
    required bool isCompact,
    String trailingLabel = 'See All',
    VoidCallback? onTrailingTap,
  }) {
    return Row(
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: TextStyle(
                  fontSize: isCompact ? 17 : 21,
                  fontWeight: FontWeight.w900,
                  color: const Color(0xFF111827),
                ),
              ),
              SizedBox(height: isCompact ? 2 : 3),
              Text(
                subtitle,
                style: TextStyle(
                  fontSize: isCompact ? 11 : 13,
                  color: const Color(0xFF6B7280),
                  fontWeight: FontWeight.w500,
                ),
              ),
            ],
          ),
        ),
        InkWell(
          onTap: onTrailingTap,
          borderRadius: BorderRadius.circular(18),
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
            child: Text(
              trailingLabel,
              style: TextStyle(
                fontSize: isCompact ? 11 : 13,
                fontWeight: FontWeight.w800,
                color: const Color(0xFF111827),
              ),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildEmptySearchState({required bool isCompact}) {
    return Container(
      width: double.infinity,
      padding: EdgeInsets.all(isCompact ? 18 : 22),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: const Color(0xFFE5E7EB)),
      ),
      child: Column(
        children: [
          const Icon(Icons.search_off, size: 38, color: Color(0xFF6B7280)),
          const SizedBox(height: 10),
          Text(
            'No products found',
            style: TextStyle(
              fontSize: isCompact ? 15 : 17,
              fontWeight: FontWeight.w900,
              color: const Color(0xFF111827),
            ),
          ),
          const SizedBox(height: 6),
          Text(
            'Try another product name, brand, color, or style.',
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: isCompact ? 12 : 13,
              color: const Color(0xFF6B7280),
              height: 1.35,
            ),
          ),
          const SizedBox(height: 14),
          OutlinedButton.icon(
            onPressed: _openSearchScreen,
            icon: const Icon(Icons.search),
            label: const Text('Search Again'),
          ),
        ],
      ),
    );
  }
}
