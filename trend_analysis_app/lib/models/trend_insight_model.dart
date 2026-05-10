class TrendInsightModel {
  final int trendId;
  final String title;
  final String summary;
  final String reason;
  final String attributeType;
  final String attributeValue;
  final double trendScore;
  final double growthRate;
  final String trendStatus;
  final double confidence;
  final String displayBadge;

  TrendInsightModel({
    required this.trendId,
    required this.title,
    required this.summary,
    required this.reason,
    required this.attributeType,
    required this.attributeValue,
    required this.trendScore,
    required this.growthRate,
    required this.trendStatus,
    required this.confidence,
    required this.displayBadge,
  });

  factory TrendInsightModel.fromJson(Map<String, dynamic> json) {
    return TrendInsightModel(
      trendId: json['trend_id'] ?? 0,
      title: json['title'] ?? '',
      summary: json['summary'] ?? '',
      reason: json['reason'] ?? '',
      attributeType: json['attribute_type'] ?? '',
      attributeValue: json['attribute_value'] ?? '',
      trendScore: (json['trend_score'] ?? 0).toDouble(),
      growthRate: (json['growth_rate'] ?? 0).toDouble(),
      trendStatus: json['trend_status'] ?? '',
      confidence: (json['confidence'] ?? 0).toDouble(),
      displayBadge: json['display_badge'] ?? '',
    );
  }
}