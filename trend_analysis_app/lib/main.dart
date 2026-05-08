import 'package:flutter/material.dart';

import 'models/trend_model.dart';
import 'services/trend_api_service.dart';

void main() {
  runApp(const TrendAnalysisApp());
}

class TrendAnalysisApp extends StatelessWidget {
  const TrendAnalysisApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Trend Analysis',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        fontFamily: 'Roboto',
        scaffoldBackgroundColor: const Color(0xFFF7F8FA),
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF00796B),
        ),
        useMaterial3: true,
      ),
      home: const TrendDashboardScreen(),
    );
  }
}

class TrendDashboardScreen extends StatefulWidget {
  const TrendDashboardScreen({super.key});

  @override
  State<TrendDashboardScreen> createState() => _TrendDashboardScreenState();
}

class _TrendDashboardScreenState extends State<TrendDashboardScreen> {
  final TrendApiService _trendApiService = TrendApiService();

  late Future<List<TrendModel>> _trendsFuture;

  String selectedFilter = 'all';

  final List<String> filters = [
    'all',
    'style',
    'color',
    'material',
    'fit_type',
    'category',
    'brand',
  ];

  @override
  void initState() {
    super.initState();
    _trendsFuture = _trendApiService.getAllTrends();
  }

  void _loadTrends(String filter) {
    setState(() {
      selectedFilter = filter;

      if (filter == 'all') {
        _trendsFuture = _trendApiService.getAllTrends();
      } else {
        _trendsFuture = _trendApiService.getTrendsByAttributeType(filter);
      }
    });
  }

  IconData _getTrendIcon(String attributeType) {
    switch (attributeType) {
      case 'style':
        return Icons.checkroom;
      case 'color':
        return Icons.palette;
      case 'material':
        return Icons.texture;
      case 'fit_type':
        return Icons.trending_up;
      case 'category':
        return Icons.category;
      case 'brand':
        return Icons.storefront;
      default:
        return Icons.auto_graph;
    }
  }

  String _formatAttributeType(String value) {
    return value
        .replaceAll('_', ' ')
        .split(' ')
        .map((word) {
          if (word.isEmpty) return word;
          return word[0].toUpperCase() + word.substring(1);
        })
        .join(' ');
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      bottomNavigationBar: const TrendBottomNavBar(),
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: () async {
            _loadTrends(selectedFilter);
          },
          child: SingleChildScrollView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.fromLTRB(18, 16, 18, 90),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const DashboardHeader(),
                const SizedBox(height: 22),
                const SearchFilterBar(),
                const SizedBox(height: 18),
                FilterChipsRow(
                  filters: filters,
                  selectedFilter: selectedFilter,
                  onFilterSelected: _loadTrends,
                ),
                const SizedBox(height: 22),
                FutureBuilder<List<TrendModel>>(
                  future: _trendsFuture,
                  builder: (context, snapshot) {
                    if (snapshot.connectionState == ConnectionState.waiting) {
                      return const LoadingView();
                    }

                    if (snapshot.hasError) {
                      return ErrorView(
                        errorMessage: snapshot.error.toString(),
                        onRetry: () {
                          _loadTrends(selectedFilter);
                        },
                      );
                    }

                    final List<TrendModel> trends = snapshot.data ?? [];

                    if (trends.isEmpty) {
                      return const EmptyView();
                    }

                    return Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        SummaryCard(totalTrends: trends.length),
                        const SizedBox(height: 24),
                        const SectionTitle(title: 'Top Fashion Trends'),
                        const SizedBox(height: 14),
                        GridView.builder(
                          itemCount: trends.length,
                          shrinkWrap: true,
                          physics: const NeverScrollableScrollPhysics(),
                          gridDelegate:
                              const SliverGridDelegateWithFixedCrossAxisCount(
                            crossAxisCount: 2,
                            mainAxisSpacing: 14,
                            crossAxisSpacing: 14,
                            childAspectRatio: 0.80,
                          ),
                          itemBuilder: (context, index) {
                            final trend = trends[index];

                            return TrendCard(
                              trend: trend,
                              icon: _getTrendIcon(trend.attributeType),
                              formattedType:
                                  _formatAttributeType(trend.attributeType),
                            );
                          },
                        ),
                        const SizedBox(height: 24),
                        const SectionTitle(title: 'Analysis Status'),
                        const SizedBox(height: 14),
                        const AnalysisStatusCard(),
                      ],
                    );
                  },
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class DashboardHeader extends StatelessWidget {
  const DashboardHeader({super.key});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        const Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Trend Analysis',
                style: TextStyle(
                  fontSize: 28,
                  fontWeight: FontWeight.w800,
                  color: Color(0xFF143D35),
                ),
              ),
              SizedBox(height: 4),
              Text(
                'Discover weekly fashion movements',
                style: TextStyle(
                  fontSize: 14,
                  color: Color(0xFF7A7A7A),
                ),
              ),
            ],
          ),
        ),
        Container(
          height: 46,
          width: 46,
          decoration: BoxDecoration(
            color: const Color(0xFF00796B),
            borderRadius: BorderRadius.circular(16),
          ),
          child: const Icon(
            Icons.auto_graph,
            color: Colors.white,
          ),
        ),
      ],
    );
  }
}

