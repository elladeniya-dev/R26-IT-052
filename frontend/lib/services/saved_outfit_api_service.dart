import 'dart:convert';

import 'package:http/http.dart' as http;

import '../constants/api_constants.dart';
import '../models/saved_outfit_model.dart';

class SavedOutfitApiService {
  Future<SaveOutfitResponse> saveOutfit({
    required String outfitId,
  }) async {
    try {
      final response = await http
          .post(
            Uri.parse(ApiConstants.saveOutfitEndpoint(outfitId)),
            headers: {
              'Content-Type': 'application/json',
              'Accept': 'application/json',
            },
          )
          .timeout(const Duration(seconds: 30));

      final Map<String, dynamic> responseBody = jsonDecode(response.body);

      if (response.statusCode >= 200 && response.statusCode < 300) {
        return SaveOutfitResponse.fromJson(responseBody);
      }

      final String errorMessage =
          responseBody['detail']?.toString() ??
          responseBody['message']?.toString() ??
          'Failed to save outfit';

      throw Exception(errorMessage);
    } catch (error) {
      throw Exception('Save outfit failed: $error');
    }
  }

  Future<SavedOutfitsResponse> getSavedOutfits({
    required String userId,
  }) async {
    try {
      final response = await http
          .get(
            Uri.parse(ApiConstants.getSavedOutfitsEndpoint(userId)),
            headers: {
              'Accept': 'application/json',
            },
          )
          .timeout(const Duration(seconds: 30));

      final Map<String, dynamic> responseBody = jsonDecode(response.body);

      if (response.statusCode >= 200 && response.statusCode < 300) {
        return SavedOutfitsResponse.fromJson(responseBody);
      }

      final String errorMessage =
          responseBody['detail']?.toString() ??
          responseBody['message']?.toString() ??
          'Failed to load saved outfits';

      throw Exception(errorMessage);
    } catch (error) {
      throw Exception('Load saved outfits failed: $error');
    }
  }

  Future<SavedOutfitDetailResponse> getSavedOutfitDetail({
    required String outfitId,
  }) async {
    try {
      final response = await http
          .get(
            Uri.parse(ApiConstants.savedOutfitDetailEndpoint(outfitId)),
            headers: {
              'Accept': 'application/json',
            },
          )
          .timeout(const Duration(seconds: 30));

      final Map<String, dynamic> responseBody = jsonDecode(response.body);

      if (response.statusCode >= 200 && response.statusCode < 300) {
        return SavedOutfitDetailResponse.fromJson(responseBody);
      }

      final String errorMessage =
          responseBody['detail']?.toString() ??
          responseBody['message']?.toString() ??
          'Failed to load outfit details';

      throw Exception(errorMessage);
    } catch (error) {
      throw Exception('Reuse outfit failed: $error');
    }
  }

  Future<RemoveSavedOutfitResponse> removeSavedOutfit({
    required String outfitId,
  }) async {
    try {
      final response = await http
          .delete(
            Uri.parse(ApiConstants.removeSavedOutfitEndpoint(outfitId)),
            headers: {
              'Accept': 'application/json',
            },
          )
          .timeout(const Duration(seconds: 30));

      final Map<String, dynamic> responseBody = jsonDecode(response.body);

      if (response.statusCode >= 200 && response.statusCode < 300) {
        return RemoveSavedOutfitResponse.fromJson(responseBody);
      }

      final String errorMessage =
          responseBody['detail']?.toString() ??
          responseBody['message']?.toString() ??
          'Failed to remove saved outfit';

      throw Exception(errorMessage);
    } catch (error) {
      throw Exception('Remove saved outfit failed: $error');
    }
  }
}