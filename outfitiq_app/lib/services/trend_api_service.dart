import 'dart:convert';

import 'package:http/http.dart' as http;

import '../core/api_config.dart';
import '../models/recommendation_product_model.dart';

/// What the trend engine needs to describe one cloth. Nothing else is sent.
Map<String, dynamic> trendScoringPayload(RecommendationProduct p) => {
      'id': p.itemId,
      'title': p.title,
      'category': p.category,
      'subcategory': p.subcategory,
      'colors': p.color,
      'tags': p.style,
    };

double _toDouble(dynamic value) {
  if (value == null) return 0.0;
  if (value is num) return value.toDouble();
  return double.tryParse(value.toString()) ?? 0.0;
}

/// One half of a trend segment, e.g. colour "white" of "white + dress".
class SegmentPart {
  final String attributeType;
  final String value;

  SegmentPart({required this.attributeType, required this.value});

  factory SegmentPart.fromJson(Map<String, dynamic> json) => SegmentPart(
        attributeType: (json['attr_type'] ?? '').toString(),
        value: (json['attr_value'] ?? '').toString(),
      );
}

List<SegmentPart> _partsFrom(dynamic raw) => raw is List
    ? [
        for (final item in raw)
          if (item is Map<String, dynamic>) SegmentPart.fromJson(item),
      ]
    : <SegmentPart>[];

/// A rising combination of attributes, e.g. "white + dress".
///
/// One rising attribute says nothing about a cloth ("white" rising does not
/// make a white cloth trending), so the trend engine also forecasts pairs of
/// attributes. Matches GET /api/v1/trends/segments.
class TrendSegment {
  final String segment;
  final String segmentType;
  final List<SegmentPart> parts;
  final double score;
  final String confidence;
  final int storesCarrying;

  TrendSegment({
    required this.segment,
    required this.segmentType,
    required this.parts,
    required this.score,
    required this.confidence,
    required this.storesCarrying,
  });

  factory TrendSegment.fromJson(Map<String, dynamic> json) => TrendSegment(
        segment: (json['segment'] ?? '').toString(),
        segmentType: (json['segment_type'] ?? '').toString(),
        parts: _partsFrom(json['parts']),
        score: _toDouble(json['score']),
        confidence: (json['confidence'] ?? '').toString(),
        storesCarrying: _toDouble(json['stores_carrying']).round(),
      );
}

/// Why one cloth scored: a rising segment it carries both parts of.
class ProductSegmentMatch {
  final String segment;
  final String segmentType;
  final List<SegmentPart> parts;
  final String match; // exact | family
  final String confidence;
  final double trendScore;
  final double contribution;

  ProductSegmentMatch({
    required this.segment,
    required this.segmentType,
    required this.parts,
    required this.match,
    required this.confidence,
    required this.trendScore,
    required this.contribution,
  });

  factory ProductSegmentMatch.fromJson(Map<String, dynamic> json) =>
      ProductSegmentMatch(
        segment: (json['segment'] ?? '').toString(),
        segmentType: (json['segment_type'] ?? '').toString(),
        parts: _partsFrom(json['parts']),
        match: (json['match'] ?? '').toString(),
        confidence: (json['confidence'] ?? '').toString(),
        trendScore: _toDouble(json['trend_score']),
        contribution: _toDouble(json['contribution']),
      );
}

/// Trend result for one cloth from POST /api/v1/trends/score-products.
class ProductTrend {
  final String id;
  final double segmentScore;
  final List<ProductSegmentMatch> segments;

  ProductTrend({
    required this.id,
    required this.segmentScore,
    required this.segments,
  });

  bool get isTrending => segmentScore > 0 && segments.isNotEmpty;

  factory ProductTrend.fromJson(Map<String, dynamic> json) => ProductTrend(
        id: (json['id'] ?? '').toString(),
        segmentScore: _toDouble(json['segment_score']),
        segments: [
          if (json['segments'] is List)
            for (final item in json['segments'])
              if (item is Map<String, dynamic>)
                ProductSegmentMatch.fromJson(item),
        ],
      );
}

class TrendApiService {
  static String get baseUrl => ApiConfig.trendBaseUrl;

  // The backend accepts at most this many products per scoring call.
  static const int _scoreBatchSize = 500;

  /// Currently rising attribute combinations, strongest first. Only medium and
  /// high confidence ones, so the list is a signal rather than noise.
  ///
  /// Deliberately does NOT call /trends/products — that endpoint returns
  /// products from Givi's own scraped catalog, which must never be shown
  /// to the user. Only Koji's catalog is a valid product source.
  Future<List<TrendSegment>> getTrendingSegments({
    int horizon = 3,
    int limit = 30,
  }) async {
    final http.Response response = await http
        .get(Uri.parse(
          '$baseUrl/api/v1/trends/segments'
          '?horizon=$horizon&limit=$limit&min_confidence=medium',
        ))
        .timeout(const Duration(seconds: 20));

    if (response.statusCode != 200) {
      throw Exception('Trend segments failed (${response.statusCode}).');
    }

    final dynamic decoded = jsonDecode(response.body);
    final dynamic data = decoded is Map<String, dynamic> ? decoded['data'] : null;
    return [
      if (data is List)
        for (final item in data)
          if (item is Map<String, dynamic>) TrendSegment.fromJson(item),
    ];
  }

  /// Scores partner products against the rising segments with the trend
  /// engine's stateless POST /api/v1/trends/score-products. Returns
  /// {productId: ProductTrend}; products in no rising segment are left out.
  Future<Map<String, ProductTrend>> scoreProducts(
    List<Map<String, dynamic>> products, {
    int horizon = 3,
  }) async {
    final Map<String, ProductTrend> results = {};

    for (int start = 0; start < products.length; start += _scoreBatchSize) {
      final int end = start + _scoreBatchSize < products.length
          ? start + _scoreBatchSize
          : products.length;

      final http.Response response = await http
          .post(
            Uri.parse('$baseUrl/api/v1/trends/score-products'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({
              'products': products.sublist(start, end),
              'horizon': horizon,
            }),
          )
          .timeout(const Duration(seconds: 20));

      if (response.statusCode != 200) {
        throw Exception('Trend scoring failed (${response.statusCode}).');
      }

      final dynamic decoded = jsonDecode(response.body);
      final dynamic data = decoded is Map<String, dynamic> ? decoded['data'] : null;
      if (data is List) {
        for (final item in data) {
          if (item is Map<String, dynamic>) {
            final ProductTrend trend = ProductTrend.fromJson(item);
            if (trend.isTrending) results[trend.id] = trend;
          }
        }
      }
    }
    return results;
  }
}
