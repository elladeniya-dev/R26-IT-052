import 'package:flutter/material.dart';

import 'screens/product_list_screen.dart';

void main() {
  runApp(const SenuOutfitApp());
}

class SenuOutfitApp extends StatelessWidget {
  const SenuOutfitApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Senu Outfit Compatibility',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        scaffoldBackgroundColor: const Color(0xFFF8F8F8),
        fontFamily: 'Roboto',
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF111827),
        ),
        appBarTheme: const AppBarTheme(
          centerTitle: false,
          backgroundColor: Color(0xFFF8F8F8),
          foregroundColor: Color(0xFF111827),
          elevation: 0,
        ),
      ),
      home: const ProductListScreen(),
    );
  }
}