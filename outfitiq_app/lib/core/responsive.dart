import 'package:flutter/material.dart';

/// Caps content width and centers it on large viewports (web/desktop)
/// so mobile-first layouts stop stretching edge-to-edge, while staying
/// full-width on phone-sized viewports.
class ResponsiveCenter extends StatelessWidget {
  final Widget child;
  final double maxWidth;

  const ResponsiveCenter({
    super.key,
    required this.child,
    this.maxWidth = 480,
  });

  @override
  Widget build(BuildContext context) {
    return Center(
      child: ConstrainedBox(
        constraints: BoxConstraints(maxWidth: maxWidth),
        child: child,
      ),
    );
  }
}
