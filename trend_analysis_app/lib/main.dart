import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import 'screens/trend_dashboard_screen.dart';

const Color _appPrimary = Color(0xFF0B5D85);
const Color _appSecondary = Color(0xFF0E6E9E);
const Color _appAccent = Color(0xFF073B5A);
const Color _appBackground = Color(0xFFF6F7F9);
const Color _appSurface = Color(0xFFFFFFFF);
const Color _appTextPrimary = Color(0xFF111827);
const Color _appTextSecondary = Color(0xFF6B7280);

void main() {
  runApp(const TrendAnalysisApp());
}

class TrendAnalysisApp extends StatelessWidget {
  const TrendAnalysisApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Trend Analysis',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        scaffoldBackgroundColor: _appBackground,
        fontFamily: GoogleFonts.poppins().fontFamily,
        colorScheme: ColorScheme.fromSeed(
          seedColor: _appPrimary,
          brightness: Brightness.light,
        ).copyWith(
          primary: _appPrimary,
          secondary: _appSecondary,
          tertiary: _appAccent,
          surface: _appSurface,
          error: const Color(0xFFEF4444),
          onPrimary: Colors.white,
          onSecondary: Colors.white,
          onSurface: _appTextPrimary,
        ),
        textTheme: GoogleFonts.poppinsTextTheme().copyWith(
          bodyLarge: GoogleFonts.poppins(color: _appTextPrimary),
          bodyMedium: GoogleFonts.poppins(color: _appTextSecondary),
          bodySmall: GoogleFonts.poppins(color: _appTextSecondary),
          titleLarge: GoogleFonts.poppins(
            color: _appTextPrimary,
            fontWeight: FontWeight.w800,
          ),
          titleMedium: GoogleFonts.poppins(
            color: _appTextPrimary,
            fontWeight: FontWeight.w700,
          ),
          titleSmall: GoogleFonts.poppins(
            color: _appTextSecondary,
            fontWeight: FontWeight.w600,
          ),
        ),
        appBarTheme: const AppBarTheme(
          backgroundColor: _appBackground,
          foregroundColor: _appTextPrimary,
          elevation: 0,
          centerTitle: false,
          surfaceTintColor: Colors.transparent,
        ),
        snackBarTheme: const SnackBarThemeData(
          backgroundColor: _appAccent,
          contentTextStyle: TextStyle(color: Colors.white),
        ),
        cardTheme: CardThemeData(
          color: _appSurface,
          surfaceTintColor: _appSurface,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(24),
          ),
        ),
        dividerColor: const Color(0xFFE5E7EB),
      ),
      home: const TrendDashboardScreen(),
    );
  }
}