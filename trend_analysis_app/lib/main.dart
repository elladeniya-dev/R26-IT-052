import 'package:flutter/material.dart';

import 'screens/trend_dashboard_screen.dart';

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
        fontFamily: 'Roboto',
        scaffoldBackgroundColor: const Color(0xFFF7F8FA),
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF00796B),
        ),
        useMaterial3: true,
      ),
      home: const TrendDashboardScreen(),
    );
  }
}