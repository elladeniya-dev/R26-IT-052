import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:provider/provider.dart';

import '../../core/responsive.dart';
import '../../core/api_config.dart';
import '../../core/theme.dart';
import '../../providers/auth_provider.dart';
import '../../services/profile_service.dart';
import '../../widgets/google_web_sign_in_button.dart';
import '../shell/main_shell.dart';
import '../onboarding/onboarding_screen.dart';

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {
  final ProfileService _profileService = ProfileService();

  StreamSubscription<GoogleSignInAuthenticationEvent>?
      _googleAuthenticationSubscription;

  bool _webGoogleInitialized = false;
  bool _isCheckingUserProfile = false;

  @override
  void initState() {
    super.initState();

    if (kIsWeb) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        _initializeGoogleWebSignIn();
      });
    }
  }

  Future<void> _initializeGoogleWebSignIn() async {
    if (_webGoogleInitialized) {
      return;
    }

    _webGoogleInitialized = true;

    final authProvider = Provider.of<AuthProvider>(context, listen: false);

    try {
      await authProvider.initializeGoogleSignIn();

      _googleAuthenticationSubscription =
          GoogleSignIn.instance.authenticationEvents.listen(
        (event) async {
          if (event is GoogleSignInAuthenticationEventSignIn) {
            await _handleGoogleWebSignIn(event.user);
          }
        },
        onError: (Object error) {
          if (!mounted) {
            return;
          }

          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('Google Sign-In failed: $error'),
              backgroundColor: AppTheme.errorColor,
            ),
          );
        },
      );
    } catch (error) {
      if (!mounted) {
        return;
      }

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Could not initialize Google Sign-In: $error'),
          backgroundColor: AppTheme.errorColor,
        ),
      );
    }
  }

  Future<void> _handleGoogleSignIn(BuildContext context) async {
    final authProvider = Provider.of<AuthProvider>(context, listen: false);

    final bool success = await authProvider.signInWithGoogle();

    if (!context.mounted) {
      return;
    }

    if (success) {
      await _navigateAfterLogin(context, authProvider);
    } else {
      _showLoginError(context, authProvider);
    }
  }

  Future<void> _handleDevLogin(BuildContext context) async {
    final authProvider = Provider.of<AuthProvider>(context, listen: false);

    final bool success = await authProvider.signInWithDevBypass();

    if (!context.mounted) {
      return;
    }

    if (success) {
      await _navigateAfterLogin(context, authProvider);
    } else {
      _showLoginError(context, authProvider);
    }
  }

  Future<void> _handleGoogleWebSignIn(
    GoogleSignInAccount googleUser,
  ) async {
    final authProvider = Provider.of<AuthProvider>(context, listen: false);

    final bool success = await authProvider.signInWithGoogleWeb(googleUser);

    if (!mounted) {
      return;
    }

    if (success) {
      await _navigateAfterLogin(context, authProvider);
    } else {
      _showLoginError(context, authProvider);
    }
  }

  Future<void> _navigateAfterLogin(
    BuildContext context,
    AuthProvider authProvider,
  ) async {
    if (_isCheckingUserProfile) {
      return;
    }

    setState(() {
      _isCheckingUserProfile = true;
    });

    try {
      final Map<String, dynamic> profileData =
          await _profileService.getProfile();

      if (!context.mounted) {
        return;
      }

      final dynamic onboardingPreferences =
          profileData['onboarding_preferences'];

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            'Welcome ${authProvider.currentUser?.fullName ?? 'back'}!',
          ),
          backgroundColor: AppTheme.darkTextColor,
        ),
      );

      if (onboardingPreferences == null) {
        // New user:
        // No onboarding preferences have been saved yet.
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(
            builder: (context) => const OnboardingScreen(),
          ),
        );
      } else {
        // Returning user:
        // Onboarding already exists, so go directly home.
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(
            builder: (context) => const MainShell(),
          ),
        );
      }
    } catch (error) {
      if (!context.mounted) {
        return;
      }

      setState(() {
        _isCheckingUserProfile = false;
      });

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Could not check your profile: $error'),
          backgroundColor: AppTheme.errorColor,
        ),
      );
    }
  }

  void _showLoginError(
    BuildContext context,
    AuthProvider authProvider,
  ) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          authProvider.errorMessage ?? 'Google Sign-In failed.',
        ),
        backgroundColor: AppTheme.errorColor,
      ),
    );
  }

  Future<void> _showServerConnectionDialog(BuildContext context) async {
    final TextEditingController controller = TextEditingController(
      text: ApiConfig.isUsingOverride
          ? ApiConfig.currentHost.replaceFirst('http://', '')
          : '',
    );

    await showDialog<void>(
      context: context,
      builder: (dialogContext) {
        return AlertDialog(
          title: const Text('Server Connection'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Only needed if USB (adb reverse) isn\'t available. '
                'Enter this laptop\'s LAN IP (from ipconfig). Leave '
                'empty to use the default (127.0.0.1).',
                style: TextStyle(fontSize: 12.5, height: 1.4),
              ),
              const SizedBox(height: 14),
              TextField(
                controller: controller,
                keyboardType: TextInputType.url,
                decoration: const InputDecoration(
                  labelText: 'LAN IP',
                  hintText: '192.168.1.2',
                  border: OutlineInputBorder(),
                ),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(dialogContext),
              child: const Text('Cancel'),
            ),
            TextButton(
              onPressed: () async {
                final String raw = controller.text.trim();
                final String? host =
                    raw.isEmpty ? null : 'http://$raw';

                await ApiConfig.setOverrideHost(host);

                if (dialogContext.mounted) {
                  Navigator.pop(dialogContext);
                }

                if (context.mounted) {
                  setState(() {});

                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text(
                        host == null
                            ? 'Reset to default (127.0.0.1).'
                            : 'Server set to $raw. Restart the app '
                                'for it to take effect everywhere.',
                      ),
                    ),
                  );
                }
              },
              child: const Text('Save'),
            ),
          ],
        );
      },
    );
  }

  @override
  void dispose() {
    _googleAuthenticationSubscription?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Stack(
        children: [
          // Background image section
          Positioned.fill(
            child: Image.network(
              'https://images.unsplash.com/photo-1483985988355-763728e1935b?w=1200',
              fit: BoxFit.cover,
              loadingBuilder: (context, child, loadingProgress) {
                if (loadingProgress == null) return child;

                return Container(
                  color: const Color(0xFF073B5A),
                  child: const Center(
                    child: CircularProgressIndicator(
                      color: Colors.white,
                      strokeWidth: 2.5,
                    ),
                  ),
                );
              },
              errorBuilder: (context, error, stackTrace) {
                return Container(
                  decoration: const BoxDecoration(
                    gradient: LinearGradient(
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                      colors: [
                        Color(0xFF073B5A),
                        Color(0xFF0E6E9E),
                      ],
                    ),
                  ),
                );
              },
            ),
          ),

          // Dark overlay
          Positioned.fill(
            child: Container(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                  colors: [
                    Colors.black.withOpacity(0.20),
                    Colors.black.withOpacity(0.90),
                  ],
                ),
              ),
            ),
          ),

          // Single flowing column: badge, hero copy, sign-in.
          // Everything lives in one Column (no independently-positioned
          // siblings) and scrolls if the viewport is too short, so nothing
          // can ever overlap regardless of window size.
          SafeArea(
            child: ResponsiveCenter(
              child: Consumer<AuthProvider>(
                builder: (context, authProvider, child) {
                  final bool isBusy =
                      authProvider.isLoading || _isCheckingUserProfile;

                  return LayoutBuilder(
                    builder: (context, constraints) {
                      return SingleChildScrollView(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 28,
                          vertical: 24,
                        ),
                        child: ConstrainedBox(
                          constraints: BoxConstraints(
                            minHeight: constraints.maxHeight - 48,
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Row(
                                children: [
                                  Container(
                                    height: 42,
                                    width: 42,
                                    decoration: BoxDecoration(
                                      color: Colors.white.withOpacity(0.18),
                                      borderRadius: BorderRadius.circular(16),
                                      border: Border.all(
                                        color:
                                            Colors.white.withOpacity(0.25),
                                      ),
                                    ),
                                    child: const Icon(
                                      Icons.auto_awesome_rounded,
                                      color: Colors.white,
                                      size: 23,
                                    ),
                                  ),
                                  const SizedBox(width: 10),
                                  Text(
                                    'Smart Fashion Assistant',
                                    style: GoogleFonts.poppins(
                                      fontSize: 13,
                                      fontWeight: FontWeight.w600,
                                      color: Colors.white.withOpacity(0.92),
                                    ),
                                  ),
                                ],
                              ),

                              const SizedBox(height: 36),

                              Container(
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 13,
                                  vertical: 8,
                                ),
                                decoration: BoxDecoration(
                                  color: Colors.white.withOpacity(0.15),
                                  borderRadius: BorderRadius.circular(22),
                                  border: Border.all(
                                    color: Colors.white.withOpacity(0.22),
                                  ),
                                ),
                                child: Text(
                                  'Personalized • Trend-aware • Smart',
                                  style: GoogleFonts.poppins(
                                    fontSize: 12,
                                    fontWeight: FontWeight.w600,
                                    color: Colors.white,
                                  ),
                                ),
                              ),

                              const SizedBox(height: 18),

                              Text(
                                'OutfitIQ',
                                style: GoogleFonts.poppins(
                                  fontSize: 44,
                                  fontWeight: FontWeight.w800,
                                  color: Colors.white,
                                  letterSpacing: -1.2,
                                ),
                              ),

                              const SizedBox(height: 10),

                              Text(
                                'Discover fashion products matched with your enriched style profile, preferences, and latest shopping needs.',
                                style: GoogleFonts.poppins(
                                  fontSize: 15,
                                  height: 1.55,
                                  fontWeight: FontWeight.w500,
                                  color: Colors.white.withOpacity(0.9),
                                ),
                              ),

                              const SizedBox(height: 26),

                              Row(
                                children: [
                                  _buildFeaturePill('Smart Search'),
                                  const SizedBox(width: 8),
                                  _buildFeaturePill('Style Match'),
                                  const SizedBox(width: 8),
                                  _buildFeaturePill('Real Products'),
                                ],
                              ),

                              const SizedBox(height: 34),

                              // Sign-in card (moved from WelcomeScreen).
                              Container(
                                width: double.infinity,
                                padding: const EdgeInsets.all(18),
                                decoration: BoxDecoration(
                                  color: Colors.white,
                                  borderRadius: BorderRadius.circular(28),
                                  boxShadow: [
                                    BoxShadow(
                                      color: Colors.black.withOpacity(0.25),
                                      blurRadius: 28,
                                      offset: const Offset(0, 12),
                                    ),
                                  ],
                                ),
                                child: Column(
                                  children: [
                                    if (kIsWeb)
                                      SizedBox(
                                        width: double.infinity,
                                        child: Center(
                                          child: buildGoogleWebSignInButton(),
                                        ),
                                      )
                                    else
                                      SizedBox(
                                        width: double.infinity,
                                        height: 58,
                                        child: ElevatedButton(
                                          onPressed: isBusy
                                              ? null
                                              : () => _handleGoogleSignIn(
                                                    context,
                                                  ),
                                          style: ElevatedButton.styleFrom(
                                            backgroundColor:
                                                AppTheme.primaryColor,
                                            foregroundColor:
                                                AppTheme.whiteColor,
                                            disabledBackgroundColor:
                                                AppTheme.primaryColor
                                                    .withOpacity(0.65),
                                            disabledForegroundColor:
                                                AppTheme.whiteColor
                                                    .withOpacity(0.85),
                                            elevation: 0,
                                            shape: RoundedRectangleBorder(
                                              borderRadius:
                                                  BorderRadius.circular(32),
                                            ),
                                          ),
                                          child: isBusy
                                              ? const SizedBox(
                                                  width: 24,
                                                  height: 24,
                                                  child:
                                                      CircularProgressIndicator(
                                                    strokeWidth: 2.5,
                                                    color:
                                                        AppTheme.whiteColor,
                                                  ),
                                                )
                                              : const Row(
                                                  mainAxisAlignment:
                                                      MainAxisAlignment
                                                          .center,
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
                                                        fontWeight:
                                                            FontWeight.bold,
                                                      ),
                                                    ),
                                                  ],
                                                ),
                                        ),
                                      ),
                                    if (isBusy && kIsWeb) ...[
                                      const SizedBox(height: 14),
                                      const SizedBox(
                                        width: 22,
                                        height: 22,
                                        child: CircularProgressIndicator(
                                          strokeWidth: 2.5,
                                          color: AppTheme.primaryColor,
                                        ),
                                      ),
                                    ],
                                    if (ApiConfig.devLoginEnabled) ...[
                                      const SizedBox(height: 10),
                                      TextButton.icon(
                                        onPressed: isBusy
                                            ? null
                                            : () => _handleDevLogin(context),
                                        icon: const Icon(
                                          Icons.bug_report_outlined,
                                          size: 18,
                                        ),
                                        label: const Text(
                                          'Dev login (skip Google)',
                                        ),
                                      ),
                                    ],
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

                              const SizedBox(height: 14),

                              Center(
                                child: Text(
                                  'Powered by Enriched User Preferences and Recommendation Engine',
                                  textAlign: TextAlign.center,
                                  style: GoogleFonts.poppins(
                                    fontSize: 11,
                                    height: 1.4,
                                    fontWeight: FontWeight.w500,
                                    color: Colors.white.withOpacity(0.72),
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                      );
                    },
                  );
                },
              ),
            ),
          ),
          Positioned(
            top: 12,
            right: 14,
            child: SafeArea(
              child: Consumer<AuthProvider>(
                builder: (context, authProvider, child) => IconButton(
                  tooltip: 'Server Connection',
                  icon: const Icon(Icons.info_outline_rounded),
                  color: Colors.white,
                  onPressed: authProvider.isLoading || _isCheckingUserProfile
                      ? null
                      : () => _showServerConnectionDialog(context),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFeaturePill(String text) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 9),
        decoration: BoxDecoration(
          color: Colors.white.withOpacity(0.14),
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: Colors.white.withOpacity(0.22),
          ),
        ),
        child: Center(
          child: Text(
            text,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: GoogleFonts.poppins(
              fontSize: 11,
              fontWeight: FontWeight.w700,
              color: Colors.white,
            ),
          ),
        ),
      ),
    );
  }
}
