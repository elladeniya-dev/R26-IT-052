import 'dart:convert';

import 'package:http/http.dart' as http;

import '../models/recommendation_product_model.dart';

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
          const Duration(seconds: 15),
        );

    if (response.statusCode != 200) {
      throw Exception(
        'Failed to load recommendations. Status code: ${response.statusCode}',
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

    return normalized;
  }

  String _normalizeStyle(String value) {
    final String normalized = value.trim().toLowerCase();

    if (normalized == 'party wear') return 'party';

    return normalized;
  }
}