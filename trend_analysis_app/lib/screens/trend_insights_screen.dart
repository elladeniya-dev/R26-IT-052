import 'package:flutter/material.dart';

import '../models/trend_insight_model.dart';
import '../services/trend_api_service.dart';
import '../widgets/trend_insight_card.dart';

class TrendInsightsScreen extends StatefulWidget {
  const TrendInsightsScreen({super.key});

  @override
  State<TrendInsightsScreen> createState() => _TrendInsightsScreenState();
}

class _TrendInsightsScreenState extends State<TrendInsightsScreen> {
  final TrendApiService _trendApiService = TrendApiService();

  late Future<List<TrendInsightModel>> _insightsFuture;

  @override
  void initState() {
    super.initState();
    _loadInsights();
  }

  void _loadInsights() {
    _insightsFuture = _trendApiService.getTrendInsights();
  }

  Future<void> _refreshInsights() async {
    setState(() {
      _loadInsights();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF6F8F7),
      appBar: AppBar(
        backgroundColor: const Color(0xFFF6F8F7),
        elevation: 0,
        centerTitle: false,
        iconTheme: const IconThemeData(
          color: Color(0xFF143D35),
        ),
        title: const Text(
          'Trending Insights',
          style: TextStyle(
            color: Color(0xFF143D35),
            fontSize: 22,
            fontWeight: FontWeight.w900,
          ),
        ),
      ),
      body: RefreshIndicator(
        color: const Color(0xFF00796B),
        onRefresh: _refreshInsights,
        child: FutureBuilder<List<TrendInsightModel>>(
          future: _insightsFuture,
          builder: (context, snapshot) {
            if (snapshot.connectionState == ConnectionState.waiting) {
              return const Center(
                child: CircularProgressIndicator(
                  color: Color(0xFF00796B),
                ),
              );
            }

            if (snapshot.hasError) {
              return ListView(
                padding: const EdgeInsets.all(20),
                children: [
                  const SizedBox(height: 100),
                  Icon(
                    Icons.error_outline,
                    size: 56,
                    color: Colors.red.shade400,
                  ),
                  const SizedBox(height: 16),
                  const Text(
                    'Failed to load trend insights',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      color: Color(0xFF143D35),
                      fontSize: 18,
                      fontWeight: FontWeight.w900,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    snapshot.error.toString(),
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      color: Colors.grey.shade600,
                      fontSize: 13,
                      height: 1.4,
                    ),
                  ),
                ],
              );
            }

            final insights = snapshot.data ?? [];

            if (insights.isEmpty) {
              return ListView(
                padding: const EdgeInsets.all(20),
                children: [
                  const SizedBox(height: 100),
                  Icon(
                    Icons.insights_outlined,
                    size: 58,
                    color: Colors.grey.shade400,
                  ),
                  const SizedBox(height: 16),
                  const Text(
                    'No insights available yet',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      color: Color(0xFF143D35),
                      fontSize: 18,
                      fontWeight: FontWeight.w900,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Run trend analysis first to generate fashion insights.',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      color: Colors.grey.shade600,
                      fontSize: 13,
                    ),
                  ),
                ],
              );
            }

            return ListView(
              padding: const EdgeInsets.fromLTRB(20, 8, 20, 24),
              children: [
                _InsightsHeader(totalInsights: insights.length),
                const SizedBox(height: 18),
                ...insights.map(
                  (insight) => TrendInsightCard(insight: insight),
                ),
              ],
            );
          },
        ),
      ),
    );
  }
}

class _InsightsHeader extends StatelessWidget {
  final int totalInsights;

  const _InsightsHeader({
    required this.totalInsights,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [
            Color(0xFF00796B),
            Color(0xFF005B4F),
          ],
        ),
        borderRadius: BorderRadius.circular(24),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF00796B).withValues(alpha: 0.20),
            blurRadius: 18,
            offset: const Offset(0, 9),
          ),
        ],
      ),
      child: Row(
        children: [
          Container(
            width: 54,
            height: 54,
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: 0.18),
              borderRadius: BorderRadius.circular(18),
            ),
            child: const Icon(
              Icons.auto_awesome,
              color: Colors.white,
              size: 28,
            ),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'AI Fashion Insights',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 18,
                    fontWeight: FontWeight.w900,
                  ),
                ),
                const SizedBox(height: 5),
                Text(
                  '$totalInsights insights generated from latest trend signals',
                  style: TextStyle(
                    color: Colors.white.withValues(alpha: 0.86),
                    fontSize: 12.5,
                    height: 1.4,
                    fontWeight: FontWeight.w600,
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