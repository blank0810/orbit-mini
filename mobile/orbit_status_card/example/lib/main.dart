import 'package:flutter/material.dart';
import 'package:orbit_status_card/orbit_status_card.dart';

/// A host app whose only job is to show the card against the real API.
///
/// The package is the deliverable; this exists so it can be run and recorded.
void main() => runApp(const OrbitExampleApp());

const _apiBaseUrl = String.fromEnvironment(
  'ORBIT_API_BASE_URL',
  defaultValue: 'https://orbit.ehnand.com',
);

class OrbitExampleApp extends StatelessWidget {
  const OrbitExampleApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Orbit',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.dark,
        scaffoldBackgroundColor: OrbitTheme.background,
        fontFamily: 'sans-serif',
      ),
      home: const _Home(),
    );
  }
}

class _Home extends StatefulWidget {
  const _Home();
  @override
  State<_Home> createState() => _HomeState();
}

class _HomeState extends State<_Home> {
  late final SubscriberService _service =
      SubscriberService(baseUrl: _apiBaseUrl);

  Subscriber? _subscriber;
  String? _error;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _service.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      // Generates a throwaway demo account and signs into it, so the card has something
      // real to show without anyone typing credentials. The API caps these at five.
      final subscriber = await _service.signInAsNewDemo();
      if (!mounted) return;
      setState(() {
        _subscriber = subscriber;
        _loading = false;
      });
    } on Object catch (error) {
      if (!mounted) return;
      setState(() {
        _error = error is OrbitApiException ? error.message : 'Network unavailable';
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 460),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      const Text(
                        'Orbit',
                        style: TextStyle(
                          color: OrbitTheme.text,
                          fontSize: 22,
                          fontWeight: FontWeight.w600,
                          letterSpacing: -0.3,
                        ),
                      ),
                      const SizedBox(width: 8),
                      Container(
                        width: 8,
                        height: 8,
                        decoration: const BoxDecoration(
                          color: OrbitTheme.accent,
                          shape: BoxShape.circle,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 28),
                  if (_subscriber case final subscriber?)
                    Text(
                      '${subscriber.firstName}’s subscription',
                      style: const TextStyle(
                        color: OrbitTheme.text,
                        fontSize: 27,
                        fontWeight: FontWeight.w700,
                        letterSpacing: -0.5,
                      ),
                    ),
                  if (_subscriber case final subscriber?) ...[
                    const SizedBox(height: 6),
                    Text(
                      subscriber.email,
                      style: const TextStyle(
                        color: OrbitTheme.textMuted,
                        fontSize: 14,
                      ),
                    ),
                  ],
                  const SizedBox(height: 20),
                  if (_loading)
                    const OrbitStatusLoading()
                  else if (_error case final message?)
                    OrbitStatusError(message: message, onRetry: _load)
                  else if (_subscriber case final subscriber?)
                    OrbitStatusCard(subscriber: subscriber),
                  const SizedBox(height: 22),
                  Text(
                    'Same API as the web dashboard.',
                    style: TextStyle(
                      color: OrbitTheme.textMuted.withValues(alpha: 0.8),
                      fontSize: 13,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
