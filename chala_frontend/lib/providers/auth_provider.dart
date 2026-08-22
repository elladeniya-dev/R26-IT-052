import 'package:flutter/material.dart';
import 'package:google_sign_in/google_sign_in.dart';

import '../models/user_model.dart';
import '../services/auth_service.dart';

class AuthProvider extends ChangeNotifier {
  final AuthService _authService = AuthService();

  UserModel? _currentUser;
  bool _isLoading = false;
  String? _errorMessage;

  UserModel? get currentUser => _currentUser;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;
  bool get isLoggedIn => _currentUser != null;

  /// Checks whether a backend JWT has already been stored.
  Future<void> checkStoredToken() async {
    _isLoading = true;
    notifyListeners();

    try {
      final token = await _authService.getStoredToken();

      if (token != null && token.isNotEmpty) {
        // Later we can call GET /auth/me here
        // to restore the complete logged-in user.
      }
    } catch (e) {
      _errorMessage = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Android / iOS Google Sign-In.
  Future<bool> signInWithGoogle() async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final UserModel user =
          await _authService.signInWithGoogle();

      _currentUser = user;

      _isLoading = false;
      notifyListeners();

      return true;
    } catch (e) {
      _errorMessage = _cleanErrorMessage(e);

      _isLoading = false;
      notifyListeners();

      return false;
    }
  }

  /// Flutter Web Google Sign-In.
  Future<bool> signInWithGoogleWeb(
    GoogleSignInAccount googleUser,
  ) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final UserModel user =
          await _authService.handleGoogleAccount(
        googleUser,
      );

      _currentUser = user;

      _isLoading = false;
      notifyListeners();

      return true;
    } catch (e) {
      _errorMessage = _cleanErrorMessage(e);

      _isLoading = false;
      notifyListeners();

      return false;
    }
  }

  /// Initializes Google Sign-In.
  Future<void> initializeGoogleSignIn() async {
    await _authService.initializeGoogleSignIn();
  }

  /// Permanently deletes the user's account and saved data.
  Future<bool> deleteAccount() async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      await _authService.deleteAccount();

      _currentUser = null;
      _errorMessage = null;
      _isLoading = false;

      notifyListeners();

      return true;
    } catch (e) {
      _errorMessage = _cleanErrorMessage(e);

      _isLoading = false;
      notifyListeners();

      return false;
    }
  }

  /// Logout from Google and clear backend JWT.
  Future<void> logout() async {
    try {
      await _authService.signOut();
    } finally {
      _currentUser = null;
      _errorMessage = null;
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Clears an old authentication error from the UI.
  void clearError() {
    _errorMessage = null;
    notifyListeners();
  }

  /// Removes prefixes such as Exception: from errors.
  String _cleanErrorMessage(Object error) {
    String message = error.toString();

    if (message.startsWith('Exception: ')) {
      message = message.substring('Exception: '.length);
    }

    return message;
  }
}