import 'package:flutter/material.dart';

import '../../core/theme.dart';
import '../../services/interaction_service.dart';
import '../../services/learning_service.dart';
import '../profile/profile_screen.dart';

class HomeScreen extends StatelessWidget {
  HomeScreen({super.key});

  final InteractionService _interactionService = InteractionService();
  final LearningService _learningService = LearningService();

  final List<Map<String, dynamic>> _recommendedItems = const [
  {
    'itemId': 'P001',
    'title': 'White Cotton T-Shirt',
    'price': 'LKR 3,500',
    'tag': 'Casual',
    'rating': '4.8',
  },
  {
    'itemId': 'P002',
    'title': 'Grey Hoodie',
    'price': 'LKR 6,900',
    'tag': 'Comfort',
    'rating': '4.7',
  },
  {
    'itemId': 'P003',
    'title': 'Blue Denim Jeans',
    'price': 'LKR 7,500',
    'tag': 'Trendy',
    'rating': '4.6',
  },
  {
    'itemId': 'P004',
    'title': 'Black Blazer',
    'price': 'LKR 12,000',
    'tag': 'Formal',
    'rating': '4.9',
  },
];

  final List<Map<String, dynamic>> _styleCategories = const [
    {
      'title': 'Casual',
      'icon': Icons.checkroom,
    },
    {
      'title': 'Formal',
      'icon': Icons.work_outline,
    },
    {
      'title': 'Trendy',
      'icon': Icons.local_fire_department_outlined,
    },
    {
      'title': 'Elegant',
      'icon': Icons.diamond_outlined,
    },
    {
      'title': 'Sporty',
      'icon': Icons.directions_run,
    },
  ];

