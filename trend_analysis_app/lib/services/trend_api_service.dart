import 'dart:convert';

import 'package:http/http.dart' as http;

import '../models/trend_model.dart';
import '../models/trend_insight_model.dart';

class TrendApiService {
  static const String baseUrl = 'https://trend-analysis-engine.onrender.com';

  Future<List<TrendModel>> getAllTrends() async {
    final Uri url = Uri.parse('$baseUrl/trends');

    final response = await http.get(url);

    if (response.statusCode == 200) {
      final Map<String, dynamic> decodedData = jsonDecode(response.body);
      final List<dynamic> trendsJson = decodedData['trends'] ?? [];

      return trendsJson
          .map((trendJson) => TrendModel.fromJson(trendJson))
          .toList();
    } else {
      throw Exception(
        'Failed to load trends. Status code: ${response.statusCode}',
      );
    }
  }
  
  Future<List<TrendModel>> getTrendHistory() async {
  final Uri url = Uri.parse('$baseUrl/trends/history');

  final response = await http.get(url);

  if (response.statusCode == 200) {
    final Map<String, dynamic> decodedData = jsonDecode(response.body);
    final List<dynamic> trendsJson = decodedData['trends'] ?? [];

    return trendsJson
        .map((trendJson) => TrendModel.fromJson(trendJson))
        .toList();
  } else {
    throw Exception(
      'Failed to load trend history. Status code: ${response.statusCode}',
    );
  }
}

  Future<List<TrendModel>> getTrendsByAttributeType(String attributeType) async {
    final Uri url = Uri.parse('$baseUrl/trends/$attributeType');

    final response = await http.get(url);

    if (response.statusCode == 200) {
      final Map<String, dynamic> decodedData = jsonDecode(response.body);
      final List<dynamic> trendsJson = decodedData['trends'] ?? [];

      return trendsJson
          .map((trendJson) => TrendModel.fromJson(trendJson))
          .toList();
    } else {
      throw Exception(
        'Failed to load $attributeType trends. Status code: ${response.statusCode}',
      );
    }
  }
    Future<Map<String, dynamic>> analyzeTrends() async {
    final Uri url = Uri.parse('$baseUrl/trends/analyze');

    final response = await http.get(url);

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception(
        'Failed to analyze trends. Status code: ${response.statusCode}',
      );
    }
  }
  Future<List<TrendInsightModel>> getTrendInsights() async {
  final Uri url = Uri.parse('$baseUrl/trend-insights');

  final response = await http.get(url);

  if (response.statusCode == 200) {
    final Map<String, dynamic> decodedData = jsonDecode(response.body);

    final List<dynamic> insightsJson = decodedData['insights'] ?? [];

    return insightsJson
        .map((item) => TrendInsightModel.fromJson(item))
        .toList();
  } else {
    throw Exception(
      'Failed to load trend insights. Status code: ${response.statusCode}',
    );
  }
}
}