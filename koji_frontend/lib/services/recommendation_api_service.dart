import 'dart:convert';

import 'package:http/http.dart' as http;

import '../models/recommendation_product_model.dart';

class AppliedPreferences {
  final List<String> categories;
  final List<String> colors;
  final List<String> styles;
  final List<String> occasions;
  final List<String> preferredBrands;

  AppliedPreferences({
    required this.categories,
    required this.colors,
    required this.styles,
    required this.occasions,
    required this.preferredBrands,
  });

  factory AppliedPreferences.fromJson(Map<String, dynamic>? json) {
    if (json == null) {
      return AppliedPreferences(
        categories: [],
        colors: [],
        styles: [],
        occasions: [],
        preferredBrands: [],
      );
    }

    return AppliedPreferences(
      categories: _toStringList(json['categories']),
      colors: _toStringList(json['colors']),
      styles: _toStringList(json['styles']),
      occasions: _toStringList(json['occasions']),
      preferredBrands: _toStringList(json['preferred_brands']),
    );
  }

  static List<String> _toStringList(dynamic value) {
    if (value is! List) {
      return [];
    }

    return value.map((item) => item.toString()).toList();
  }
}

class RecommendationApiService {
  /*
    For Chrome testing:
    baseUrl = 'http://127.0.0.1:8000'

    For physical iPhone testing:
    1. Connect Mac and iPhone to the same Wi-Fi.
    2. Run backend using:
       python -m uvicorn app.main:app --reload --host 0.0.0.0
    3. Replace 127.0.0.1 with your Mac Wi-Fi IP.
       Example:
       baseUrl = 'http://192.168.1.5:8000'
  */
  static const String baseUrl = 'http://127.0.0.1:8000';

  AppliedPreferences? lastAppliedPreferences;

  /*
    Integrated endpoint.

    Flutter sends only user_id, price range, and max_results.
    Koji backend calls Chala backend internally and gets enriched preferences.

    Retry logic is added because Chala backend is hosted on Render Free.
    The first request may wake the service and fail. The second request usually works.
  */
  Future<List<RecommendationProduct>> getRecommendationsFromChala({
    required int userId,
    required double priceMin,
    required double priceMax,
    required int maxResults,
  }) async {
    final Uri url = Uri.parse('$baseUrl/recommendations/from-chala');

    final Map<String, dynamic> requestBody = {
      'user_id': userId,
      'price_min': priceMin,
      'price_max': priceMax,
      'max_results': maxResults,
    };

    http.Response? response;
    Object? lastError;

    for (int attempt = 1; attempt <= 2; attempt++) {
      try {
        response = await http
            .post(
              url,
              headers: {
                'Content-Type': 'application/json',
              },
              body: jsonEncode(requestBody),
            )
            .timeout(
              const Duration(seconds: 120),
            );

        if (response.statusCode == 200) {
          break;
        }

        lastError =
            'Status code: ${response.statusCode}. Response: ${response.body}';

        if (attempt == 1) {
          await Future.delayed(const Duration(seconds: 5));
          continue;
        }
      } catch (error) {
        lastError = error;

        if (attempt == 1) {
          await Future.delayed(const Duration(seconds: 5));
          continue;
        }
      }
    }

    if (response == null || response.statusCode != 200) {
      throw Exception(
        'Failed to load Chala integrated recommendations after retry. '
        'Last error: $lastError',
      );
    }

    final Map<String, dynamic> decodedBody = jsonDecode(response.body);

    lastAppliedPreferences = AppliedPreferences.fromJson(
      decodedBody['applied_preferences'] as Map<String, dynamic>?,
    );

    final List<dynamic> recommendations =
        decodedBody['recommendations'] as List<dynamic>? ?? [];

    return recommendations
        .map(
          (item) => RecommendationProduct.fromJson(
            item as Map<String, dynamic>,
          ),
        )
        .toList();
  }

  /*
    Existing manual recommendation endpoint.

    Keep this for testing your recommendation engine manually from Flutter.
  */
  Future<List<RecommendationProduct>> getRecommendations({
    required String userId,
    required List<String> preferredCategories,
    required List<String> preferredColors,
    required List<String> preferredStyles,
    required List<String> preferredBrands,
    required double priceMin,
    required double priceMax,
    required int maxResults,
  }) async {
    final Uri url = Uri.parse('$baseUrl/recommendations/');

    final Map<String, dynamic> requestBody = {
      'user_id': userId,
      'preferred_categories':
          preferredCategories.map(_normalizeCategory).toList(),
      'preferred_colors': preferredColors.map(_normalizeText).toList(),
      'preferred_styles': preferredStyles.map(_normalizeStyle).toList(),
      'preferred_brands': preferredBrands
          .where((brand) => brand != 'No specific brand')
          .toList(),
      'price_min': priceMin,
      'price_max': priceMax,
      'max_results': maxResults,
    };

    final http.Response response = await http
        .post(
          url,
          headers: {
            'Content-Type': 'application/json',
          },
          body: jsonEncode(requestBody),
        )
        .timeout(
          const Duration(seconds: 30),
        );

    if (response.statusCode != 200) {
      throw Exception(
        'Failed to load recommendations. '
        'Status code: ${response.statusCode}. '
        'Response: ${response.body}',
      );
    }

    final Map<String, dynamic> decodedBody = jsonDecode(response.body);

    final List<dynamic> recommendations =
        decodedBody['recommendations'] as List<dynamic>? ?? [];

    return recommendations
        .map(
          (item) => RecommendationProduct.fromJson(
            item as Map<String, dynamic>,
          ),
        )
        .toList();
  }

  String _normalizeText(String value) {
    return value.trim().toLowerCase();
  }

  String _normalizeCategory(String value) {
    final String normalized = value.trim().toLowerCase();

    if (normalized.contains('dress')) return 'dress';
    if (normalized.contains('top')) return 'top';
    if (normalized.contains('jean')) return 'jeans';
    if (normalized.contains('blazer')) return 'blazer';
    if (normalized.contains('jacket')) return 'jacket';
    if (normalized.contains('skirt')) return 'skirt';
    if (normalized.contains('trouser')) return 'pants';

    return normalized;
  }

  String _normalizeStyle(String value) {
    final String normalized = value.trim().toLowerCase();

    if (normalized == 'party wear') return 'party';
    if (normalized == 'comfort wear') return 'comfort';

    return normalized;
  }
}