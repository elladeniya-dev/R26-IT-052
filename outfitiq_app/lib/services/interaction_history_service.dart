import 'dart:convert';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;

import '../core/api_config.dart';

class InteractionHistoryService {
  static const String _tokenKey = 'access_token';

  final FlutterSecureStorage _secureStorage = const FlutterSecureStorage();

  Future<Map<String, dynamic>> getInteractionHistory() async {
    final String? token = await _secureStorage.read(key: _tokenKey);

    if (token == null || token.isEmpty) {
      throw Exception('User token not found. Please login again.');
    }

    final url = Uri.parse('${ApiConfig.baseUrl}/interactions/history');

    final response = await http.get(
      url,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
    );

    final Map<String, dynamic> responseData = jsonDecode(response.body);

    if (response.statusCode == 200) {
      return responseData;
    }

    throw Exception(
      responseData['detail'] ?? 'Failed to load interaction history.',
    );
  }
}