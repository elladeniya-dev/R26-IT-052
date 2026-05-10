import 'package:flutter/material.dart';

class AppTheme {
  // Main brand colors
  static const Color primaryColor = Color(0xFF0B5D85); // Deep Ocean Blue
  static const Color secondaryColor = Color(0xFF0E6E9E); // Fashion Teal Blue
  static const Color darkAccentColor = Color(0xFF073B5A); // Luxury Navy

  // Background colors
  static const Color backgroundColor = Color(0xFFF6F7F9); // Soft Off White
  static const Color cardBackgroundColor = Color(0xFFFFFFFF); // Pure White
  static const Color softHighlightColor = Color(0xFFE8F3F8); // Light Blue Tint

  // Text colors
  static const Color darkTextColor = Color(0xFF111827); // Charcoal Black
  static const Color lightTextColor = Color(0xFF6B7280); // Cool Gray
  static const Color inactiveColor = Color(0xFF9CA3AF); // Muted Gray

  // Status colors
  static const Color successColor = Color(0xFF22C55E); // Fresh Green
  static const Color warningColor = Color(0xFFF59E0B); // Warm Amber
  static const Color errorColor = Color(0xFFEF4444); // Soft Red

  static const Color whiteColor = Colors.white;

  static ThemeData get lightTheme {
    return ThemeData(
      useMaterial3: true,
      scaffoldBackgroundColor: backgroundColor,
      fontFamily: 'Poppins',
      colorScheme: ColorScheme.fromSeed(
        seedColor: primaryColor,
        primary: primaryColor,
        secondary: secondaryColor,
        surface: cardBackgroundColor,
        error: errorColor,
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: backgroundColor,
        foregroundColor: darkTextColor,
        elevation: 0,
        centerTitle: false,
      ),
      textTheme: const TextTheme(
        headlineLarge: TextStyle(
          fontSize: 30,
          fontWeight: FontWeight.bold,
          color: darkTextColor,
        ),
        headlineMedium: TextStyle(
          fontSize: 24,
          fontWeight: FontWeight.bold,
          color: darkTextColor,
        ),
        titleLarge: TextStyle(
          fontSize: 20,
          fontWeight: FontWeight.bold,
          color: darkTextColor,
        ),
        titleMedium: TextStyle(
          fontSize: 16,
          fontWeight: FontWeight.w600,
          color: darkTextColor,
        ),
        bodyLarge: TextStyle(
          fontSize: 16,
          color: darkTextColor,
        ),
        bodyMedium: TextStyle(
          fontSize: 14,
          color: lightTextColor,
        ),
        bodySmall: TextStyle(
          fontSize: 12,
          color: lightTextColor,
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: primaryColor,
          foregroundColor: whiteColor,
          minimumSize: const Size(double.infinity, 54),
          elevation: 0,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(30),
          ),
          textStyle: const TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: primaryColor,
          side: const BorderSide(
            color: primaryColor,
            width: 1,
          ),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(24),
          ),
        ),
      ),
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          foregroundColor: primaryColor,
          textStyle: const TextStyle(
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
      cardTheme: CardThemeData(
        color: cardBackgroundColor,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(20),
        ),
      ),
      iconTheme: const IconThemeData(
        color: primaryColor,
      ),
      progressIndicatorTheme: const ProgressIndicatorThemeData(
        color: primaryColor,
      ),
    );
  }
}