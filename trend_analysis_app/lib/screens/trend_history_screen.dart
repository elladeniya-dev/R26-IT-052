import 'package:flutter/material.dart';

import '../models/trend_model.dart';
import '../services/trend_api_service.dart';
import 'trend_detail_screen.dart';

class TrendHistoryScreen extends StatefulWidget {
  const TrendHistoryScreen({super.key});

  @override
  State<TrendHistoryScreen> createState() => _TrendHistoryScreenState();
}

class _TrendHistoryScreenState extends State<TrendHistoryScreen> {
  final TrendApiService _trendApiService = TrendApiService();

  late Future<List<TrendModel>> _historyFuture;

  @override
  void initState() {
    super.initState();
    _historyFuture = _trendApiService.getTrendHistory();
  }

  Future<void> _refreshHistory() async {
    setState(() {
      _historyFuture = _trendApiService.getTrendHistory();
    });
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

  String _formatDate(String dateTime) {
    if (dateTime.isEmpty) return 'N/A';

    try {
      final DateTime parsedDate = DateTime.parse(dateTime);
      return '${parsedDate.year}-${parsedDate.month.toString().padLeft(2, '0')}-${parsedDate.day.toString().padLeft(2, '0')}';
    } catch (_) {
      return dateTime;
    }
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
      backgroundColor: const Color(0xFFF7F8FA),
      body: SafeArea(
        child: RefreshIndicator(
          color: const Color(0xFF00796B),
          onRefresh: _refreshHistory,
          child: SingleChildScrollView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.fromLTRB(18, 16, 18, 28),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _HistoryHeader(
                  onBack: () => Navigator.pop(context),
                ),
                const SizedBox(height: 22),
                Container(
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
                  child: const Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Trend History',
                        style: TextStyle(
                          color: Colors.white70,
                          fontSize: 14,
                        ),
                      ),
                      SizedBox(height: 8),
                      Text(
                        'Historical trend signals',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 24,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                      SizedBox(height: 10),
                      Text(
                        'These records are useful for future ML-based trend prediction.',
                        style: TextStyle(
                          color: Colors.white70,
                          fontSize: 13,
                          height: 1.4,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 22),
                FutureBuilder<List<TrendModel>>(
                  future: _historyFuture,
                  builder: (context, snapshot) {
                    if (snapshot.connectionState == ConnectionState.waiting) {
                      return const Padding(
                        padding: EdgeInsets.only(top: 80),
                        child: Center(
                          child: CircularProgressIndicator(
                            color: Color(0xFF00796B),
                          ),
                        ),
                      );
                    }

                    if (snapshot.hasError) {
                      return _ErrorHistoryView(
                        errorMessage: snapshot.error.toString(),
                        onRetry: _refreshHistory,
                      );
                    }

                    final List<TrendModel> history = snapshot.data ?? [];

                    if (history.isEmpty) {
                      return const Padding(
                        padding: EdgeInsets.only(top: 80),
                        child: Center(
                          child: Text(
                            'No history records found',
                            style: TextStyle(
                              color: Color(0xFF7A7A7A),
                              fontSize: 15,
                            ),
                          ),
                        ),
                      );
                    }

                    return Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          '${history.length} history records',
                          style: const TextStyle(
                            fontSize: 19,
                            fontWeight: FontWeight.w800,
                            color: Color(0xFF143D35),
                          ),
                        ),
                        const SizedBox(height: 14),
                        ListView.separated(
                          itemCount: history.length,
                          shrinkWrap: true,
                          physics: const NeverScrollableScrollPhysics(),
                          separatorBuilder: (context, index) =>
                              const SizedBox(height: 12),
                          itemBuilder: (context, index) {
                            final trend = history[index];

                            return _HistoryTrendTile(
                              trend: trend,
                              icon: _getTrendIcon(trend.attributeType),
                              formattedType:
                                  _formatAttributeType(trend.attributeType),
                              startDate: _formatDate(trend.startDate),
                              endDate: _formatDate(trend.endDate),
                              onTap: () => _openTrendDetails(trend),
                            );
                          },
                        ),
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

class _HistoryHeader extends StatelessWidget {
  final VoidCallback onBack;

  const _HistoryHeader({
    required this.onBack,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        GestureDetector(
          onTap: onBack,
          child: Container(
            height: 44,
            width: 44,
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(15),
            ),
            child: const Icon(
              Icons.arrow_back_ios_new,
              size: 18,
              color: Color(0xFF143D35),
            ),
          ),
        ),
        const SizedBox(width: 14),
        const Text(
          'History',
          style: TextStyle(
            fontSize: 24,
            fontWeight: FontWeight.w800,
            color: Color(0xFF143D35),
          ),
        ),
      ],
    );
  }
}

class _HistoryTrendTile extends StatelessWidget {
  final TrendModel trend;
  final IconData icon;
  final String formattedType;
  final String startDate;
  final String endDate;
  final VoidCallback onTap;

  const _HistoryTrendTile({
    required this.trend,
    required this.icon,
    required this.formattedType,
    required this.startDate,
    required this.endDate,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final double score = trend.trendScore.clamp(0.0, 1.0);

    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(22),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.04),
              blurRadius: 12,
              offset: const Offset(0, 5),
            ),
          ],
        ),
        child: Row(
          children: [
            Container(
              height: 48,
              width: 48,
              decoration: BoxDecoration(
                color: const Color(0xFFE6F4F1),
                borderRadius: BorderRadius.circular(16),
              ),
              child: Icon(
                icon,
                color: const Color(0xFF00796B),
              ),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    '$formattedType • ${trend.timeWindow}',
                    style: const TextStyle(
                      color: Color(0xFF7A7A7A),
                      fontSize: 12,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    trend.attributeValue,
                    style: const TextStyle(
                      color: Color(0xFF143D35),
                      fontSize: 17,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                  const SizedBox(height: 5),
                  Text(
                    '$startDate to $endDate',
                    style: const TextStyle(
                      color: Color(0xFF7A7A7A),
                      fontSize: 12,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 12),
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(
                  '${(score * 100).toInt()}%',
                  style: const TextStyle(
                    color: Color(0xFF00796B),
                    fontSize: 18,
                    fontWeight: FontWeight.w900,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  '+${trend.growthRate.toStringAsFixed(2)}',
                  style: const TextStyle(
                    color: Color(0xFFFF3045),
                    fontSize: 12,
                    fontWeight: FontWeight.w800,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _ErrorHistoryView extends StatelessWidget {
  final String errorMessage;
  final VoidCallback onRetry;

  const _ErrorHistoryView({
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
            'Could not load history',
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