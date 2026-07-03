import 'package:flutter/material.dart';

import '../models/product_model.dart';
import '../widgets/product_card.dart';
import 'product_detail_screen.dart';
import 'saved_outfits_screen.dart';

class ProductListScreen extends StatefulWidget {
  const ProductListScreen({super.key});

  @override
  State<ProductListScreen> createState() => _ProductListScreenState();
}

class _ProductListScreenState extends State<ProductListScreen> {
  int _selectedBottomIndex = 0;

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

  void _openSavedOutfits(BuildContext context) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => const SavedOutfitsScreen(),
      ),
    );
  }

  void _openProductDetails(BuildContext context, ProductModel product) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => ProductDetailScreen(product: product),
      ),
    );
  }

  void _onBottomNavTap(int index) {
    if (index == 3) {
      setState(() {
        _selectedBottomIndex = index;
      });

      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (context) => const SavedOutfitsScreen(),
        ),
      ).then((_) {
        if (mounted) {
          setState(() {
            _selectedBottomIndex = 0;
          });
        }
      });

      return;
    }

    setState(() {
      _selectedBottomIndex = index;
    });

    if (index != 0) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('This section will be added next.'),
          behavior: SnackBarBehavior.floating,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8F8F8),
      appBar: AppBar(
        elevation: 0,
        backgroundColor: const Color(0xFFF8F8F8),
        title: const Text(
          'OutfitIQ',
          style: TextStyle(
            color: Color(0xFF111827),
            fontSize: 26,
            fontWeight: FontWeight.w900,
          ),
        ),
        actions: [
          IconButton(
            onPressed: () {},
            icon: const Icon(
              Icons.search,
              color: Color(0xFF111827),
            ),
          ),
          IconButton(
            tooltip: 'Saved Outfits',
            onPressed: () {
              _openSavedOutfits(context);
            },
            icon: const Icon(
              Icons.favorite_border,
              color: Color(0xFF111827),
            ),
          ),
        ],
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(18),
          children: [
            _buildWelcomeSection(),
            const SizedBox(height: 20),
            _buildBrandSection(),
            const SizedBox(height: 22),
            _buildSectionHeader(
              title: 'Flash Sale',
              subtitle: 'Choose an item and complete the look',
            ),
            const SizedBox(height: 16),
            GridView.builder(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              itemCount: sampleProducts.length,
              gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: 2,
                crossAxisSpacing: 14,
                mainAxisSpacing: 14,
                childAspectRatio: 0.62,
              ),
              itemBuilder: (context, index) {
                final product = sampleProducts[index];

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
      bottomNavigationBar: _buildBottomNavigationBar(),
    );
  }

  Widget _buildWelcomeSection() {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: const Color(0xFF111827),
        borderRadius: BorderRadius.circular(24),
      ),
      child: const Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Find your best outfit',
            style: TextStyle(
              color: Colors.white,
              fontSize: 22,
              fontWeight: FontWeight.w900,
            ),
          ),
          SizedBox(height: 8),
          Text(
            'Select a fashion item and generate compatible outfit suggestions.',
            style: TextStyle(
              color: Color(0xFFD1D5DB),
              fontSize: 14,
              height: 1.5,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildBrandSection() {
    final brands = ['Gflock', 'Kelly Felder', 'Fashion Bug', 'Carnage'];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildSectionHeader(
          title: 'Popular Brand',
          subtitle: 'Brands used in sample products',
        ),
        const SizedBox(height: 12),
        SizedBox(
          height: 42,
          child: ListView.separated(
            scrollDirection: Axis.horizontal,
            itemCount: brands.length,
            separatorBuilder: (context, index) => const SizedBox(width: 10),
            itemBuilder: (context, index) {
              return Container(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(22),
                  border: Border.all(color: const Color(0xFFE5E7EB)),
                ),
                child: Text(
                  brands[index],
                  style: const TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w700,
                    color: Color(0xFF111827),
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
  }) {
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
              const SizedBox(height: 3),
              Text(
                subtitle,
                style: const TextStyle(
                  fontSize: 13,
                  color: Color(0xFF6B7280),
                  fontWeight: FontWeight.w500,
                ),
              ),
            ],
          ),
        ),
        const Text(
          'See All',
          style: TextStyle(
            fontSize: 13,
            fontWeight: FontWeight.w800,
            color: Color(0xFF111827),
          ),
        ),
      ],
    );
  }

  Widget _buildBottomNavigationBar() {
    return SafeArea(
      top: false,
      child: Container(
        padding: const EdgeInsets.fromLTRB(16, 10, 16, 12),
        decoration: const BoxDecoration(
          color: Colors.white,
          border: Border(
            top: BorderSide(
              color: Color(0xFFE5E7EB),
            ),
          ),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceAround,
          children: [
            _buildBottomNavItem(
              index: 0,
              icon: Icons.home_outlined,
            ),
            _buildBottomNavItem(
              index: 1,
              icon: Icons.search,
            ),
            _buildBottomNavItem(
              index: 2,
              icon: Icons.inventory_2_outlined,
            ),
            _buildBottomNavItem(
              index: 3,
              icon: Icons.favorite_border,
            ),
            _buildBottomNavItem(
              index: 4,
              icon: Icons.person_outline,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildBottomNavItem({
    required int index,
    required IconData icon,
  }) {
    final bool isSelected = _selectedBottomIndex == index;

    return GestureDetector(
      onTap: () {
        _onBottomNavTap(index);
      },
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 180),
        width: 42,
        height: 42,
        decoration: BoxDecoration(
          color: isSelected ? const Color(0xFF0F8B8D) : Colors.transparent,
          shape: BoxShape.circle,
        ),
        child: Icon(
          icon,
          size: 22,
          color: isSelected ? Colors.white : const Color(0xFF9CA3AF),
        ),
      ),
    );
  }
}