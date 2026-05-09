import 'product_model.dart';

class SavedOutfitModel {
  final String outfitId;
  final String generationBatchId;
  final String userId;
  final String selectedItemId;
  final double compatibilityScore;
  final List<String> reasonTags;
  final bool isSaved;
  final String generatedAt;
  final List<ProductModel> items;

  SavedOutfitModel({
    required this.outfitId,
    required this.generationBatchId,
    required this.userId,
    required this.selectedItemId,
    required this.compatibilityScore,
    required this.reasonTags,
    required this.isSaved,
    required this.generatedAt,
    required this.items,
  });

  factory SavedOutfitModel.fromJson(Map<String, dynamic> json) {
    return SavedOutfitModel(
      outfitId: json['outfit_id']?.toString() ?? '',
      generationBatchId: json['generation_batch_id']?.toString() ?? '',
      userId: json['user_id']?.toString() ?? '',
      selectedItemId: json['selected_item_id']?.toString() ?? '',
      compatibilityScore: _toDouble(json['compatibility_score']),
      reasonTags: _toStringList(json['reason_tags']),
      isSaved: _toBool(json['is_saved']),
      generatedAt: json['generated_at']?.toString() ?? '',
      items: _toProductList(json['items']),
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

  static bool _toBool(dynamic value) {
    if (value == null) {
      return false;
    }

    if (value is bool) {
      return value;
    }

    return value.toString().toLowerCase() == 'true';
  }
}

class SaveOutfitResponse {
  final String status;
  final String message;
  final SavedOutfitModel? outfit;

  SaveOutfitResponse({
    required this.status,
    required this.message,
    required this.outfit,
  });

  factory SaveOutfitResponse.fromJson(Map<String, dynamic> json) {
    return SaveOutfitResponse(
      status: json['status']?.toString() ?? '',
      message: json['message']?.toString() ?? '',
      outfit: json['outfit'] is Map<String, dynamic>
          ? SavedOutfitModel.fromJson(json['outfit'])
          : null,
    );
  }
}

class SavedOutfitsResponse {
  final String status;
  final String userId;
  final int totalSavedOutfits;
  final List<SavedOutfitModel> savedOutfits;

  SavedOutfitsResponse({
    required this.status,
    required this.userId,
    required this.totalSavedOutfits,
    required this.savedOutfits,
  });

  factory SavedOutfitsResponse.fromJson(Map<String, dynamic> json) {
    return SavedOutfitsResponse(
      status: json['status']?.toString() ?? '',
      userId: json['user_id']?.toString() ?? '',
      totalSavedOutfits: _toInt(json['total_saved_outfits']),
      savedOutfits: _toSavedOutfitList(json['saved_outfits']),
    );
  }

  static List<SavedOutfitModel> _toSavedOutfitList(dynamic value) {
    if (value == null || value is! List) {
      return [];
    }

    return value
        .whereType<Map<String, dynamic>>()
        .map((item) => SavedOutfitModel.fromJson(item))
        .toList();
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

class SavedOutfitDetailResponse {
  final String status;
  final SavedOutfitModel? savedOutfit;

  SavedOutfitDetailResponse({
    required this.status,
    required this.savedOutfit,
  });

  factory SavedOutfitDetailResponse.fromJson(Map<String, dynamic> json) {
    return SavedOutfitDetailResponse(
      status: json['status']?.toString() ?? '',
      savedOutfit: json['saved_outfit'] is Map<String, dynamic>
          ? SavedOutfitModel.fromJson(json['saved_outfit'])
          : null,
    );
  }
}

class RemoveSavedOutfitResponse {
  final String status;
  final String message;
  final String outfitId;

  RemoveSavedOutfitResponse({
    required this.status,
    required this.message,
    required this.outfitId,
  });

  factory RemoveSavedOutfitResponse.fromJson(Map<String, dynamic> json) {
    return RemoveSavedOutfitResponse(
      status: json['status']?.toString() ?? '',
      message: json['message']?.toString() ?? '',
      outfitId: json['outfit_id']?.toString() ?? '',
    );
  }
}