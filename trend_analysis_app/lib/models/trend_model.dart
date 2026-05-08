class TrendModel {
  final int trendId;
  final String attributeType;
  final String attributeValue;
  final double trendScore;
  final double growthRate;
  final String timeWindow;
  final String startDate;
  final String endDate;
  final String generatedAt;

  TrendModel({
    required this.trendId,
    required this.attributeType,
    required this.attributeValue,
    required this.trendScore,
    required this.growthRate,
    required this.timeWindow,
    required this.startDate,
    required this.endDate,
    required this.generatedAt,
  });

  factory TrendModel.fromJson(Map<String, dynamic> json) {
    return TrendModel(
      trendId: json['trend_id'] ?? 0,
      attributeType: json['attribute_type'] ?? '',
      attributeValue: json['attribute_value'] ?? '',
      trendScore: (json['trend_score'] ?? 0).toDouble(),
      growthRate: (json['growth_rate'] ?? 0).toDouble(),
      timeWindow: json['time_window'] ?? '',
      startDate: json['start_date'] ?? '',
      endDate: json['end_date'] ?? '',
      generatedAt: json['generated_at'] ?? '',
    );
  }
}