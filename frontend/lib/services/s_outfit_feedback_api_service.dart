import 'dart:convert';

import 'package:http/http.dart' as http;

import '../constants/s_api_constants.dart';

class OutfitFeedbackApiService {
  Future<String> submitFeedback({
    required String outfitId,
    required String userId,
    required int rating,
    String? comment,
  }) async {
    final Map<String, dynamic> requestBody = {
      'user_id': userId,
      'rating': rating,
      'comment': comment,
    };

    try {
      final response = await http
          .post(
            Uri.parse(ApiConstants.submitOutfitFeedbackEndpoint(outfitId)),
            headers: {
              'Content-Type': 'application/json',
              'Accept': 'application/json',
            },
            body: jsonEncode(requestBody),
          )
          .timeout(const Duration(seconds: 30));

      final Map<String, dynamic> responseBody = jsonDecode(response.body);

      if (response.statusCode >= 200 && response.statusCode < 300) {
        return responseBody['message']?.toString() ??
            'Feedback saved successfully';
      }

      final String errorMessage =
          responseBody['detail']?.toString() ??
          responseBody['message']?.toString() ??
          'Failed to save outfit feedback';

      throw Exception(errorMessage);
    } on Exception {
      rethrow;
    } catch (error) {
      throw Exception('Save feedback failed: $error');
    }
  }

  Future<OutfitFeedbackSummary> getFeedbackSummary({
    required String userId,
  }) async {
    try {
      final response = await http
          .get(
            Uri.parse(ApiConstants.outfitFeedbackSummaryEndpoint(userId)),
            headers: {'Accept': 'application/json'},
          )
          .timeout(const Duration(seconds: 30));

      final Map<String, dynamic> responseBody = jsonDecode(response.body);

      if (response.statusCode >= 200 && response.statusCode < 300) {
        final summary = responseBody['summary'];

        return OutfitFeedbackSummary.fromJson(
          summary is Map<String, dynamic> ? summary : {},
        );
      }

      final String errorMessage =
          responseBody['detail']?.toString() ??
          responseBody['message']?.toString() ??
          'Failed to load feedback summary';

      throw Exception(errorMessage);
    } on Exception {
      rethrow;
    } catch (error) {
      throw Exception('Load feedback summary failed: $error');
    }
  }
}

class OutfitFeedbackSummary {
  final String userId;
  final int totalFeedback;
  final double averageRating;
  final int goodMatches;
  final int okayMatches;
  final int badMatches;
  final Map<String, int> ratingDistribution;

  OutfitFeedbackSummary({
    required this.userId,
    required this.totalFeedback,
    required this.averageRating,
    required this.goodMatches,
    required this.okayMatches,
    required this.badMatches,
    required this.ratingDistribution,
  });

  factory OutfitFeedbackSummary.fromJson(Map<String, dynamic> json) {
    return OutfitFeedbackSummary(
      userId: json['user_id']?.toString() ?? '',
      totalFeedback: _toInt(json['total_feedback']),
      averageRating: _toDouble(json['average_rating']),
      goodMatches: _toInt(json['good_matches']),
      okayMatches: _toInt(json['okay_matches']),
      badMatches: _toInt(json['bad_matches']),
      ratingDistribution: _toRatingDistribution(json['rating_distribution']),
    );
  }

  static Map<String, int> _toRatingDistribution(dynamic value) {
    final defaultDistribution = {'1': 0, '2': 0, '3': 0, '4': 0, '5': 0};

    if (value is! Map) {
      return defaultDistribution;
    }

    for (final entry in value.entries) {
      final key = entry.key.toString();

      if (defaultDistribution.containsKey(key)) {
        defaultDistribution[key] = _toInt(entry.value);
      }
    }

    return defaultDistribution;
  }

  static int _toInt(dynamic value) {
    if (value == null) {
      return 0;
    }

    if (value is int) {
      return value;
    }

    if (value is double) {
      return value.round();
    }

    return int.tryParse(value.toString()) ?? 0;
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
