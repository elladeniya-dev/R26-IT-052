class TrendingProduct {
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
  final double trendScore;
  final String trendReason;

  TrendingProduct({
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
    required this.trendScore,
    required this.trendReason,
  });

  factory TrendingProduct.fromJson(Map<String, dynamic> json) {
    return TrendingProduct(
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
      trendScore: _toDouble(json['trend_score']),
      trendReason: json['trend_reason']?.toString() ?? '',
    );
  }

  static List<String> _toStringList(dynamic value) {
    if (value == null) return [];
    if (value is List) return value.map((item) => item.toString()).toList();
    if (value is String) return value.trim().isEmpty ? [] : [value];
    return [value.toString()];
  }

  static double _toDouble(dynamic value) {
    if (value == null) return 0.0;
    if (value is int) return value.toDouble();
    if (value is double) return value;
    if (value is String) return double.tryParse(value) ?? 0.0;
    return 0.0;
  }
}
