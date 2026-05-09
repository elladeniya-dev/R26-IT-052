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
    required List<String> preferredPatterns,
  }) async {
    final String? token = await _secureStorage.read(key: _tokenKey);

    if (token == null || token.isEmpty) {
      throw Exception('Login token not found. Please sign in again.');
    }

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
}