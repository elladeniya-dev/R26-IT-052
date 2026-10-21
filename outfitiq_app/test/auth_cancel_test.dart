import 'package:flutter_test/flutter_test.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:outfitiq_app/models/user_model.dart';
import 'package:outfitiq_app/providers/auth_provider.dart';
import 'package:outfitiq_app/services/auth_service.dart';

class _FakeAuthService extends AuthService {
  _FakeAuthService(this.onSignIn);

  final Future<UserModel> Function() onSignIn;

  @override
  Future<UserModel> signInWithGoogle() => onSignIn();
}

void main() {
  test('closing the Google account picker is not an error', () async {
    final provider = AuthProvider(
      authService: _FakeAuthService(() async => throw const GoogleSignInException(
            code: GoogleSignInExceptionCode.canceled,
            description: 'User closed the account picker',
          )),
    );

    final bool success = await provider.signInWithGoogle();

    expect(success, isFalse);
    expect(provider.signInCancelled, isTrue);
    expect(provider.errorMessage, isNull);
    expect(provider.isLoading, isFalse);
    expect(provider.isLoggedIn, isFalse);
  });

  test('a real failure still reports an error and is not treated as a cancel', () async {
    final provider = AuthProvider(
      authService: _FakeAuthService(() async => throw Exception('Backend login failed (500).')),
    );

    final bool success = await provider.signInWithGoogle();

    expect(success, isFalse);
    expect(provider.signInCancelled, isFalse);
    expect(provider.errorMessage, 'Backend login failed (500).');
  });

  test('a misconfigured client is an error, not a cancel', () async {
    final provider = AuthProvider(
      authService: _FakeAuthService(() async => throw const GoogleSignInException(
            code: GoogleSignInExceptionCode.clientConfigurationError,
            description: 'bad client id',
          )),
    );

    await provider.signInWithGoogle();

    expect(provider.signInCancelled, isFalse);
    expect(provider.errorMessage, isNotNull);
  });

  test('a cancel does not stick: the next attempt starts clean', () async {
    int calls = 0;
    final provider = AuthProvider(
      authService: _FakeAuthService(() async {
        calls++;
        if (calls == 1) {
          throw const GoogleSignInException(code: GoogleSignInExceptionCode.canceled);
        }
        throw Exception('Network down');
      }),
    );

    await provider.signInWithGoogle();
    expect(provider.signInCancelled, isTrue);

    await provider.signInWithGoogle();
    expect(provider.signInCancelled, isFalse);
    expect(provider.errorMessage, 'Network down');
  });

  test('isUserCancel only matches the cancel code', () {
    expect(
      AuthProvider.isUserCancel(const GoogleSignInException(code: GoogleSignInExceptionCode.canceled)),
      isTrue,
    );
    expect(
      AuthProvider.isUserCancel(const GoogleSignInException(code: GoogleSignInExceptionCode.interrupted)),
      isFalse,
    );
    expect(AuthProvider.isUserCancel(Exception('canceled')), isFalse);
  });
}
