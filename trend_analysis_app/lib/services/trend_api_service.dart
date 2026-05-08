import 'dart:convert';

import 'package:http/http.dart' as http;

import '../models/trend_model.dart';

class TrendApiService {
  static const String baseUrl = 'http://192.168.1.2:9000';

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
}