  Future<void> _handleInteraction({
  required BuildContext context,
  required String itemId,
  required String interactionType,
}) async {
  try {
    await _interactionService.sendInteraction(
      itemId: itemId,
      interactionType: interactionType,
    );

    final learningResponse =
        await _learningService.updateLearningPreferences();

    final String learningMessage =
        learningResponse['message'] ?? 'Learning updated successfully';

    if (!context.mounted) return;

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          '$interactionType interaction saved. $learningMessage',
        ),
        duration: const Duration(seconds: 3),
      ),
    );
  } catch (e) {
    if (!context.mounted) return;

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(e.toString()),
        duration: const Duration(seconds: 3),
      ),
    );
  }
}

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundColor,
      body: SafeArea(
        child: Column(
          children: [
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(22, 18, 22, 20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _buildTopBar(context),
                    const SizedBox(height: 18),
                    _buildProfileStatusCard(),
                    const SizedBox(height: 18),
                    _buildHeroBanner(),
                    const SizedBox(height: 26),
                    _buildSectionTitle('Explore Styles'),
                    const SizedBox(height: 14),
                    _buildStyleCategoryList(),
                    const SizedBox(height: 26),
                    _buildSectionTitle('Recommended For You'),
                    const SizedBox(height: 14),
                    _buildRecommendedGrid(),
                  ],
                ),
              ),
            ),
            _buildBottomNavigation(context),
          ],
        ),
      ),
    );
  }

  Widget _buildTopBar(BuildContext context) {
    return Row(
      children: [
        Container(
          width: 32,
          height: 32,
          decoration: const BoxDecoration(
            color: AppTheme.primaryColor,
            shape: BoxShape.rectangle,
          ),
          child: const Icon(
            Icons.diamond_outlined,
            color: Colors.white,
            size: 20,
          ),
        ),
        const SizedBox(width: 10),
        const Text(
          'OutfitIQ',
          style: TextStyle(
            fontSize: 21,
            fontWeight: FontWeight.bold,
            color: AppTheme.darkTextColor,
          ),
        ),
        const Spacer(),
        IconButton(
          onPressed: () {
            // Search screen will be added later.
          },
          icon: const Icon(
            Icons.search_rounded,
            color: AppTheme.darkTextColor,
            size: 26,
          ),
        ),
        IconButton(
          onPressed: () {
            Navigator.push(
              context,
              MaterialPageRoute(
                builder: (context) => const ProfileScreen(),
              ),
            );
          },
          icon: const Icon(
            Icons.person_outline_rounded,
            color: AppTheme.darkTextColor,
            size: 26,
          ),
        ),
      ],
    );
  }

  Widget _buildProfileStatusCard() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 15),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
      ),
      child: Row(
        children: [
          Container(
            width: 42,
            height: 42,
            decoration: BoxDecoration(
              color: AppTheme.primaryColor.withOpacity(0.10),
              borderRadius: BorderRadius.circular(14),
            ),
            child: const Icon(
              Icons.auto_awesome_rounded,
              color: AppTheme.primaryColor,
              size: 22,
            ),
          ),
          const SizedBox(width: 14),
          const Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Personalized for you',
                  style: TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.bold,
                    color: AppTheme.darkTextColor,
                  ),
                ),
                SizedBox(height: 4),
                Text(
                  'Based on your saved style preferences',
                  style: TextStyle(
                    fontSize: 13,
                    color: AppTheme.lightTextColor,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildHeroBanner() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(22),
      decoration: BoxDecoration(
        color: AppTheme.primaryColor,
        borderRadius: BorderRadius.circular(22),
      ),
      child: Row(
        children: [
          const Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  "Don't miss out —",
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 20,
                    height: 1.2,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                SizedBox(height: 10),
                Text(
                  'Discover fashion items matched to your personal style.',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 14,
                    height: 1.45,
                  ),
                ),
                SizedBox(height: 18),
                _BannerButton(),
              ],
            ),
          ),
          const SizedBox(width: 14),
          Container(
            width: 105,
            height: 115,
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.18),
              borderRadius: BorderRadius.circular(18),
            ),
            child: const Icon(
              Icons.checkroom,
              color: Colors.white,
              size: 58,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSectionTitle(String title) {
    return Text(
      title,
      style: const TextStyle(
        fontSize: 18,
        fontWeight: FontWeight.bold,
        color: AppTheme.darkTextColor,
      ),
    );
  }

  Widget _buildStyleCategoryList() {
    return SizedBox(
      height: 86,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        itemCount: _styleCategories.length,
        separatorBuilder: (context, index) => const SizedBox(width: 15),
        itemBuilder: (context, index) {
          final category = _styleCategories[index];

          return Column(
            children: [
              Container(
                width: 56,
                height: 56,
                decoration: const BoxDecoration(
                  color: Colors.white,
                  shape: BoxShape.circle,
                ),
                child: Icon(
                  category['icon'],
                  color: AppTheme.primaryColor,
                  size: 25,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                category['title'],
                style: const TextStyle(
                  fontSize: 12,
                  color: AppTheme.darkTextColor,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ],
          );
        },
      ),
    );
  }

  Widget _buildRecommendedGrid() {
    return GridView.builder(
      itemCount: _recommendedItems.length,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 2,
        crossAxisSpacing: 14,
        mainAxisSpacing: 14,
        mainAxisExtent: 330,
      ),
      itemBuilder: (context, index) {
        final item = _recommendedItems[index];

        return _ProductCard(
          itemId: item['itemId'],
          title: item['title'],
          price: item['price'],
          tag: item['tag'],
          rating: item['rating'],
          onInteraction: (interactionType) {
            _handleInteraction(
              context: context,
              itemId: item['itemId'],
              interactionType: interactionType,
            );
          },
        );
      },
    );
  }

  Widget _buildBottomNavigation(BuildContext context) {
    return Container(
      height: 78,
      padding: const EdgeInsets.symmetric(horizontal: 22),
      decoration: const BoxDecoration(
        color: Colors.white,
        border: Border(
          top: BorderSide(
            color: Color(0xFFE5E7EB),
            width: 1,
          ),
        ),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          _buildNavItem(
            icon: Icons.home_rounded,
            label: 'Home',
            isActive: true,
          ),
          _buildNavItem(
            icon: Icons.search_rounded,
            label: 'Explore',
            isActive: false,
          ),
          _buildNavItem(
            icon: Icons.trending_up_rounded,
            label: 'Trends',
            isActive: false,
          ),
          GestureDetector(
            onTap: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (context) => const ProfileScreen(),
                ),
              );
            },
            child: _buildNavItem(
              icon: Icons.person_outline_rounded,
              label: 'Profile',
              isActive: false,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildNavItem({
    required IconData icon,
    required String label,
    required bool isActive,
  }) {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Icon(
          icon,
          size: 25,
          color: isActive ? AppTheme.primaryColor : const Color(0xFF9CA3AF),
        ),
        const SizedBox(height: 4),
        Text(
          label,
          style: TextStyle(
            fontSize: 11,
            fontWeight: isActive ? FontWeight.bold : FontWeight.w500,
            color: isActive ? AppTheme.primaryColor : const Color(0xFF9CA3AF),
          ),
        ),
      ],
    );
  }
}

class _BannerButton extends StatelessWidget {
  const _BannerButton();

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 112,
      height: 38,
      alignment: Alignment.center,
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(24),
      ),
      child: const Text(
        'Explore',
        style: TextStyle(
          color: AppTheme.primaryColor,
          fontSize: 13,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }
}

class _ProductCard extends StatelessWidget {
  final String itemId;
  final String title;
  final String price;
  final String tag;
  final String rating;
  final void Function(String interactionType) onInteraction;

  const _ProductCard({
    required this.itemId,
    required this.title,
    required this.price,
    required this.tag,
    required this.rating,
    required this.onInteraction,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(
          color: const Color(0xFFE5E7EB),
          width: 1,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          GestureDetector(
            onTap: () {
              onInteraction('click');
            },
            child: Container(
              height: 105,
              width: double.infinity,
              decoration: BoxDecoration(
                color: AppTheme.primaryColor.withOpacity(0.10),
                borderRadius: const BorderRadius.vertical(
                  top: Radius.circular(18),
                ),
              ),
              child: const Icon(
                Icons.checkroom,
                color: AppTheme.primaryColor,
                size: 52,
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.fromLTRB(12, 10, 12, 10),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 9,
                        vertical: 4,
                      ),
                      decoration: BoxDecoration(
                        color: AppTheme.primaryColor.withOpacity(0.10),
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: Text(
                        tag,
                        style: const TextStyle(
                          color: AppTheme.primaryColor,
                          fontSize: 11,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                    const Spacer(),
                    Text(
                      '#$itemId',
                      style: const TextStyle(
                        fontSize: 10,
                        color: AppTheme.lightTextColor,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Text(
                  title,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    fontSize: 14,
                    height: 1.25,
                    fontWeight: FontWeight.bold,
                    color: AppTheme.darkTextColor,
                  ),
                ),
                const SizedBox(height: 7),
                Row(
                  children: [
                    Expanded(
                      child: Text(
                        price,
                        style: const TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.bold,
                          color: AppTheme.darkTextColor,
                        ),
                      ),
                    ),
                    const Icon(
                      Icons.star_rounded,
                      color: Color(0xFFFBBF24),
                      size: 17,
                    ),
                    const SizedBox(width: 3),
                    Text(
                      rating,
                      style: const TextStyle(
                        fontSize: 12,
                        color: AppTheme.darkTextColor,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 10),
                SizedBox(
                  width: double.infinity,
                  height: 32,
                  child: OutlinedButton(
                    onPressed: () {
                      onInteraction('click');
                    },
                    style: OutlinedButton.styleFrom(
                      foregroundColor: AppTheme.primaryColor,
                      side: const BorderSide(
                        color: AppTheme.primaryColor,
                      ),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(22),
                      ),
                    ),
                    child: const Text(
                      'View Item',
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: 8),
                Row(
                  children: [
                    Expanded(
                      child: _SmallActionButton(
                        icon: Icons.bookmark_border_rounded,
                        label: 'Save',
                        onTap: () {
                          onInteraction('save');
                        },
                      ),
                    ),
                    const SizedBox(width: 7),
                    Expanded(
                      child: _SmallActionButton(
                        icon: Icons.check_circle_outline_rounded,
                        label: 'Select',
                        onTap: () {
                          onInteraction('select');
                        },
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 7),
                SizedBox(
                  width: double.infinity,
                  height: 30,
                  child: TextButton.icon(
                    onPressed: () {
                      onInteraction('dislike');
                    },
                    icon: const Icon(
                      Icons.thumb_down_alt_outlined,
                      size: 15,
                    ),
                    label: const Text(
                      'Dislike',
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    style: TextButton.styleFrom(
                      foregroundColor: Colors.redAccent,
                      padding: EdgeInsets.zero,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _SmallActionButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback onTap;

  const _SmallActionButton({
    required this.icon,
    required this.label,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 30,
      child: ElevatedButton.icon(
        onPressed: onTap,
        icon: Icon(
          icon,
          size: 14,
        ),
        label: Text(
          label,
          style: const TextStyle(
            fontSize: 10,
            fontWeight: FontWeight.bold,
          ),
        ),
        style: ElevatedButton.styleFrom(
          backgroundColor: AppTheme.primaryColor,
          foregroundColor: Colors.white,
          padding: const EdgeInsets.symmetric(horizontal: 4),
          elevation: 0,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(18),
          ),
        ),
      ),
    );
  }
}

