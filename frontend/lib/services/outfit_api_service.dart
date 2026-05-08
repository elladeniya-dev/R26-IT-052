import 'dart:convert';

import 'package:http/http.dart' as http;

import '../constants/api_constants.dart';
import '../models/outfit_model.dart';

class OutfitApiService {
  Future<OutfitGenerateResponse> generateOutfits({
    required String userId,
    required String selectedItemId,
    required String occasion,
    int maxOutfits = 5,
    double minPrice = 3000,
    double maxPrice = 10000,
    List<String> preferredColors = const ['white', 'blue', 'black'],
    List<String> excludedCategories = const [],
    int maxItemsPerCategory = 5,
  }) async {
    final Map<String, dynamic> requestBody = {
      'user_id': userId,
      'selected_item_id': selectedItemId,
      'occasion': occasion,
      'max_outfits': maxOutfits,
      'min_price': minPrice,
      'max_price': maxPrice,
      'preferred_colors': preferredColors,
      'excluded_categories': excludedCategories,
      'max_items_per_category': maxItemsPerCategory,
    };

    try {
      final response = await http
          .post(
            Uri.parse(ApiConstants.generateOutfitsEndpoint),
            headers: {
              'Content-Type': 'application/json',
              'Accept': 'application/json',
            },
            body: jsonEncode(requestBody),
          )
          .timeout(const Duration(seconds: 30));

      final Map<String, dynamic> responseBody = jsonDecode(response.body);

      if (response.statusCode >= 200 && response.statusCode < 300) {
        return OutfitGenerateResponse.fromJson(responseBody);
      }

      final String errorMessage =
          responseBody['detail']?.toString() ??
          responseBody['message']?.toString() ??
          'Failed to generate outfits';

      throw Exception(errorMessage);
    } catch (error) {
      throw Exception('Backend connection failed: $error');
    }
  }
}