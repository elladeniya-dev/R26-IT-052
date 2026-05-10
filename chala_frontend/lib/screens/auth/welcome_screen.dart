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
          backgroundColor: AppTheme.successColor,
        ),
      );

      Navigator.pushReplacement(
        context,
        MaterialPageRoute(
          builder: (context) => const OnboardingScreen(),
        ),
      );
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            authProvider.errorMessage ?? 'Google Sign-In failed.',
          ),
          backgroundColor: AppTheme.errorColor,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundColor,
      body: SafeArea(
        child: Consumer<AuthProvider>(
          builder: (context, authProvider, child) {
            return Stack(
              children: [
                const _WelcomeBackground(),

                Padding(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 26,
                    vertical: 24,
                  ),
                  child: Column(
                    children: [
                      const SizedBox(height: 10),

                      const _AppLogo(),

                      const Spacer(),

                      const _FashionIconCard(),

                      const SizedBox(height: 34),

                      const Text(
                        'Discover Your Ultimate\nFashion Destination!',
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          color: AppTheme.darkTextColor,
                          fontSize: 29,
                          height: 1.25,
                          fontWeight: FontWeight.bold,
                        ),
                      ),

                      const SizedBox(height: 16),

                      const Text(
                        'Unleash your unique style with personalized fashion recommendations, just for you!',
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          color: AppTheme.lightTextColor,
                          fontSize: 15,
                          height: 1.6,
                          fontWeight: FontWeight.w500,
                        ),
                      ),

                      const Spacer(),

                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.all(18),
                        decoration: BoxDecoration(
                          color: AppTheme.cardBackgroundColor,
                          borderRadius: BorderRadius.circular(28),
                          boxShadow: [
                            BoxShadow(
                              color: AppTheme.primaryColor.withOpacity(0.10),
                              blurRadius: 28,
                              offset: const Offset(0, 12),
                            ),
                          ],
                        ),
                        child: Column(
                          children: [
                            SizedBox(
                              width: double.infinity,
                              height: 58,
                              child: ElevatedButton(
                                onPressed: authProvider.isLoading
                                    ? null
                                    : () => _handleGoogleSignIn(context),
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: AppTheme.primaryColor,
                                  foregroundColor: AppTheme.whiteColor,
                                  disabledBackgroundColor:
                                      AppTheme.primaryColor.withOpacity(0.65),
                                  disabledForegroundColor:
                                      AppTheme.whiteColor.withOpacity(0.85),
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
                                          color: AppTheme.whiteColor,
                                        ),
                                      )
                                    : const Row(
                                        mainAxisAlignment:
                                            MainAxisAlignment.center,
                                        children: [
                                          Icon(
                                            Icons.login_rounded,
                                            size: 20,
                                          ),
                                          SizedBox(width: 10),
                                          Text(
                                            'Sign in with Google',
                                            style: TextStyle(
                                              fontSize: 16,
                                              fontWeight: FontWeight.bold,
                                            ),
                                          ),
                                        ],
                                      ),
                              ),
                            ),

                            const SizedBox(height: 14),

                            const Text(
                              'Continue to your personal fashion assistant',
                              textAlign: TextAlign.center,
                              style: TextStyle(
                                color: AppTheme.lightTextColor,
                                fontSize: 12,
                                fontWeight: FontWeight.w500,
                              ),
                            ),
                          ],
                        ),
                      ),

                      const SizedBox(height: 18),
                    ],
                  ),
                ),
              ],
            );
          },
        ),
      ),
    );
  }
}

class _WelcomeBackground extends StatelessWidget {
  const _WelcomeBackground();

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        Container(
          decoration: const BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter,
              colors: [
                AppTheme.softHighlightColor,
                AppTheme.backgroundColor,
                AppTheme.backgroundColor,
              ],
            ),
          ),
        ),

        Positioned(
          top: -80,
          right: -80,
          child: _BackgroundCircle(
            size: 220,
            color: AppTheme.secondaryColor,
            opacity: 0.14,
          ),
        ),

        Positioned(
          top: 150,
          left: -100,
          child: _BackgroundCircle(
            size: 210,
            color: AppTheme.primaryColor,
            opacity: 0.10,
          ),
        ),

        Positioned(
          bottom: 120,
          right: -70,
          child: _BackgroundCircle(
            size: 180,
            color: AppTheme.darkAccentColor,
            opacity: 0.09,
          ),
        ),
      ],
    );
  }
}

class _BackgroundCircle extends StatelessWidget {
  final double size;
  final Color color;
  final double opacity;

  const _BackgroundCircle({
    required this.size,
    required this.color,
    required this.opacity,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        color: color.withOpacity(opacity),
        shape: BoxShape.circle,
      ),
    );
  }
}

class _AppLogo extends StatelessWidget {
  const _AppLogo();

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Container(
          width: 34,
          height: 34,
          decoration: BoxDecoration(
            color: AppTheme.primaryColor,
            borderRadius: BorderRadius.circular(10),
          ),
          child: const Icon(
            Icons.diamond_outlined,
            size: 21,
            color: AppTheme.whiteColor,
          ),
        ),
        const SizedBox(width: 10),
        const Text(
          'OutfitIQ',
          style: TextStyle(
            color: AppTheme.darkTextColor,
            fontSize: 23,
            fontWeight: FontWeight.bold,
          ),
        ),
      ],
    );
  }
}

class _FashionIconCard extends StatelessWidget {
  const _FashionIconCard();

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      height: 285,
      decoration: BoxDecoration(
        color: AppTheme.cardBackgroundColor,
        borderRadius: BorderRadius.circular(34),
        boxShadow: [
          BoxShadow(
            color: AppTheme.primaryColor.withOpacity(0.12),
            blurRadius: 30,
            offset: const Offset(0, 16),
          ),
        ],
      ),
      child: Stack(
        alignment: Alignment.center,
        children: [
          Container(
            width: 190,
            height: 190,
            decoration: BoxDecoration(
              color: AppTheme.softHighlightColor,
              borderRadius: BorderRadius.circular(100),
            ),
          ),

          Container(
            width: 132,
            height: 132,
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [
                  AppTheme.secondaryColor,
                  AppTheme.primaryColor,
                  AppTheme.darkAccentColor,
                ],
              ),
              borderRadius: BorderRadius.circular(42),
            ),
            child: const Icon(
              Icons.checkroom_rounded,
              size: 78,
              color: AppTheme.whiteColor,
            ),
          ),

          Positioned(
            top: 36,
            right: 44,
            child: _MiniFashionBadge(
              icon: Icons.auto_awesome_rounded,
            ),
          ),

          Positioned(
            bottom: 40,
            left: 42,
            child: _MiniFashionBadge(
              icon: Icons.favorite_rounded,
            ),
          ),
        ],
      ),
    );
  }
}

class _MiniFashionBadge extends StatelessWidget {
  final IconData icon;

  const _MiniFashionBadge({
    required this.icon,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 46,
      height: 46,
      decoration: BoxDecoration(
        color: AppTheme.whiteColor,
        borderRadius: BorderRadius.circular(18),
        boxShadow: [
          BoxShadow(
            color: AppTheme.primaryColor.withOpacity(0.12),
            blurRadius: 18,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: Icon(
        icon,
        color: AppTheme.primaryColor,
        size: 22,
      ),
    );
  }
}