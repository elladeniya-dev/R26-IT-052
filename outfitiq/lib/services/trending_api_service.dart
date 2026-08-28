import 'dart:convert';

import 'package:http/http.dart' as http;

import '../models/trending_product_model.dart';

class TrendingApiService {
  // Same backend, same host convention as RecommendationApiService — see the
  // comment block there for Chrome vs physical-device setup.
  static const String baseUrl = 'http://127.0.0.1:8000';

  Future<List<TrendingProduct>> getTrendingProducts({int limit = 20}) async {
    final Uri url = Uri.parse('$baseUrl/trending-products/?limit=$limit');

    final http.Response response = await http.get(url).timeout(
          const Duration(seconds: 15),
        );

    if (response.statusCode != 200) {
      throw Exception(
        'Failed to load trending products. Status code: ${response.statusCode}',
      );
    }

    final Map<String, dynamic> decodedBody = jsonDecode(response.body);

    final List<dynamic> products =
        decodedBody['products'] as List<dynamic>? ?? [];

    return products
        .map(
          (item) => TrendingProduct.fromJson(item as Map<String, dynamic>),
        )
        .toList();
  }
}
