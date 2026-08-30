class RecommendationProduct {
  final String itemId;
  final String title;
  final String category;
  final List<String> color;
  final List<String> style;
  final String brand;
  final String source;
  final double price;
  final String imageUrl;
  final String productUrl;
  final double finalScore;
  final double userMatchScore;
  final double mlSimilarityScore;
  final double productQualityScore;
  final List<String> reasonTags;

  RecommendationProduct({
    required this.itemId,
    required this.title,
    required this.category,
    required this.color,
    required this.style,
    required this.brand,
    required this.source,
    required this.price,
    required this.imageUrl,
    required this.productUrl,
    required this.finalScore,
    required this.userMatchScore,
    required this.mlSimilarityScore,
    required this.productQualityScore,
    required this.reasonTags,
  });

  factory RecommendationProduct.fromJson(Map<String, dynamic> json) {
    return RecommendationProduct(
      itemId: json['item_id']?.toString() ?? '',
      title: json['title']?.toString() ?? 'Fashion Product',
      category: json['category']?.toString() ?? '',
      color: _toStringList(json['color']),
      style: _toStringList(json['style']),
      brand: json['brand']?.toString() ?? '',
      source: json['source']?.toString() ?? '',
      price: _toDouble(json['price']),
      imageUrl: json['image_url']?.toString() ?? '',
      productUrl: json['product_url']?.toString() ?? '',
      finalScore: _toDouble(json['final_score']),
      userMatchScore: _toDouble(json['user_match_score']),
      mlSimilarityScore: _toDouble(json['ml_similarity_score']),
      productQualityScore: _toDouble(json['product_quality_score']),
      reasonTags: _toStringList(json['reason_tags']),
    );
  }

  Map<String, dynamic> toProductDetailMap() {
    return {
      'itemId': itemId,
      'title': title,
      'brand': brand,
      'source': source,
      'category': category,
      'price': 'LKR ${price.toStringAsFixed(0)}',
      'priceValue': price.round(),
      'match': '${(finalScore * 100).round()}%',
      'color': color.isNotEmpty ? color.join(', ') : 'Not specified',
      'style': style.isNotEmpty ? style.join(', ') : 'Not specified',
      'image': imageUrl,
      'productUrl': productUrl,
      'finalScore': finalScore,
      'userMatchScore': userMatchScore,
      'mlSimilarityScore': mlSimilarityScore,
      'productQualityScore': productQualityScore,
      'tags': reasonTags,
    };
  }

  static List<String> _toStringList(dynamic value) {
    if (value == null) return [];

    if (value is List) {
      return value.map((item) => item.toString()).toList();
    }

    if (value is String) {
      if (value.trim().isEmpty) return [];

      return [value];
    }

    return [value.toString()];
  }

  static double _toDouble(dynamic value) {
    if (value == null) return 0.0;

    if (value is int) return value.toDouble();

    if (value is double) return value;

    if (value is String) {
      return double.tryParse(value) ?? 0.0;
    }

    return 0.0;
  }
}