import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Backend host configuration, with a runtime-editable override.
///
/// Default is '127.0.0.1', which works when the app runs on the SAME
/// machine as the backends (Chrome/web), OR on an Android phone with
/// `adb reverse tcp:8001 tcp:8001` (etc.) set up over USB — see
/// connect_phone.ps1. adb reverse makes the phone's own 127.0.0.1
/// transparently tunnel to the laptop, so this never needs to change
/// even if the WiFi network changes, since it doesn't depend on WiFi
/// at all.
///
/// If USB isn't available at a venue, [setOverrideHost] lets the
/// laptop's LAN IP be typed in from the login screen info button
/// instead — no rebuild needed, takes effect immediately, and persists
/// across app restarts (cleared with an empty value to go back to
/// 127.0.0.1).
class ApiConfig {
  static const String _defaultHost = 'http://127.0.0.1';
  static const String _storageKey = 'api_host_override';

  static final FlutterSecureStorage _storage = const FlutterSecureStorage();

  static String? _overrideHost;

  /// Plug-and-play dev login. Run with `--dart-define=DEV_LOGIN=true`
  /// to show the "Dev login" button on the welcome screen; omit the
  /// flag to get the normal Google-only screen. Never active in
  /// release builds.
  static const bool _devLoginFlag =
      bool.fromEnvironment('DEV_LOGIN', defaultValue: false);

  static bool get devLoginEnabled => _devLoginFlag && !kReleaseMode;

  /// Loads any saved override from disk. Call once at app startup,
  /// before the first network request.
  static Future<void> init() async {
    _overrideHost = await _storage.read(key: _storageKey);
  }

  /// Sets (or clears, with null/empty) the backend host override.
  /// Expects just a host, e.g. "http://192.168.1.2" — no port, no
  /// trailing slash.
  static Future<void> setOverrideHost(String? host) async {
    final String? trimmed = host?.trim();

    if (trimmed == null || trimmed.isEmpty) {
      await _storage.delete(key: _storageKey);
      _overrideHost = null;
      return;
    }

    await _storage.write(key: _storageKey, value: trimmed);
    _overrideHost = trimmed;
  }

  static String get currentHost => _overrideHost ?? _defaultHost;

  static bool get isUsingOverride => _overrideHost != null;

  // Chala backend: Google Sign-In, Onboarding, User Profile, Learning Engine.
  // Deployed value: https://r26-it-052.onrender.com
  static String get baseUrl => '$currentHost:8001';

  // Koji backend: Data Collection and Recommendation Engine.
  // Deployed value: https://koji-outfitiq.onrender.com
  static String get recommendationBaseUrl => '$currentHost:8002';

  // Givi backend: Trend Analysis Engine.
  // Attribute-level trend scores only — never a product source.
  static String get trendBaseUrl => '$currentHost:8003';

  // Senu backend: Outfit Matching and Style Compatibility Engine.
  static String get outfitMatchBaseUrl => '$currentHost:8004';
}
