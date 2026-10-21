import '../../models/recommendation_product_model.dart';
import '../../services/trend_api_service.dart';

/// Products shown together under one confidence level (High / Medium / Low).
class ConfidenceSection {
  final String level;
  final List<Map<String, dynamic>> products;

  ConfidenceSection({required this.level, required this.products});
}

const List<String> confidenceLevels = ['high', 'medium', 'low'];

String _levelOf(String confidence) {
  final String c = confidence.toLowerCase();
  return c == 'high' || c == 'medium' ? c : 'low';
}

/// "white + dress" -> "White + Dress".
String titleCaseSegment(String value) => value
    .split(' ')
    .map((w) => w.isEmpty ? w : '${w[0].toUpperCase()}${w.substring(1)}')
    .join(' ');

/// The segment that explains a cloth best: the most confident one it
/// matches, then the biggest contribution.
ProductSegmentMatch? primarySegment(ProductTrend trend) {
  if (trend.segments.isEmpty) return null;
  final List<ProductSegmentMatch> ordered =
      List<ProductSegmentMatch>.from(trend.segments)
        ..sort((a, b) {
          final int byLevel = confidenceLevels
              .indexOf(_levelOf(a.confidence))
              .compareTo(confidenceLevels.indexOf(_levelOf(b.confidence)));
          if (byLevel != 0) return byLevel;
          return b.contribution.compareTo(a.contribution);
        });
  return ordered.first;
}

/// Groups the cloths the trend engine scored into one list per confidence level.
///
/// A cloth is "trending" only when it carries BOTH parts of a rising segment
/// (decided by the engine), never because a single attribute such as its
/// colour is rising. Each cloth appears once, under its most confident
/// segment, strongest first. Cloths the engine did not score are left out and
/// empty sections are dropped.
List<ConfidenceSection> sectionsFromTrends(
  List<RecommendationProduct> source,
  Map<String, ProductTrend> trends, {
  Map<String, dynamic> Function(RecommendationProduct product)? cardFor,
}) {
  final List<(Map<String, dynamic>, double, String)> cards = [];
  final Set<String> seen = {};

  for (final RecommendationProduct product in source) {
    final ProductTrend? trend = trends[product.itemId];
    if (trend == null || !trend.isTrending) continue;
    final ProductSegmentMatch? primary = primarySegment(trend);
    if (primary == null || !seen.add(product.itemId)) continue;

    final Map<String, dynamic> card =
        (cardFor ?? (p) => p.toProductDetailMap())(product);
    card['trendingLabel'] = titleCaseSegment(primary.segment);
    card['trendingConfidence'] = primary.confidence;
    card['trendScore'] = trend.segmentScore;
    card['trendingSegments'] = [
      for (final ProductSegmentMatch m in trend.segments)
        titleCaseSegment(m.segment),
    ];
    cards.add((card, trend.segmentScore, _levelOf(primary.confidence)));
  }

  cards.sort((a, b) => b.$2.compareTo(a.$2));

  return [
    for (final String level in confidenceLevels)
      if (cards.any((c) => c.$3 == level))
        ConfidenceSection(
          level: level,
          products: [
            for (final c in cards)
              if (c.$3 == level) c.$1,
          ],
        ),
  ];
}
