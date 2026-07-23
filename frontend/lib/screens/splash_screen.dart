import 'dart:async';
import 'dart:math';

import 'package:flutter/material.dart';

import 'product_list_screen.dart';

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen>
    with TickerProviderStateMixin {
  // -- Logo entrance
  late final AnimationController _logoController;
  late final Animation<double> _logoFade;
  late final Animation<double> _logoScale;

  // -- Tagline entrance
  late final AnimationController _taglineController;
  late final Animation<double> _taglineFade;
  late final Animation<Offset> _taglineSlide;

  // -- 3-dot bounce loader
  late final AnimationController _dotsController;

  // -- Ambient orb pulse
  late final AnimationController _orbController;

  @override
  void initState() {
    super.initState();

    _logoController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 900),
    );
    _logoFade = CurvedAnimation(parent: _logoController, curve: Curves.easeOut);
    _logoScale = Tween<double>(begin: 0.7, end: 1.0).animate(
      CurvedAnimation(parent: _logoController, curve: Curves.easeOutBack),
    );

    _taglineController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 700),
    );
    _taglineFade = CurvedAnimation(
      parent: _taglineController,
      curve: Curves.easeOut,
    );
    _taglineSlide =
        Tween<Offset>(begin: const Offset(0, 0.35), end: Offset.zero).animate(
          CurvedAnimation(parent: _taglineController, curve: Curves.easeOut),
        );

    _dotsController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 900),
    )..repeat();

    _orbController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 3000),
    )..repeat(reverse: true);

    _logoController.forward().then((_) {
      Future.delayed(const Duration(milliseconds: 150), () {
        if (mounted) _taglineController.forward();
      });
    });

    Timer(const Duration(milliseconds: 3200), () {
      if (mounted) {
        Navigator.of(context).pushReplacement(
          PageRouteBuilder(
            transitionDuration: const Duration(milliseconds: 600),
            pageBuilder: (_, _, _) => const ProductListScreen(),
            transitionsBuilder: (_, animation, _, child) =>
                FadeTransition(opacity: animation, child: child),
          ),
        );
      }
    });
  }

  @override
  void dispose() {
    _logoController.dispose();
    _taglineController.dispose();
    _dotsController.dispose();
    _orbController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final screenWidth = MediaQuery.sizeOf(context).width;
    final isCompact = screenWidth <= 360;

    return Scaffold(
      body: AnimatedBuilder(
        animation: _orbController,
        builder: (context, child) {
          final orb = _orbController.value;
          return Container(
            decoration: BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: const [
                  Color(0xFF073B5A),
                  Color(0xFF0B5D85),
                  Color(0xFF0E6E9E),
                ],
                stops: [0.0, 0.5 + orb * 0.15, 1.0],
              ),
            ),
            child: child,
          );
        },
        child: Stack(
          children: [
            _AmbientOrb(controller: _orbController),
            SafeArea(
              child: Padding(
                padding: EdgeInsets.symmetric(horizontal: isCompact ? 28 : 36),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.center,
                  children: [
                    const Spacer(flex: 3),

                    // Glass card
                    FadeTransition(
                      opacity: _logoFade,
                      child: ScaleTransition(
                        scale: _logoScale,
                        child: _GlassLogoCard(isCompact: isCompact),
                      ),
                    ),

                    SizedBox(height: isCompact ? 28 : 32),

                    // App name
                    FadeTransition(
                      opacity: _logoFade,
                      child: Text(
                        'OutfitIQ',
                        textAlign: TextAlign.center,
                        maxLines: 1,
                        style: TextStyle(
                          fontFamily: 'Roboto',
                          fontSize: isCompact ? 40 : 46,
                          fontWeight: FontWeight.w900,
                          color: Colors.white,
                          letterSpacing: 0,
                          height: 1,
                        ),
                      ),
                    ),

                    SizedBox(height: isCompact ? 14 : 16),

                    // Tagline
                    SlideTransition(
                      position: _taglineSlide,
                      child: FadeTransition(
                        opacity: _taglineFade,
                        child: FittedBox(
                          fit: BoxFit.scaleDown,
                          child: Text(
                            'FASHION & STYLE',
                            textAlign: TextAlign.center,
                            maxLines: 1,
                            style: TextStyle(
                              fontFamily: 'Roboto',
                              fontSize: isCompact ? 12 : 13,
                              fontWeight: FontWeight.w700,
                              color: const Color(0xFFC4E1EF),
                              letterSpacing: isCompact ? 3 : 4,
                            ),
                          ),
                        ),
                      ),
                    ),

                    const Spacer(flex: 3),

                    // 3-dot loader
                    FadeTransition(
                      opacity: _logoFade,
                      child: _ThreeDotsLoader(controller: _dotsController),
                    ),

                    const SizedBox(height: 48),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _GlassLogoCard extends StatelessWidget {
  const _GlassLogoCard({required this.isCompact});

  final bool isCompact;

  @override
  Widget build(BuildContext context) {
    final cardSize = isCompact ? 108.0 : 118.0;
    final circleSize = isCompact ? 60.0 : 66.0;

    return Container(
      width: cardSize,
      height: cardSize,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(isCompact ? 30 : 34),
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            Colors.white.withValues(alpha: 0.20),
            Colors.white.withValues(alpha: 0.06),
          ],
        ),
        border: Border.all(
          color: Colors.white.withValues(alpha: 0.30),
          width: 1.5,
        ),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF0B5D85).withValues(alpha: 0.45),
            blurRadius: 40,
            spreadRadius: 4,
          ),
        ],
      ),
      child: Center(
        child: Container(
          width: circleSize,
          height: circleSize,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            gradient: const LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [Color(0xFF5AB4D6), Color(0xFF0B5D85)],
            ),
            boxShadow: [
              BoxShadow(
                color: const Color(0xFF0B5D85).withValues(alpha: 0.6),
                blurRadius: 18,
                spreadRadius: 2,
              ),
            ],
          ),
          child: const Icon(
            Icons.checkroom_rounded,
            color: Colors.white,
            size: 32,
          ),
        ),
      ),
    );
  }
}

