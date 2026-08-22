import 'dart:async';
import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:http/http.dart' as http;

import '../core/api_config.dart';
import '../models/user_model.dart';

class AuthService {
  static const String _tokenKey = 'access_token';

  // Google Web OAuth Client ID
  static const String _webClientId =
      '722642303671-ub1bipd4gl2egr46c07e809r1n9nts45.apps.googleusercontent.com';

  final FlutterSecureStorage _secureStorage =
      const FlutterSecureStorage();

  static bool _isGoogleSignInInitialized = false;

  /// Initialize Google Sign-In only once.
  Future<void> _initializeGoogleSignIn() async {
    if (_isGoogleSignInInitialized) {
      return;
    }

    if (kIsWeb) {
      await GoogleSignIn.instance.initialize();
    } else {
      await GoogleSignIn.instance.initialize(
        serverClientId: _webClientId,
      );
    }

    _isGoogleSignInInitialized = true;
  }

  /// Public initializer.
  Future<void> initializeGoogleSignIn() async {
    await _initializeGoogleSignIn();
  }

  /// Returns the stored backend JWT token.
  Future<String?> getStoredToken() async {
    return await _secureStorage.read(
      key: _tokenKey,
    );
  }

  /// Saves backend JWT token.
  Future<void> saveToken(String token) async {
    await _secureStorage.write(
      key: _tokenKey,
      value: token,
    );
  }

  /// Removes backend JWT token.
  Future<void> clearToken() async {
    await _secureStorage.delete(
      key: _tokenKey,
    );
  }

  /// Android / iOS Google Sign-In.
  Future<UserModel> signInWithGoogle() async {
    await _initializeGoogleSignIn();

    if (kIsWeb) {
      throw UnsupportedError(
        'Google authenticate() is not supported on Flutter Web. '
        'Use the Google rendered sign-in button instead.',
      );
    }

    final GoogleSignInAccount googleUser =
        await GoogleSignIn.instance.authenticate(
      scopeHint: const [
        'email',
        'profile',
      ],
    );

    final String? googleIdToken =
        googleUser.authentication.idToken;

    if (googleIdToken == null || googleIdToken.isEmpty) {
      throw Exception(
        'Google ID token was not received.',
      );
    }

    return await loginWithBackend(
      googleIdToken,
    );
  }

  /// Handles Google account returned by Web authentication.
  Future<UserModel> handleGoogleAccount(
    GoogleSignInAccount googleUser,
  ) async {
    final String? googleIdToken =
        googleUser.authentication.idToken;

    if (googleIdToken == null || googleIdToken.isEmpty) {
      throw Exception(
        'Google ID token was not received.',
      );
    }

    return await loginWithBackend(
      googleIdToken,
    );
  }

  /// Sends Google ID token to FastAPI backend.
  Future<UserModel> loginWithBackend(
    String googleIdToken,
  ) async {
    final Uri url = Uri.parse(
      '${ApiConfig.baseUrl}/auth/google',
    );

    final http.Response response;

    try {
      response = await http.post(
        url,
        headers: {
          'Content-Type': 'application/json',
        },
        body: jsonEncode({
          'token': googleIdToken,
        }),
      );
    } catch (error) {
      throw Exception(
        'Could not connect to backend: $error',
      );
    }

    Map<String, dynamic> responseData = {};

    try {
      if (response.body.isNotEmpty) {
        responseData =
            jsonDecode(response.body) as Map<String, dynamic>;
      }
    } catch (_) {
      throw Exception(
        'Backend returned an invalid response.',
      );
    }

    if (response.statusCode == 200) {
      final dynamic tokenValue =
          responseData['access_token'];

      if (tokenValue == null ||
          tokenValue.toString().isEmpty) {
        throw Exception(
          'Backend access token was not received.',
        );
      }

      final String accessToken =
          tokenValue.toString();

      await saveToken(
        accessToken,
      );

      final dynamic userData =
          responseData['user'];

      if (userData == null ||
          userData is! Map<String, dynamic>) {
        throw Exception(
          'User information was not received from backend.',
        );
      }

      return UserModel.fromJson(
        userData,
      );
    }

    final dynamic detail =
        responseData['detail'];

    throw Exception(
      detail?.toString() ??
          'Google login failed. Please try again.',
    );
  }

  /// Permanently deletes the logged-in user's account.
  Future<void> deleteAccount() async {
    final String? token = await getStoredToken();

    if (token == null || token.isEmpty) {
      throw Exception(
        'Authentication token was not found.',
      );
    }

    final Uri url = Uri.parse(
      '${ApiConfig.baseUrl}/account',
    );

    final http.Response response;

    try {
      response = await http.delete(
        url,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
      );
    } catch (error) {
      throw Exception(
        'Could not connect to backend: $error',
      );
    }

    Map<String, dynamic> responseData = {};

    try {
      if (response.body.isNotEmpty) {
        responseData =
            jsonDecode(response.body) as Map<String, dynamic>;
      }
    } catch (_) {
      throw Exception(
        'Backend returned an invalid response.',
      );
    }

    if (response.statusCode != 200) {
      final dynamic detail =
          responseData['detail'];

      throw Exception(
        detail?.toString() ??
            'Failed to delete account.',
      );
    }

    // Remove local authentication after successful deletion.
    await _initializeGoogleSignIn();

    try {
      await GoogleSignIn.instance.signOut();
    } finally {
      await clearToken();
    }
  }

  /// Sign out from Google and remove backend JWT.
  Future<void> signOut() async {
    await _initializeGoogleSignIn();

    try {
      await GoogleSignIn.instance.signOut();
    } finally {
      await clearToken();
    }
  }
}