import 'package:flutter_test/flutter_test.dart';
import 'package:outfitiq_app/models/recommendation_product_model.dart';
import 'package:outfitiq_app/screens/trending/trend_matching.dart';
import 'package:outfitiq_app/services/trend_api_service.dart';

RecommendationProduct product(String id, {String title = 'Cloth'}) {
  return RecommendationProduct(
    itemId: id,
    title: title,
    category: 'dress',
    subcategory: 'dress',
    color: const ['white'],
    style: const ['casual'],
    brand: 'Brand',
    source: 'source',
    price: 1000,
    imageUrl: '',
    productUrl: '',
    finalScore: 0.5,
    userMatchScore: 0.5,
    mlSimilarityScore: 0.5,
    productQualityScore: 0.5,
    reasonTags: const [],
  );
}

ProductSegmentMatch match(String segment, String confidence, double contribution) {
  return ProductSegmentMatch(
    segment: segment,
    segmentType: 'color_x_category',
    parts: const [],
    match: 'exact',
    confidence: confidence,
    trendScore: 1,
    contribution: contribution,
  );
}

ProductTrend trendOf(String id, double score, List<ProductSegmentMatch> matches) =>
    ProductTrend(id: id, segmentScore: score, segments: matches);

void main() {
  group('sectionsFromTrends', () {
    test('groups cloths by the confidence of their segment, strongest first', () {
      final sections = sectionsFromTrends(
        [product('a'), product('b'), product('c')],
        {
          'a': trendOf('a', 1.0, [match('white + dress', 'medium', 0.6)]),
          'b': trendOf('b', 2.5, [match('red + dress', 'high', 1.3)]),
          'c': trendOf('c', 1.8, [match('satin + top', 'high', 1.0)]),
        },
      );
      expect(sections.map((s) => s.level), ['high', 'medium']);
      expect(sections[0].products.map((p) => p['itemId']), ['b', 'c']);
      expect(sections[1].products.map((p) => p['itemId']), ['a']);
    });

    test('a cloth the engine did not score is never shown as trending', () {
      final sections = sectionsFromTrends(
        [product('white-top'), product('scored')],
        {'scored': trendOf('scored', 1.2, [match('white + dress', 'high', 1.2)])},
      );
      final ids = sections.expand((s) => s.products).map((p) => p['itemId']);
      expect(ids, ['scored']);
    });

    test('a score without any matching segment does not count', () {
      expect(
        sectionsFromTrends([product('x')], {'x': trendOf('x', 1.0, [])}),
        isEmpty,
      );
      expect(
        sectionsFromTrends([product('x')], {'x': trendOf('x', 0, [match('a + b', 'high', 1)])}),
        isEmpty,
      );
    });

    test('a cloth sits under its most confident segment, not its biggest one', () {
      final sections = sectionsFromTrends(
        [product('p')],
        {
          'p': trendOf('p', 3.0, [
            match('white + linen', 'medium', 2.0),
            match('white + dress', 'high', 0.9),
          ]),
        },
      );
      expect(sections.single.level, 'high');
      final card = sections.single.products.single;
      expect(card['trendingLabel'], 'White + Dress');
      expect(card['trendingConfidence'], 'high');
      expect(card['trendScore'], 3.0);
      expect(card['trendingSegments'], ['White + Linen', 'White + Dress']);
    });

    test('a cloth listed twice appears once', () {
      final sections = sectionsFromTrends(
        [product('dup'), product('dup')],
        {'dup': trendOf('dup', 1.0, [match('white + dress', 'high', 1.0)])},
      );
      expect(sections.single.products, hasLength(1));
    });

    test('empty input gives no sections, and unknown confidence counts as low', () {
      expect(sectionsFromTrends([], {}), isEmpty);
      final sections = sectionsFromTrends(
        [product('q')],
        {'q': trendOf('q', 1.0, [match('a + b', '', 1.0)])},
      );
      expect(sections.single.level, 'low');
    });

    test('cardFor lets the caller shape the card', () {
      final sections = sectionsFromTrends(
        [product('k')],
        {'k': trendOf('k', 1.0, [match('a + b', 'high', 1.0)])},
        cardFor: (p) => {'itemId': p.itemId, 'custom': true},
      );
      expect(sections.single.products.single['custom'], isTrue);
    });
  });

  group('titleCaseSegment', () {
    test('capitalises each word and keeps the plus sign', () {
      expect(titleCaseSegment('off white + top'), 'Off White + Top');
      expect(titleCaseSegment(''), '');
    });
  });

  group('trend responses', () {
    test('a segment parses from the API shape', () {
      final s = TrendSegment.fromJson({
        'segment_type': 'color_x_category',
        'segment': 'white + dress',
        'parts': [
          {'attr_type': 'color', 'attr_value': 'white'},
          {'attr_type': 'category', 'attr_value': 'dress'},
        ],
        'score': 1.37,
        'confidence': 'high',
        'stores_carrying': 5,
      });
      expect(s.segment, 'white + dress');
      expect(s.parts.map((p) => p.attributeType), ['color', 'category']);
      expect(s.score, 1.37);
      expect(s.storesCarrying, 5);
    });

    test('a product trend ignores the old single-attribute fields', () {
      final t = ProductTrend.fromJson({
        'id': 'p1',
        'trend_score': 4.0,
        'matches': [],
        'segment_score': 0,
        'segments': [],
      });
      expect(t.isTrending, isFalse);
    });

    test('a product trend reads its segment matches', () {
      final t = ProductTrend.fromJson({
        'id': 'p1',
        'segment_score': 2.1,
        'segments': [
          {
            'segment_type': 'color_x_category',
            'segment': 'red + dress',
            'parts': [],
            'match': 'family',
            'trend_score': 1.4,
            'confidence': 'high',
            'contribution': 0.7,
          },
        ],
      });
      expect(t.isTrending, isTrue);
      expect(t.segments.single.match, 'family');
      expect(t.segments.single.contribution, 0.7);
    });

    test('the scoring payload carries only what the engine needs', () {
      expect(trendScoringPayload(product('z', title: 'Maxi Dress')), {
        'id': 'z',
        'title': 'Maxi Dress',
        'category': 'dress',
        'subcategory': 'dress',
        'colors': ['white'],
        'tags': ['casual'],
      });
    });
  });
}
