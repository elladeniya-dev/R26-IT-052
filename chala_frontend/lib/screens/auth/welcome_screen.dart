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
          backgroundColor: AppTheme.darkTextColor,
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

  static const String imageUrl =
      'https://images.unsplash.com/photo-1483985988355-763728e1935b?auto=format&fit=crop&w=900&q=80';

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
      child: ClipRRect(
        borderRadius: BorderRadius.circular(34),
        child: Stack(
          fit: StackFit.expand,
          children: [
            Image.network(
              imageUrl,
              fit: BoxFit.cover,
              loadingBuilder: (context, child, loadingProgress) {
                if (loadingProgress == null) {
                  return child;
                }

                return Container(
                  color: AppTheme.softHighlightColor,
                  child: const Center(
                    child: CircularProgressIndicator(
                      color: AppTheme.primaryColor,
                    ),
                  ),
                );
              },
              errorBuilder: (context, error, stackTrace) {
                return Container(
                  color: AppTheme.softHighlightColor,
                  child: const Center(
                    child: Icon(
                      Icons.checkroom_rounded,
                      size: 90,
                      color: AppTheme.primaryColor,
                    ),
                  ),
                );
              },
            ),

            Container(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                  colors: [
                    AppTheme.darkAccentColor.withOpacity(0.05),
                    AppTheme.darkAccentColor.withOpacity(0.35),
                  ],
                ),
              ),
            ),

            Positioned(
              top: 22,
              right: 22,
              child: _MiniFashionBadge(
                icon: Icons.auto_awesome_rounded,
              ),
            ),

            Positioned(
              bottom: 22,
              left: 22,
              child: _MiniFashionBadge(
                icon: Icons.shopping_bag_rounded,
              ),
            ),

            Positioned(
              left: 24,
              right: 24,
              bottom: 24,
              child: Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 16,
                  vertical: 12,
                ),
                decoration: BoxDecoration(
                  color: AppTheme.whiteColor.withOpacity(0.88),
                  borderRadius: BorderRadius.circular(22),
                ),
                child: const Text(
                  'Style inspiration, picked for you',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    color: AppTheme.darkTextColor,
                    fontSize: 14,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ),
          ],
        ),
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