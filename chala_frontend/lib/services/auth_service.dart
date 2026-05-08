import 'dart:convert';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:http/http.dart' as http;

import '../core/api_config.dart';
import '../models/user_model.dart';

class AuthService {
  static const String _tokenKey = 'access_token';

  // This is your Web application client ID.
  // Do not replace this with the Android client ID.
  static const String _webClientId =
      '722642303671-ub1bipd4gl2egr46c07e809r1n9nts45.apps.googleusercontent.com';

  final FlutterSecureStorage _secureStorage = const FlutterSecureStorage();

  bool _isGoogleSignInInitialized = false;

  Future<void> _initializeGoogleSignIn() async {
    if (_isGoogleSignInInitialized) {
      return;
    }

    await GoogleSignIn.instance.initialize(
      serverClientId: _webClientId,
    );

    _isGoogleSignInInitialized = true;
  }

  Future<String?> getStoredToken() async {
    return await _secureStorage.read(key: _tokenKey);
  }

  Future<void> saveToken(String token) async {
    await _secureStorage.write(key: _tokenKey, value: token);
  }

  Future<void> clearToken() async {
    await _secureStorage.delete(key: _tokenKey);
  }

  Future<UserModel> signInWithGoogle() async {
    await _initializeGoogleSignIn();

    final GoogleSignInAccount googleUser =
        await GoogleSignIn.instance.authenticate(
      scopeHint: ['email', 'profile'],
    );

    final String? googleIdToken = googleUser.authentication.idToken;

    if (googleIdToken == null || googleIdToken.isEmpty) {
      throw Exception('Google ID token was not received.');
    }

    return await loginWithBackend(googleIdToken);
  }

  Future<UserModel> loginWithBackend(String googleIdToken) async {
    final url = Uri.parse('${ApiConfig.baseUrl}/auth/google');

    final response = await http.post(
      url,
      headers: {
        'Content-Type': 'application/json',
      },
      body: jsonEncode({
        'token': googleIdToken,
      }),
    );

    final Map<String, dynamic> responseData = jsonDecode(response.body);

    if (response.statusCode == 200) {
      final String accessToken = responseData['access_token'];
      await saveToken(accessToken);

      return UserModel.fromJson(responseData['user']);
    } else {
      throw Exception(
        responseData['detail'] ?? 'Google login failed. Please try again.',
      );
    }
  }

  Future<void> signOut() async {
    await _initializeGoogleSignIn();
    await GoogleSignIn.instance.signOut();
    await clearToken();
  }
}