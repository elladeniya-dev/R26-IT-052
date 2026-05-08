class ProductModel {
  final String itemId;
  final String title;
  final String role;
  final List<String> color;
  final List<String> style;
  final String imageUrl;
  final String productUrl;
  final double price;
  final String brand;
  final String description;

  ProductModel({
    required this.itemId,
    required this.title,
    required this.role,
    required this.color,
    required this.style,
    required this.imageUrl,
    required this.productUrl,
    required this.price,
    required this.brand,
    required this.description,
  });

  factory ProductModel.fromJson(Map<String, dynamic> json) {
    return ProductModel(
      itemId: json['item_id']?.toString() ?? '',
      title: json['title']?.toString() ?? '',
      role: json['role']?.toString() ?? '',
      color: _toStringList(json['color']),
      style: _toStringList(json['style']),
      imageUrl: json['image_url']?.toString() ?? '',
      productUrl: json['product_url']?.toString() ?? '',
      price: _toDouble(json['price']),
      brand: json['brand']?.toString() ?? '',
      description: json['description']?.toString() ?? '',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'item_id': itemId,
      'title': title,
      'role': role,
      'color': color,
      'style': style,
      'image_url': imageUrl,
      'product_url': productUrl,
      'price': price,
      'brand': brand,
      'description': description,
    };
  }

  static List<String> _toStringList(dynamic value) {
    if (value == null) {
      return [];
    }

    if (value is List) {
      return value.map((item) => item.toString()).toList();
    }

    return [value.toString()];
  }

  static double _toDouble(dynamic value) {
    if (value == null) {
      return 0.0;
    }

    if (value is int) {
      return value.toDouble();
    }

    if (value is double) {
      return value;
    }

    return double.tryParse(value.toString()) ?? 0.0;
  }
}