import 'package:flutter/material.dart';

import '../models/trend_model.dart';

class TrendDetailScreen extends StatelessWidget {
  final TrendModel trend;

  const TrendDetailScreen({
    super.key,
    required this.trend,
  });

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
    if (dateTime.isEmpty) return 'Not available';

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

  @override
  Widget build(BuildContext context) {
    final double score = trend.trendScore.clamp(0.0, 1.0);
    final String formattedType = _formatAttributeType(trend.attributeType);

    return Scaffold(
      backgroundColor: const Color(0xFFF7F8FA),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(18, 16, 18, 28),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _DetailHeader(
                onBack: () => Navigator.pop(context),
              ),
              const SizedBox(height: 24),
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(22),
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [
                      Color(0xFF00796B),
                      Color(0xFF005B4F),
                    ],
                  ),
                  borderRadius: BorderRadius.circular(28),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Icon(
                      _getTrendIcon(trend.attributeType),
                      color: Colors.white,
                      size: 42,
                    ),
                    const SizedBox(height: 18),
                    Text(
                      formattedType,
                      style: const TextStyle(
                        color: Colors.white70,
                        fontSize: 15,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      trend.attributeValue,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 32,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                    const SizedBox(height: 18),
                    LinearProgressIndicator(
                      value: score,
                      minHeight: 8,
                      borderRadius: BorderRadius.circular(12),
                      backgroundColor: Colors.white24,
                      valueColor: const AlwaysStoppedAnimation<Color>(
                        Colors.white,
                      ),
                    ),
                    const SizedBox(height: 10),
                    Text(
                      'Trend score ${(score * 100).toInt()}%',
                      style: const TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 22),
              Row(
                children: [
                  Expanded(
                    child: _MiniMetricCard(
                      title: 'Growth Rate',
                      value: '+${trend.growthRate.toStringAsFixed(2)}',
                      icon: Icons.trending_up,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: _MiniMetricCard(
                      title: 'Window',
                      value: trend.timeWindow,
                      icon: Icons.calendar_month,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 22),
              const Text(
                'Analysis Details',
                style: TextStyle(
                  fontSize: 19,
                  fontWeight: FontWeight.w800,
                  color: Color(0xFF143D35),
                ),
              ),
              const SizedBox(height: 14),
              _DetailInfoCard(
                rows: [
                  _DetailRowData(
                    label: 'Trend ID',
                    value: trend.trendId.toString(),
                  ),
                  _DetailRowData(
                    label: 'Attribute Type',
                    value: formattedType,
                  ),
                  _DetailRowData(
                    label: 'Attribute Value',
                    value: trend.attributeValue,
                  ),
                  _DetailRowData(
                    label: 'Start Date',
                    value: _formatDate(trend.startDate),
                  ),
                  _DetailRowData(
                    label: 'End Date',
                    value: _formatDate(trend.endDate),
                  ),
                  _DetailRowData(
                    label: 'Generated At',
                    value: _formatDate(trend.generatedAt),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _DetailHeader extends StatelessWidget {
  final VoidCallback onBack;

  const _DetailHeader({
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
          'Trend Details',
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

class _MiniMetricCard extends StatelessWidget {
  final String title;
  final String value;
  final IconData icon;

  const _MiniMetricCard({
    required this.title,
    required this.value,
    required this.icon,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 118,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(22),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(
            icon,
            color: const Color(0xFF00796B),
          ),
          const Spacer(),
          Text(
            title,
            style: const TextStyle(
              color: Color(0xFF7A7A7A),
              fontSize: 13,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            value,
            style: const TextStyle(
              color: Color(0xFF143D35),
              fontSize: 20,
              fontWeight: FontWeight.w800,
            ),
          ),
        ],
      ),
    );
  }
}

class _DetailInfoCard extends StatelessWidget {
  final List<_DetailRowData> rows;

  const _DetailInfoCard({
    required this.rows,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 8),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(22),
      ),
      child: Column(
        children: rows.map((row) {
          return _DetailRow(
            label: row.label,
            value: row.value,
          );
        }).toList(),
      ),
    );
  }
}

class _DetailRow extends StatelessWidget {
  final String label;
  final String value;

  const _DetailRow({
    required this.label,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 12),
      child: Row(
        children: [
          Expanded(
            child: Text(
              label,
              style: const TextStyle(
                color: Color(0xFF7A7A7A),
                fontSize: 14,
              ),
            ),
          ),
          const SizedBox(width: 12),
          Flexible(
            child: Text(
              value,
              textAlign: TextAlign.right,
              style: const TextStyle(
                color: Color(0xFF143D35),
                fontSize: 14,
                fontWeight: FontWeight.w800,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _DetailRowData {
  final String label;
  final String value;

  _DetailRowData({
    required this.label,
    required this.value,
  });
}