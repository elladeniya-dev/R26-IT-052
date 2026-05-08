import 'package:flutter/material.dart';

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

  Future<void> checkStoredToken() async {
    _isLoading = true;
    notifyListeners();

    final token = await _authService.getStoredToken();

    if (token != null && token.isNotEmpty) {
      // Later we will call GET /auth/me here to restore user data.
      // For now, token storage is ready.
    }

    _isLoading = false;
    notifyListeners();
  }

  Future<bool> signInWithGoogle() async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final user = await _authService.signInWithGoogle();
      _currentUser = user;

      _isLoading = false;
      notifyListeners();

      return true;
    } catch (e) {
      _errorMessage = e.toString();

      _isLoading = false;
      notifyListeners();

      return false;
    }
  }

  Future<void> logout() async {
    await _authService.signOut();
    _currentUser = null;
    _errorMessage = null;
    notifyListeners();
  }
}