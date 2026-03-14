import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';

import '../../config/app_config.dart';
import '../services/api_client.dart';
import 'event_models.dart';

/// Sends batched tracking events to the analytics backend.
class EventSender {
  EventSender() : _dio = Dio();

  final Dio _dio;

  /// POST a batch of events to `/api/v1/analytics/events`.
  /// Failures are caught and logged — never crashes the app.
  Future<bool> sendBatch(List<TrackingEvent> events) async {
    if (events.isEmpty) return true;

    try {
      final deviceId = ApiClient.instance.deviceId;
      final response = await _dio.post(
        '${AppConfig.apiBaseUrl}/api/v1/analytics/events',
        data: {
          'device_id': deviceId,
          'events': events.map((e) => e.toJson()).toList(),
        },
        options: Options(
          headers: {
            'Content-Type': 'application/json',
            if (deviceId != null) 'X-Device-ID': deviceId,
          },
          sendTimeout: const Duration(seconds: 10),
          receiveTimeout: const Duration(seconds: 10),
        ),
      );
      return response.statusCode != null &&
          response.statusCode! >= 200 &&
          response.statusCode! < 300;
    } on DioException catch (e) {
      if (kDebugMode) print('[EventSender] Failed to send batch: ${e.message}');
      return false;
    } catch (e) {
      if (kDebugMode) print('[EventSender] Unexpected error: $e');
      return false;
    }
  }
}
