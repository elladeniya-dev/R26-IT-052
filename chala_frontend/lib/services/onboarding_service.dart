import 'dart:convert';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;

import '../core/api_config.dart';

class OnboardingService {
  static const String _tokenKey = 'access_token';

  final FlutterSecureStorage _secureStorage = const FlutterSecureStorage();

  Future<void> submitOnboarding({
    required List<String> preferredCategories,
    required List<String> preferredColors,
    required List<String> preferredStyles,
    required List<String> occasions,
    required String budgetRange,
    required List<String> preferredPatterns,
  }) async {
    final String? token = await _secureStorage.read(key: _tokenKey);

    if (token == null || token.isEmpty) {
      throw Exception('Login token not found. Please sign in again.');
    }

    final budgetValues = _getBudgetValues(budgetRange);

    final url = Uri.parse('${ApiConfig.baseUrl}/onboarding');

    final response = await http.post(
      url,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
      body: jsonEncode({
        'preferred_categories': preferredCategories,
        'preferred_colors': preferredColors,
        'preferred_styles': preferredStyles,
        'price_min': budgetValues['price_min'],
        'price_max': budgetValues['price_max'],
        'occasions': occasions,
        'preferred_patterns': preferredPatterns,
        'extra_preferences': {},
      }),
    );

    if (response.statusCode != 200 && response.statusCode != 201) {
      final Map<String, dynamic> responseData = jsonDecode(response.body);

      throw Exception(
        responseData['detail'] ?? 'Failed to save onboarding preferences.',
      );
    }
  }

  Map<String, int?> _getBudgetValues(String budgetRange) {
    switch (budgetRange) {
      case 'Below 2,000 LKR':
        return {
          'price_min': 0,
          'price_max': 2000,
        };
      case '2,000 - 5,000 LKR':
        return {
          'price_min': 2000,
          'price_max': 5000,
        };
      case '5,000 - 10,000 LKR':
        return {
          'price_min': 5000,
          'price_max': 10000,
        };
      case '10,000 - 20,000 LKR':
        return {
          'price_min': 10000,
          'price_max': 20000,
        };
      case 'Above 20,000 LKR':
        return {
          'price_min': 20000,
          'price_max': null,
        };
      default:
        return {
          'price_min': null,
          'price_max': null,
        };
    }
  }
}