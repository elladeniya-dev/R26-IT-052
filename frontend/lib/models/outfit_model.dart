import 'product_model.dart';

class OutfitModel {
  final String outfitId;
  final String generationBatchId;
  final List<ProductModel> items;
  final double compatibilityScore;
  final List<String> reasonTags;
  final ScoreBreakdown scoreBreakdown;
  final AppliedFilters appliedFilters;

  OutfitModel({
    required this.outfitId,
    required this.generationBatchId,
    required this.items,
    required this.compatibilityScore,
    required this.reasonTags,
    required this.scoreBreakdown,
    required this.appliedFilters,
  });

  factory OutfitModel.fromJson(Map<String, dynamic> json) {
    return OutfitModel(
      outfitId: json['outfit_id']?.toString() ?? '',
      generationBatchId: json['generation_batch_id']?.toString() ?? '',
      items: _toProductList(json['items']),
      compatibilityScore: _toDouble(json['compatibility_score']),
      reasonTags: _toStringList(json['reason_tags']),
      scoreBreakdown: ScoreBreakdown.fromJson(
        json['score_breakdown'] is Map<String, dynamic>
            ? json['score_breakdown']
            : {},
      ),
      appliedFilters: AppliedFilters.fromJson(
        json['applied_filters'] is Map<String, dynamic>
            ? json['applied_filters']
            : {},
      ),
    );
  }

  static List<ProductModel> _toProductList(dynamic value) {
    if (value == null || value is! List) {
      return [];
    }

    return value
        .whereType<Map<String, dynamic>>()
        .map((item) => ProductModel.fromJson(item))
        .toList();
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

class ScoreBreakdown {
  final double styleMatchScore;
  final double colorMatchScore;
  final double categoryMatchScore;
  final double occasionMatchScore;

  ScoreBreakdown({
    required this.styleMatchScore,
    required this.colorMatchScore,
    required this.categoryMatchScore,
    required this.occasionMatchScore,
  });

  factory ScoreBreakdown.fromJson(Map<String, dynamic> json) {
    return ScoreBreakdown(
      styleMatchScore: _toDouble(json['style_match_score']),
      colorMatchScore: _toDouble(json['color_match_score']),
      categoryMatchScore: _toDouble(json['category_match_score']),
      occasionMatchScore: _toDouble(json['occasion_match_score']),
    );
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

class AppliedFilters {
  final double minPrice;
  final double maxPrice;
  final List<String> preferredColors;
  final List<String> excludedCategories;
  final int maxItemsPerCategory;

  AppliedFilters({
    required this.minPrice,
    required this.maxPrice,
    required this.preferredColors,
    required this.excludedCategories,
    required this.maxItemsPerCategory,
  });

  factory AppliedFilters.fromJson(Map<String, dynamic> json) {
    return AppliedFilters(
      minPrice: _toDouble(json['min_price']),
      maxPrice: _toDouble(json['max_price']),
      preferredColors: _toStringList(json['preferred_colors']),
      excludedCategories: _toStringList(json['excluded_categories']),
      maxItemsPerCategory: _toInt(json['max_items_per_category']),
    );
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

  static int _toInt(dynamic value) {
    if (value == null) {
      return 0;
    }

    if (value is int) {
      return value;
    }

    return int.tryParse(value.toString()) ?? 0;
  }
}

class OutfitGenerateResponse {
  final String status;
  final String message;
  final String userId;
  final String selectedItemId;
  final List<OutfitModel> outfits;
  final String generatedAt;

  OutfitGenerateResponse({
    required this.status,
    required this.message,
    required this.userId,
    required this.selectedItemId,
    required this.outfits,
    required this.generatedAt,
  });

  factory OutfitGenerateResponse.fromJson(Map<String, dynamic> json) {
    return OutfitGenerateResponse(
      status: json['status']?.toString() ?? '',
      message: json['message']?.toString() ?? '',
      userId: json['user_id']?.toString() ?? '',
      selectedItemId: json['selected_item_id']?.toString() ?? '',
      outfits: _toOutfitList(json['outfits']),
      generatedAt: json['generated_at']?.toString() ?? '',
    );
  }

  static List<OutfitModel> _toOutfitList(dynamic value) {
    if (value == null || value is! List) {
      return [];
    }

    return value
        .whereType<Map<String, dynamic>>()
        .map((item) => OutfitModel.fromJson(item))
        .toList();
  }
}