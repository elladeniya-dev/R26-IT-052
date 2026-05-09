import 'package:flutter/material.dart';

import 'core/theme.dart';
import 'screens/auth/welcome_screen.dart';

class SmartFashionApp extends StatelessWidget {
  const SmartFashionApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'OutfitIQ',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      home: const WelcomeScreen(),
    );
  }
}