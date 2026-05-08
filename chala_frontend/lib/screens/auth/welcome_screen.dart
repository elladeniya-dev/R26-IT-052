import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/theme.dart';
import '../../providers/auth_provider.dart';
import '../onboarding/onboarding_screen.dart';

class WelcomeScreen extends StatelessWidget {
  const WelcomeScreen({super.key});

  Future<void> _handleGoogleSignIn(BuildContext context) async {
    final authProvider = Provider.of<AuthProvider>(context, listen: false);

    final bool success = await authProvider.signInWithGoogle();

    if (!context.mounted) {
      return;
    }

    if (success) {
  ScaffoldMessenger.of(context).showSnackBar(
    SnackBar(
      content: Text(
        'Welcome ${authProvider.currentUser?.fullName ?? 'back'}!',
      ),
    ),
  );

  Navigator.pushReplacement(
    context,
    MaterialPageRoute(
      builder: (context) => const OnboardingScreen(),
    ),
  );
}

    else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            authProvider.errorMessage ?? 'Google Sign-In failed.',
          ),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.primaryColor,
      body: SafeArea(
        child: Consumer<AuthProvider>(
          builder: (context, authProvider, child) {
            return Padding(
              padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 24),
              child: Column(
                children: [
                  const SizedBox(height: 20),

                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Container(
                        width: 28,
                        height: 28,
                        decoration: const BoxDecoration(
                          color: Colors.white,
                          shape: BoxShape.rectangle,
                        ),
                        child: const Icon(
                          Icons.diamond_outlined,
                          size: 18,
                          color: AppTheme.primaryColor,
                        ),
                      ),
                      const SizedBox(width: 10),
                      const Text(
                        'Wearify',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 21,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),

                  const SizedBox(height: 36),

                  Container(
                    width: double.infinity,
                    height: 320,
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.18),
                      borderRadius: BorderRadius.circular(28),
                    ),
                    child: const Icon(
                      Icons.checkroom,
                      size: 120,
                      color: Colors.white,
                    ),
                  ),

                  const SizedBox(height: 36),

                  const Text(
                    'Discover Your Ultimate\nFashion Destination!',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 29,
                      height: 1.25,
                      fontWeight: FontWeight.bold,
                    ),
                  ),

                  const SizedBox(height: 18),

                  const Text(
                    'Unleash your unique style with personalized fashion recommendations, just for you!',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 15,
                      height: 1.6,
                    ),
                  ),

                  const Spacer(),

                  SizedBox(
                    width: double.infinity,
                    height: 58,
                    child: ElevatedButton(
                      onPressed: authProvider.isLoading
                          ? null
                          : () => _handleGoogleSignIn(context),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.white,
                        foregroundColor: AppTheme.primaryColor,
                        disabledBackgroundColor: Colors.white.withOpacity(0.75),
                        disabledForegroundColor:
                            AppTheme.primaryColor.withOpacity(0.65),
                        elevation: 0,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(32),
                        ),
                      ),
                      child: authProvider.isLoading
                          ? const SizedBox(
                              width: 24,
                              height: 24,
                              child: CircularProgressIndicator(
                                strokeWidth: 2.5,
                                color: AppTheme.primaryColor,
                              ),
                            )
                          : const Text(
                              'Sign in with Google',
                              style: TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                    ),
                  ),

                  const SizedBox(height: 18),
                ],
              ),
            );
          },
        ),
      ),
    );
  }
}