class _ThreeDotsLoader extends StatelessWidget {
  const _ThreeDotsLoader({required this.controller});
  final AnimationController controller;

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: controller,
      builder: (context, _) {
        return Row(
          mainAxisSize: MainAxisSize.min,
          children: List.generate(3, (i) {
            final phase = (controller.value - i * 0.22).clamp(0.0, 1.0);
            final bounce = sin(phase * pi).abs();
            return Padding(
              padding: const EdgeInsets.symmetric(horizontal: 5),
              child: Transform.translate(
                offset: Offset(0, -12 * bounce),
                child: Container(
                  width: 9,
                  height: 9,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: Color.lerp(
                      const Color(0xFF5AB4D6),
                      Colors.white,
                      bounce,
                    ),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.white.withValues(alpha: 0.4 * bounce),
                        blurRadius: 8,
                      ),
                    ],
                  ),
                ),
              ),
            );
          }),
        );
      },
    );
  }
}

class _AmbientOrb extends StatelessWidget {
  const _AmbientOrb({required this.controller});
  final AnimationController controller;

  @override
  Widget build(BuildContext context) {
    final size = MediaQuery.of(context).size;
    return AnimatedBuilder(
      animation: controller,
      builder: (context, _) {
        final t = controller.value;
        return Stack(
          children: [
            Positioned(
              top: -60 + t * 20,
              right: -60 + t * 10,
              child: _orb(260, const Color(0xFF0E6E9E), 0.18 + t * 0.06),
            ),
            Positioned(
              bottom: -80 - t * 20,
              left: -80 + t * 15,
              child: _orb(300, const Color(0xFF073B5A), 0.22 + t * 0.05),
            ),
            Positioned(
              top: size.height * 0.38 - t * 8,
              left: size.width * 0.5 - 120,
              child: _orb(240, const Color(0xFF5AB4D6), 0.07 + t * 0.04),
            ),
          ],
        );
      },
    );
  }

  Widget _orb(double size, Color color, double opacity) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: color.withValues(alpha: opacity),
      ),
    );
  }
}
