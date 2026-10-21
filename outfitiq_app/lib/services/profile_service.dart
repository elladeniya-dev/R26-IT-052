import 'dart:convert';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;

import '../core/api_config.dart';

class ProfileService {
  static const String _tokenKey = 'access_token';

  final FlutterSecureStorage _secureStorage =
      const FlutterSecureStorage();

  Future<String> _getToken() async {
    final String? token =
        await _secureStorage.read(key: _tokenKey);

    if (token == null || token.isEmpty) {
      throw Exception(
        'Login token not found. Please sign in again.',
      );
    }

    return token;
  }

  // =========================================================
  // GET USER PROFILE
  // =========================================================

  Future<Map<String, dynamic>> getProfile() async {
    final String token = await _getToken();

    final Uri url =
        Uri.parse('${ApiConfig.baseUrl}/profile');

    final http.Response response = await http.get(
      url,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
    );

    final Map<String, dynamic> responseData =
        jsonDecode(response.body);

    if (response.statusCode == 200) {
      return responseData;
    }

    throw Exception(
      responseData['detail'] ??
          'Failed to load profile details.',
    );
  }

  // =========================================================
  // GET CURRENT DYNAMIC PREFERENCES
  // =========================================================
  //
  // This is the original endpoint.
  //
  // It returns the preferences produced from:
  // onboarding + behavioral learning.
  //
  // We keep this method because other parts of the
  // application may still use it.
  // =========================================================

  Future<Map<String, dynamic>>
      getCurrentPreferences() async {
    final String token = await _getToken();

    final Uri url = Uri.parse(
      '${ApiConfig.baseUrl}/profile/current-preferences',
    );

    final http.Response response = await http.get(
      url,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
    );

    final Map<String, dynamic> responseData =
        jsonDecode(response.body);

    if (response.statusCode == 200) {
      return responseData;
    }

    throw Exception(
      responseData['detail'] ??
          'Failed to load current preferences.',
    );
  }

  // =========================================================
  // GET ML-ENRICHED CURRENT PREFERENCES
  // =========================================================
  //
  // Flow:
  //
  // Onboarding
  //      +
  // User interactions
  //      ↓
  // Dynamic current preferences
  //      ↓
  // Logistic Regression ML expansion
  //      ↓
  // Final enriched preference profile
  //
  // This is the endpoint used by the updated
  // My Current Preferences screen.
  // =========================================================

  Future<Map<String, dynamic>>
      getEnrichedCurrentPreferences() async {
    final String token = await _getToken();

    final Uri url = Uri.parse(
      '${ApiConfig.baseUrl}/profile/enriched-current-preferences',
    );

    final http.Response response = await http.get(
      url,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
    );

    final Map<String, dynamic> responseData =
        jsonDecode(response.body);

    if (response.statusCode == 200) {
      return responseData;
    }

    throw Exception(
      responseData['detail'] ??
          'Failed to load enriched current preferences.',
    );
  }
}