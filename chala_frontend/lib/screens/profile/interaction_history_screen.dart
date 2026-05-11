import 'package:flutter/material.dart';

import '../../core/theme.dart';
import '../../services/interaction_history_service.dart';

class InteractionHistoryScreen extends StatefulWidget {
  const InteractionHistoryScreen({super.key});

  @override
  State<InteractionHistoryScreen> createState() =>
      _InteractionHistoryScreenState();
}

class _InteractionHistoryScreenState extends State<InteractionHistoryScreen> {
  final InteractionHistoryService _interactionHistoryService =
      InteractionHistoryService();

  bool _isLoading = true;
  String? _errorMessage;
  Map<String, dynamic>? _historyData;

  @override
  void initState() {
    super.initState();
    _loadInteractionHistory();
  }

  Future<void> _loadInteractionHistory() async {
    try {
      final data = await _interactionHistoryService.getInteractionHistory();

      if (!mounted) {
        return;
      }

      setState(() {
        _historyData = data;
        _isLoading = false;
      });
    } catch (e) {
      if (!mounted) {
        return;
      }

      setState(() {
        _errorMessage = e.toString();
        _isLoading = false;
      });
    }
  }

  Future<void> _refreshInteractionHistory() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    await _loadInteractionHistory();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundColor,
      body: SafeArea(
        child: Column(
          children: [
            _buildHeader(context),
            Expanded(
              child: RefreshIndicator(
                color: AppTheme.primaryColor,
                onRefresh: _refreshInteractionHistory,
                child: SingleChildScrollView(
                  physics: const AlwaysScrollableScrollPhysics(),
                  padding: const EdgeInsets.fromLTRB(20, 16, 20, 24),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      _buildInfoCard(),
                      const SizedBox(height: 18),
                      _buildContent(),
                    ],
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(8, 12, 20, 8),
      child: Row(
        children: [
          IconButton(
            onPressed: () {
              Navigator.pop(context);
            },
            icon: const Icon(
              Icons.arrow_back_ios_new_rounded,
              size: 20,
              color: AppTheme.darkTextColor,
            ),
          ),
          const SizedBox(width: 4),
          const Expanded(
            child: Text(
              'Interaction History',
              style: TextStyle(
                fontSize: 21,
                fontWeight: FontWeight.bold,
                color: AppTheme.darkTextColor,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInfoCard() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: AppTheme.primaryColor,
        borderRadius: BorderRadius.circular(18),
      ),
      child: const Row(
        children: [
          Icon(
            Icons.history_rounded,
            color: Colors.white,
            size: 32,
          ),
          SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Your Fashion Activity',
                  style: TextStyle(
                    fontSize: 17,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                ),
                SizedBox(height: 5),
                Text(
                  'This shows your clicks, saves, selections and dislikes used by the learning engine.',
                  style: TextStyle(
                    fontSize: 13,
                    height: 1.4,
                    color: Colors.white,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildContent() {
    if (_isLoading) {
      return _buildContainer(
        child: const Center(
          child: CircularProgressIndicator(
            color: AppTheme.primaryColor,
          ),
        ),
      );
    }

    if (_errorMessage != null) {
      return _buildContainer(
        child: Text(
          _errorMessage!,
          style: const TextStyle(
            fontSize: 13,
            color: Color(0xFFEF4444),
          ),
        ),
      );
    }

    final Map<String, dynamic> stats =
        Map<String, dynamic>.from(_historyData?['stats'] ?? {});

    final List<dynamic> interactions = List<dynamic>.from(
      _historyData?['interactions'] ?? [],
    );

    if (interactions.isEmpty) {
      return Column(
        children: [
          _buildStatsCard(stats),
          const SizedBox(height: 14),
          _buildContainer(
            child: const Text(
              'No interactions found yet. Go to Home and interact with product cards.',
              style: TextStyle(
                fontSize: 13,
                color: AppTheme.lightTextColor,
              ),
            ),
          ),
        ],
      );
    }

    return Column(
      children: [
        _buildStatsCard(stats),
        const SizedBox(height: 14),
        ...interactions.map((item) {
          final interaction = Map<String, dynamic>.from(item);
          return _InteractionHistoryCard(interaction: interaction);
        }),
      ],
    );
  }

  Widget _buildStatsCard(Map<String, dynamic> stats) {
    final String total = '${stats['total_interactions'] ?? 0}';
    final String clicks = '${stats['click_count'] ?? 0}';
    final String saves = '${stats['save_count'] ?? 0}';
    final String selects = '${stats['select_count'] ?? 0}';
    final String dislikes = '${stats['dislike_count'] ?? 0}';

    return _buildContainer(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Activity Summary',
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.bold,
              color: AppTheme.darkTextColor,
            ),
          ),
          const SizedBox(height: 14),
          Row(
            children: [
              Expanded(
                child: _StatBox(
                  value: total,
                  label: 'Total',
                  icon: Icons.timeline_rounded,
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: _StatBox(
                  value: clicks,
                  label: 'Clicks',
                  icon: Icons.touch_app_rounded,
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              Expanded(
                child: _StatBox(
                  value: saves,
                  label: 'Saved',
                  icon: Icons.bookmark_border_rounded,
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: _StatBox(
                  value: selects,
                  label: 'Selected',
                  icon: Icons.check_circle_outline_rounded,
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: _StatBox(
                  value: dislikes,
                  label: 'Disliked',
                  icon: Icons.thumb_down_alt_outlined,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildContainer({
    required Widget child,
  }) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
      ),
      child: child,
    );
  }
}

class _InteractionHistoryCard extends StatelessWidget {
  final Map<String, dynamic> interaction;

  const _InteractionHistoryCard({
    required this.interaction,
  });


String _getDisplayProductName(String itemId, String backendProductName) {
  final Map<String, String> frontendProductNames = {
    'P001': 'White Cotton T-Shirt',
    'P002': 'Grey Hoodie',
    'P003': 'Blue Denim Jeans',
    'P004': 'Black Blazer',
    'P005': 'Pink Party Skirt',
  };

  return frontendProductNames[itemId] ?? backendProductName;
}



  @override
  Widget build(BuildContext context) {
    final String type = '${interaction['interaction_type'] ?? 'interaction'}';
    final String itemId = '${interaction['item_id'] ?? ''}';
    final String backendProductName =
    '${interaction['product_name'] ?? 'Unknown product'}';

final String productName = _getDisplayProductName(
  itemId,
  backendProductName,
);
    final String category = '${interaction['category'] ?? 'No category'}';
    final String brand = '${interaction['brand'] ?? 'No brand'}';
    final String value = '${interaction['interaction_value'] ?? ''}';

    final IconData icon = _getInteractionIcon(type);
    final Color color = _getInteractionColor(type);

    return Container(
      width: double.infinity,
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
      ),
      child: Row(
        children: [
          Container(
            width: 46,
            height: 46,
            decoration: BoxDecoration(
              color: color.withOpacity(0.10),
              shape: BoxShape.circle,
            ),
            child: Icon(
              icon,
              color: color,
              size: 22,
            ),
          ),
          const SizedBox(width: 13),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  _formatInteractionTitle(type, productName),
                  style: const TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.bold,
                    color: AppTheme.darkTextColor,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  '$category • $brand • $itemId',
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    fontSize: 12,
                    color: AppTheme.lightTextColor,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: 8),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
            decoration: BoxDecoration(
              color: color.withOpacity(0.10),
              borderRadius: BorderRadius.circular(16),
            ),
            child: Text(
              value,
              style: TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.bold,
                color: color,
              ),
            ),
          ),
        ],
      ),
    );
  }

  String _formatInteractionTitle(String type, String productName) {
    final String cleanType = type.toLowerCase();

    if (cleanType == 'click') {
      return 'Clicked $productName';
    }

    if (cleanType == 'save') {
      return 'Saved $productName';
    }

    if (cleanType == 'select') {
      return 'Selected $productName';
    }

    if (cleanType == 'dislike') {
      return 'Disliked $productName';
    }

    if (cleanType == 'view') {
      return 'Viewed $productName';
    }

    return '$type $productName';
  }

  IconData _getInteractionIcon(String type) {
    final String cleanType = type.toLowerCase();

    if (cleanType == 'click') {
      return Icons.touch_app_rounded;
    }

    if (cleanType == 'save') {
      return Icons.bookmark_border_rounded;
    }

    if (cleanType == 'select') {
      return Icons.check_circle_outline_rounded;
    }

    if (cleanType == 'dislike') {
      return Icons.thumb_down_alt_outlined;
    }

    if (cleanType == 'view') {
      return Icons.visibility_outlined;
    }

    return Icons.history_rounded;
  }

  Color _getInteractionColor(String type) {
    final String cleanType = type.toLowerCase();

    if (cleanType == 'dislike') {
      return const Color(0xFFEF4444);
    }

    return AppTheme.primaryColor;
  }
}

class _StatBox extends StatelessWidget {
  final String value;
  final String label;
  final IconData icon;

  const _StatBox({
    required this.value,
    required this.label,
    required this.icon,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 8),
      decoration: BoxDecoration(
        color: AppTheme.primaryColor.withOpacity(0.08),
        borderRadius: BorderRadius.circular(15),
      ),
      child: Column(
        children: [
          Icon(
            icon,
            color: AppTheme.primaryColor,
            size: 19,
          ),
          const SizedBox(height: 6),
          Text(
            value,
            style: const TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.bold,
              color: AppTheme.darkTextColor,
            ),
          ),
          const SizedBox(height: 2),
          Text(
            label,
            textAlign: TextAlign.center,
            style: const TextStyle(
              fontSize: 10,
              color: AppTheme.lightTextColor,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }
}