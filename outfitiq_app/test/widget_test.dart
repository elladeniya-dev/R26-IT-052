// // This is a basic Flutter widget test.
// //
// // To perform an interaction with a widget in your test, use the WidgetTester
// // utility in the flutter_test package. For example, you can send tap and scroll
// // gestures. You can also use WidgetTester to find child widgets in the widget
// // tree, read text, and verify that the values of widget properties are correct.

// import 'package:flutter/material.dart';
// import 'package:flutter_test/flutter_test.dart';

// import 'package:chala_frontend/main.dart';

// void main() {
//   testWidgets('Counter increments smoke test', (WidgetTester tester) async {
//     // Build our app and trigger a frame.
//     await tester.pumpWidget(const MyApp());

//     // Verify that our counter starts at 0.
//     expect(find.text('0'), findsOneWidget);
//     expect(find.text('1'), findsNothing);

//     // Tap the '+' icon and trigger a frame.
//     await tester.tap(find.byIcon(Icons.add));
//     await tester.pump();

//     // Verify that our counter has incremented.
//     expect(find.text('0'), findsNothing);
//     expect(find.text('1'), findsOneWidget);
//   });
// }

import 'package:flutter_test/flutter_test.dart';
import 'package:outfitiq_app/core/fashion_attribute_formatter.dart';
import 'package:outfitiq_app/models/recommendation_product_model.dart';

void main() {
  test('recommendation response parsing and display formatting', () {
    final product = RecommendationProduct.fromJson({
      'item_id': 'test-1',
      'title': 'Formal Dress',
      'category': 'dresses',
      'color': ['blue'],
      'style': ['smart_casual'],
      'brand': 'bellini',
      'source': 'bellini',
      'price': 5000,
      'image_url': 'https://shop.test/image.jpg',
      'product_url': 'https://shop.test/product',
      'final_score': 0.8,
      'user_match_score': 0.9,
      'ml_similarity_score': 0.7,
      'product_quality_score': 1.0,
      'reason_tags': ['available now'],
    });

    expect(product.itemId, 'test-1');
    expect(product.style, ['smart_casual']);
    expect(product.toProductDetailMap()['style'], 'Smart Casual');
    expect(formatFashionAttribute('blue'), 'Blue');
    expect(formatFashionAttribute('top'), 'Tops');
  });
}
