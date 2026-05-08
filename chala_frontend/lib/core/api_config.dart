class ApiConfig {
  // Backend base URL for physical Android phone testing using ADB reverse.
  // Before testing backend APIs, run:
  // adb reverse tcp:8000 tcp:8000
  static const String baseUrl = 'http://127.0.0.1:8000';
}