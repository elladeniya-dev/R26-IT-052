import 'dart:convert';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;

import '../core/api_config.dart';

class ProfileService {
  static const String _tokenKey = 'access_token';

  final FlutterSecureStorage _secureStorage = const FlutterSecureStorage();

  Future<Map<String, dynamic>> getProfile() async {
    final String? token = await _secureStorage.read(key: _tokenKey);

    if (token == null || token.isEmpty) {
      throw Exception('Login token not found. Please sign in again.');
    }

    final url = Uri.parse('${ApiConfig.baseUrl}/profile');

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
    } else {
      throw Exception(
        responseData['detail'] ?? 'Failed to load profile details.',
      );
    }
  }
}