class SearchFilterBar extends StatelessWidget {
  const SearchFilterBar({super.key});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: Container(
            height: 50,
            padding: const EdgeInsets.symmetric(horizontal: 14),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(16),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.04),
                  blurRadius: 10,
                  offset: const Offset(0, 4),
                ),
              ],
            ),
            child: const Row(
              children: [
                Icon(Icons.search, color: Color(0xFF8A8A8A)),
                SizedBox(width: 10),
                Text(
                  'Search trends',
                  style: TextStyle(
                    color: Color(0xFF8A8A8A),
                    fontSize: 14,
                  ),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(width: 12),
        Container(
          height: 50,
          width: 50,
          decoration: BoxDecoration(
            color: const Color(0xFF00796B),
            borderRadius: BorderRadius.circular(16),
          ),
          child: const Icon(
            Icons.tune,
            color: Colors.white,
          ),
        ),
      ],
    );
  }
}

class FilterChipsRow extends StatelessWidget {
  final List<String> filters;
  final String selectedFilter;
  final Function(String) onFilterSelected;

  const FilterChipsRow({
    super.key,
    required this.filters,
    required this.selectedFilter,
    required this.onFilterSelected,
  });

  String _formatFilter(String value) {
    if (value == 'all') return 'All';

    return value
        .replaceAll('_', ' ')
        .split(' ')
        .map((word) {
          if (word.isEmpty) return word;
          return word[0].toUpperCase() + word.substring(1);
        })
        .join(' ');
  }

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 38,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        itemCount: filters.length,
        separatorBuilder: (context, index) => const SizedBox(width: 8),
        itemBuilder: (context, index) {
          final filter = filters[index];
          final bool isSelected = selectedFilter == filter;

          return GestureDetector(
            onTap: () => onFilterSelected(filter),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 15),
              decoration: BoxDecoration(
                color: isSelected ? const Color(0xFF00796B) : Colors.white,
                borderRadius: BorderRadius.circular(18),
                border: Border.all(
                  color: isSelected
                      ? const Color(0xFF00796B)
                      : const Color(0xFFE5E5E5),
                ),
              ),
              child: Center(
                child: Text(
                  _formatFilter(filter),
                  style: TextStyle(
                    color: isSelected ? Colors.white : const Color(0xFF143D35),
                    fontWeight: FontWeight.w700,
                    fontSize: 13,
                  ),
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}

class SummaryCard extends StatelessWidget {
  final int totalTrends;

  const SummaryCard({
    super.key,
    required this.totalTrends,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [
            Color(0xFF00796B),
            Color(0xFF005B4F),
          ],
        ),
        borderRadius: BorderRadius.circular(24),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Weekly Trend Score',
            style: TextStyle(
              color: Colors.white70,
              fontSize: 14,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            '$totalTrends trends detected',
            style: const TextStyle(
              color: Colors.white,
              fontSize: 24,
              fontWeight: FontWeight.w800,
            ),
          ),
          const SizedBox(height: 10),
          const Text(
            'Live data loaded from FastAPI trend endpoints.',
            style: TextStyle(
              color: Colors.white70,
              fontSize: 13,
              height: 1.4,
            ),
          ),
        ],
      ),
    );
  }
}

class SectionTitle extends StatelessWidget {
  final String title;

  const SectionTitle({
    super.key,
    required this.title,
  });

  @override
  Widget build(BuildContext context) {
    return Text(
      title,
      style: const TextStyle(
        fontSize: 19,
        fontWeight: FontWeight.w800,
        color: Color(0xFF143D35),
      ),
    );
  }
}

class TrendCard extends StatelessWidget {
  final TrendModel trend;
  final IconData icon;
  final String formattedType;

  const TrendCard({
    super.key,
    required this.trend,
    required this.icon,
    required this.formattedType,
  });

