import 'package:flutter/material.dart';
import 'trend_history_screen.dart';
import '../models/trend_model.dart';
import '../services/trend_api_service.dart';
import '../widgets/analysis_status_card.dart';
import '../widgets/bottom_nav_bar.dart';
import '../widgets/dashboard_header.dart';
import '../widgets/filter_chips_row.dart';
import '../widgets/search_filter_bar.dart';
import '../widgets/summary_card.dart';
import '../widgets/trend_card.dart';
import 'trend_detail_screen.dart';

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

  Future<void> _refreshTrends() async {
    _loadTrends(selectedFilter);
  }

  void _openTrendDetails(TrendModel trend) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => TrendDetailScreen(trend: trend),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      bottomNavigationBar: TrendBottomNavBar(
  onHistoryTap: () {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => const TrendHistoryScreen(),
      ),
    );
  },
),
      body: SafeArea(
        child: RefreshIndicator(
          color: const Color(0xFF00796B),
          onRefresh: _refreshTrends,
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
                              onTap: () => _openTrendDetails(trend),
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