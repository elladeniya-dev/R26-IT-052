import 'package:flutter/material.dart';

import '../models/trend_insight_model.dart';

class TrendInsightCard extends StatelessWidget {
  final TrendInsightModel insight;

  const TrendInsightCard({
    super.key,
    required this.insight,
  });

  Color _getStatusColor() {
    if (insight.trendStatus.toLowerCase() == 'rising') {
      return const Color(0xFF22C55E);
    }

    if (insight.trendStatus.toLowerCase() == 'stable') {
      return const Color(0xFF0B5D85);
    }

    return const Color(0xFFEF4444);
  }

  String _getConfidenceText() {
    final percentage = (insight.confidence * 100).toStringAsFixed(1);
    return '$percentage% confidence';
  }

  @override
  Widget build(BuildContext context) {
    final statusColor = _getStatusColor();

    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(22),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.06),
            blurRadius: 16,
            offset: const Offset(0, 8),
          ),
        ],
        border: Border.all(
          color: statusColor.withValues(alpha: 0.14),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 12,
                  vertical: 7,
                ),
                decoration: BoxDecoration(
                  color: statusColor.withValues(alpha: 0.10),
                  borderRadius: BorderRadius.circular(50),
                ),
                child: Text(
                  insight.displayBadge,
                  style: TextStyle(
                    color: statusColor,
                    fontSize: 12,
                    fontWeight: FontWeight.w800,
                  ),
                ),
              ),
              const Spacer(),
              Text(
                _getConfidenceText(),
                style: TextStyle(
                  color: const Color(0xFF6B7280),
                  fontSize: 12,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          Text(
            insight.title,
            style: const TextStyle(
              color: Color(0xFF111827),
              fontSize: 18,
              fontWeight: FontWeight.w900,
              height: 1.25,
            ),
          ),
          const SizedBox(height: 10),
          Text(
            insight.summary,
            style: TextStyle(
              color: const Color(0xFF6B7280),
              fontSize: 13.5,
              height: 1.45,
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(height: 14),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(13),
            decoration: BoxDecoration(
              color: const Color(0xFFE8F3F8),
              borderRadius: BorderRadius.circular(16),
            ),
            child: Text(
              insight.reason,
              style: const TextStyle(
                color: Color(0xFF073B5A),
                fontSize: 12.5,
                height: 1.4,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
          const SizedBox(height: 14),
          Row(
            children: [
              _MiniStatChip(
                label: 'Score',
                value: insight.trendScore.toStringAsFixed(2),
              ),
              const SizedBox(width: 10),
              _MiniStatChip(
                label: 'Growth',
                value: insight.growthRate.toStringAsFixed(2),
              ),
              const SizedBox(width: 10),
              _MiniStatChip(
                label: insight.attributeType.replaceAll('_', ' '),
                value: insight.attributeValue,
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _MiniStatChip extends StatelessWidget {
  final String label;
  final String value;

  const _MiniStatChip({
    required this.label,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(
          horizontal: 10,
          vertical: 10,
        ),
        decoration: BoxDecoration(
          color: const Color(0xFF0B5D85).withValues(alpha: 0.08),
          borderRadius: BorderRadius.circular(14),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              label.toUpperCase(),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: TextStyle(
                color: const Color(0xFF6B7280),
                fontSize: 9,
                fontWeight: FontWeight.w900,
                letterSpacing: 0.4,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              value,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(
                color: Color(0xFF111827),
                fontSize: 12,
                fontWeight: FontWeight.w900,
              ),
            ),
          ],
        ),
      ),
    );
  }
}