  @override
  Widget build(BuildContext context) {
    final double score = trend.trendScore.clamp(0.0, 1.0);

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(22),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 12,
            offset: const Offset(0, 5),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            height: 42,
            width: 42,
            decoration: BoxDecoration(
              color: const Color(0xFFE6F4F1),
              borderRadius: BorderRadius.circular(14),
            ),
            child: Icon(
              icon,
              color: const Color(0xFF00796B),
              size: 22,
            ),
          ),
          const Spacer(),
          Text(
            formattedType,
            style: const TextStyle(
              color: Color(0xFF8A8A8A),
              fontSize: 13,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            trend.attributeValue,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(
              color: Color(0xFF143D35),
              fontSize: 19,
              fontWeight: FontWeight.w800,
            ),
          ),
          const SizedBox(height: 12),
          LinearProgressIndicator(
            value: score,
            minHeight: 7,
            borderRadius: BorderRadius.circular(10),
            backgroundColor: const Color(0xFFE9ECEF),
            valueColor: const AlwaysStoppedAnimation<Color>(
              Color(0xFF00796B),
            ),
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              Text(
                'Score ${(score * 100).toInt()}%',
                style: const TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w700,
                  color: Color(0xFF143D35),
                ),
              ),
              const Spacer(),
              Text(
                '+${trend.growthRate.toStringAsFixed(2)}',
                style: const TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w700,
                  color: Color(0xFFFF3045),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class AnalysisStatusCard extends StatelessWidget {
  const AnalysisStatusCard({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(22),
      ),
      child: const Row(
        children: [
          Icon(
            Icons.check_circle,
            color: Color(0xFF00796B),
            size: 34,
          ),
          SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Backend Connected',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w800,
                    color: Color(0xFF143D35),
                  ),
                ),
                SizedBox(height: 4),
                Text(
                  'Trend data is loaded from the FastAPI backend.',
                  style: TextStyle(
                    fontSize: 13,
                    color: Color(0xFF7A7A7A),
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

class LoadingView extends StatelessWidget {
  const LoadingView({super.key});

  @override
  Widget build(BuildContext context) {
    return const Padding(
      padding: EdgeInsets.only(top: 80),
      child: Center(
        child: CircularProgressIndicator(
          color: Color(0xFF00796B),
        ),
      ),
    );
  }
}

class ErrorView extends StatelessWidget {
  final String errorMessage;
  final VoidCallback onRetry;

  const ErrorView({
    super.key,
    required this.errorMessage,
    required this.onRetry,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.only(top: 40),
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(22),
      ),
      child: Column(
        children: [
          const Icon(
            Icons.error_outline,
            color: Color(0xFFFF3045),
            size: 42,
          ),
          const SizedBox(height: 12),
          const Text(
            'Could not load trends',
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.w800,
              color: Color(0xFF143D35),
            ),
          ),
          const SizedBox(height: 8),
          Text(
            errorMessage,
            textAlign: TextAlign.center,
            style: const TextStyle(
              fontSize: 12,
              color: Color(0xFF7A7A7A),
            ),
          ),
          const SizedBox(height: 14),
          ElevatedButton(
            onPressed: onRetry,
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF00796B),
              foregroundColor: Colors.white,
            ),
            child: const Text('Retry'),
          ),
        ],
      ),
    );
  }
}

class EmptyView extends StatelessWidget {
  const EmptyView({super.key});

  @override
  Widget build(BuildContext context) {
    return const Padding(
      padding: EdgeInsets.only(top: 80),
      child: Center(
        child: Text(
          'No trend data found',
          style: TextStyle(
            color: Color(0xFF7A7A7A),
            fontSize: 15,
          ),
        ),
      ),
    );
  }
}

class TrendBottomNavBar extends StatelessWidget {
  const TrendBottomNavBar({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 76,
      margin: const EdgeInsets.fromLTRB(18, 0, 18, 16),
      decoration: BoxDecoration(
        color: const Color(0xFF00796B),
        borderRadius: BorderRadius.circular(28),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF00796B).withOpacity(0.25),
            blurRadius: 18,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: const Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          BottomNavIcon(icon: Icons.home_rounded, isActive: true),
          BottomNavIcon(icon: Icons.search_rounded),
          BottomNavIcon(icon: Icons.favorite_border_rounded),
          BottomNavIcon(icon: Icons.person_outline_rounded),
        ],
      ),
    );
  }
}

class BottomNavIcon extends StatelessWidget {
  final IconData icon;
  final bool isActive;

  const BottomNavIcon({
    super.key,
    required this.icon,
    this.isActive = false,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 44,
      width: 44,
      decoration: BoxDecoration(
        color: isActive ? Colors.white : Colors.transparent,
        shape: BoxShape.circle,
      ),
      child: Icon(
        icon,
        color: isActive ? const Color(0xFF00796B) : Colors.white,
      ),
    );
  }
}