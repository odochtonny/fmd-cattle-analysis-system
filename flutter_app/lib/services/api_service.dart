import 'dart:convert';
import 'dart:io' show File;
import 'dart:typed_data';

import 'package:http/http.dart' as http;

import '../models/analysis_models.dart';

class ApiService {
  static const String baseUrl = 'http://127.0.0.1:8000';
  // Android emulator: http://10.0.2.2:8000

  static Future<DashboardStats> fetchDashboardStats() async {
    final res = await http.get(Uri.parse('$baseUrl/dashboard/summary'));

    if (res.statusCode != 200) {
      throw Exception('Failed to load dashboard');
    }

    return DashboardStats.fromJson(jsonDecode(res.body));
  }

  static Future<Map<String, dynamic>> analyzeCattle({
    File? image,
    required Uint8List imageBytes,
    required String imageName,
    required Map<String, dynamic> farmInfo,
    required Map<String, dynamic> symptoms,
  }) async {
    final request = http.MultipartRequest(
      'POST',
      Uri.parse('$baseUrl/analyze'),
    );

    request.fields['farm_info'] = jsonEncode(farmInfo);
    request.fields['symptoms'] = jsonEncode(symptoms);

    /*
      Web does not support File path upload.
      Therefore, we upload using imageBytes.
      This also works for Android, Windows, and desktop.
    */
    request.files.add(
      http.MultipartFile.fromBytes(
        'image',
        imageBytes,
        filename: imageName,
      ),
    );

    final streamed = await request.send();
    final response = await http.Response.fromStream(streamed);

    final data = jsonDecode(response.body);

    if (response.statusCode >= 400) {
      throw Exception(
        data['detail']?.toString() ?? 'Analysis failed',
      );
    }

    return data;
  }
}
