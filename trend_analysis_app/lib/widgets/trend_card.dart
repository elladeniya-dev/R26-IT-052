import 'package:flutter/material.dart';

import '../models/trend_model.dart';

class TrendCard extends StatelessWidget {
  final TrendModel trend;
  final IconData icon;
  final String formattedType;
  final VoidCallback onTap;

  const TrendCard({
    super.key,
    required this.trend,
    required this.icon,
    required this.formattedType,
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
              color: Colors.black.withValues(alpha: 0.05),
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
      ),
    );
  }
}