import 'package:flutter/foundation.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';

import '../models/recommendation_product_model.dart';
import 'recommendation_api_service.dart';
import 'trend_api_service.dart';

/// Phone notification listing real catalog pieces that are trending and fit
/// the signed-in user, e.g. "You may like these trending picks".
///
/// Products always come from the partner (Koji) recommendations; the trend
/// engine only scores them. Runs once per app launch, only on Android/iOS,
/// and stays silent on any failure.
class TrendNotificationService {
  TrendNotificationService._();
  static final TrendNotificationService instance = TrendNotificationService._();

  static const int _instantId = 7001;
  static const int _dailyId = 7002;
  static const int _maxItems = 3;
  static const int _maxTitleLength = 38;

  static const AndroidNotificationChannel _channel = AndroidNotificationChannel(
    'trend_picks',
    'Trending picks',
    description: 'Trending pieces picked for you',
    importance: Importance.high,
  );

  final FlutterLocalNotificationsPlugin _plugin =
      FlutterLocalNotificationsPlugin();
  bool _initialized = false;
  bool _ranThisLaunch = false;

  bool get _supported =>
      !kIsWeb &&
      (defaultTargetPlatform == TargetPlatform.android ||
          defaultTargetPlatform == TargetPlatform.iOS);

  Future<void> notifyTrendingPicks(int userId) async {
    if (!_supported || _ranThisLaunch) return;
    _ranThisLaunch = true;

    try {
      final List<String> names = await _pickTrendingNames(userId);
      if (names.isEmpty) return;

      await _ensureInitialized();
      if (!await _hasPermission()) return;

      final NotificationDetails details = _detailsFor(names);
      const String title = 'You may like these trending picks';
      final String body = _bodyFor(names);

      await _plugin.show(
        id: _instantId,
        title: title,
        body: body,
        notificationDetails: details,
      );

      // Repeats daily with the picks from this launch; replaced on the next one.
      await _plugin.periodicallyShow(
        id: _dailyId,
        title: title,
        body: body,
        repeatInterval: RepeatInterval.daily,
        notificationDetails: details,
        androidScheduleMode: AndroidScheduleMode.inexactAllowWhileIdle,
      );
    } catch (_) {
      // A missing notification must never affect the app.
    }
  }

  /// Names of the user's recommended pieces that the trend engine scores
  /// highest, strongest first.
  Future<List<String>> _pickTrendingNames(int userId) async {
    final List<RecommendationProduct> recommended =
        await RecommendationApiService().getRecommendationsFromChala(
      userId: userId,
      priceMin: 0,
      priceMax: 999999,
      maxResults: 60,
    );
    if (recommended.isEmpty) return [];

    // A cloth is picked only when it carries a whole rising look (for example
    // white AND dress), never because one of its attributes is rising.
    final Map<String, ProductTrend> scores = await TrendApiService()
        .scoreProducts([for (final p in recommended) trendScoringPayload(p)]);

    final List<RecommendationProduct> trending = recommended
        .where((p) => scores.containsKey(p.itemId))
        .toList()
      ..sort((a, b) => scores[b.itemId]!
          .segmentScore
          .compareTo(scores[a.itemId]!.segmentScore));

    final List<String> names = [];
    for (final RecommendationProduct p in trending) {
      final String name = _shorten(p.title.trim());
      if (name.isNotEmpty && !names.contains(name)) names.add(name);
      if (names.length >= _maxItems) break;
    }
    return names;
  }

  Future<void> _ensureInitialized() async {
    if (_initialized) return;

    await _plugin.initialize(
      settings: const InitializationSettings(
        android: AndroidInitializationSettings('@mipmap/ic_launcher'),
        iOS: DarwinInitializationSettings(),
      ),
    );
    await _plugin
        .resolvePlatformSpecificImplementation<
            AndroidFlutterLocalNotificationsPlugin>()
        ?.createNotificationChannel(_channel);
    _initialized = true;
  }

  Future<bool> _hasPermission() async {
    final AndroidFlutterLocalNotificationsPlugin? android = _plugin
        .resolvePlatformSpecificImplementation<
            AndroidFlutterLocalNotificationsPlugin>();
    if (android != null) {
      return await android.requestNotificationsPermission() ?? false;
    }
    final IOSFlutterLocalNotificationsPlugin? ios = _plugin
        .resolvePlatformSpecificImplementation<
            IOSFlutterLocalNotificationsPlugin>();
    return await ios?.requestPermissions(alert: true, badge: true, sound: true) ??
        false;
  }

  NotificationDetails _detailsFor(List<String> names) {
    return NotificationDetails(
      android: AndroidNotificationDetails(
        _channel.id,
        _channel.name,
        channelDescription: _channel.description,
        importance: Importance.high,
        priority: Priority.high,
        styleInformation: BigTextStyleInformation(
          names.map((n) => '• $n').join('\n'),
          contentTitle: 'You may like these trending picks',
          summaryText: 'Trending right now',
        ),
      ),
      iOS: const DarwinNotificationDetails(),
    );
  }

  String _bodyFor(List<String> names) {
    if (names.length == 1) return names.first;
    return '${names.sublist(0, names.length - 1).join(', ')} and ${names.last}';
  }

  String _shorten(String title) {
    if (title.length <= _maxTitleLength) return title;
    return '${title.substring(0, _maxTitleLength - 1).trimRight()}…';
  }
}
