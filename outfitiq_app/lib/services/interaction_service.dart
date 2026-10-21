import 'dart:convert';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;

import '../core/api_config.dart';

class InteractionService {
  static const String _tokenKey = 'access_token';

  final FlutterSecureStorage _secureStorage = const FlutterSecureStorage();

  Future<void> sendInteraction({
    required String itemId,
    required String interactionType,
  }) async {
    final String? token = await _secureStorage.read(key: _tokenKey);

    if (token == null || token.isEmpty) {
      throw Exception('User token not found. Please login again.');
    }

    final url = Uri.parse('${ApiConfig.baseUrl}/interactions');

    final response = await http.post(
      url,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
      body: jsonEncode({
        'item_id': itemId,
        'interaction_type': interactionType,
      }),
    );

    if (response.statusCode != 200 && response.statusCode != 201) {
      Map<String, dynamic> responseData = {};

      try {
        responseData = jsonDecode(response.body);
      } catch (_) {
        throw Exception('Failed to save user interaction.');
      }

      throw Exception(
        responseData['detail'] ?? 'Failed to save user interaction.',
      );
    }
  }
}