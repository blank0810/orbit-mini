import 'dart:convert';

import 'package:http/http.dart' as http;

import '../models/subscriber_model.dart';
import 'http_client_factory.dart';

/// Thrown when the API answers, but not with what was asked for.
class OrbitApiException implements Exception {
  OrbitApiException(this.statusCode, this.message);
  final int statusCode;
  final String message;
  @override
  String toString() => 'OrbitApiException($statusCode): $message';
}

/// The only class in this package that talks to the network.
///
/// Same rule as `stripe_client.py` on the server and `lib/api/client.ts` on the web:
/// one module per boundary. Widgets take a [Subscriber], never a URL, so they can be
/// rendered in a test or a storybook without a server.
class SubscriberService {
  SubscriberService({required this.baseUrl, http.Client? client})
      : _client = client ?? createHttpClient();

  final String baseUrl;
  final http.Client _client;

  /// The session is an httpOnly cookie. A browser stores it automatically; on mobile
  /// there is no cookie jar, so it is captured here and replayed by hand.
  String? _sessionCookie;

  bool get isSignedIn => _sessionCookie != null;

  Future<Subscriber> signIn(String email, String password) async {
    final response = await _client.post(
      Uri.parse('$baseUrl/api/auth/login'),
      headers: const {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email, 'password': password}),
    );
    if (response.statusCode != 200) {
      throw OrbitApiException(response.statusCode, _detail(response.body));
    }
    _captureSession(response);
    return Subscriber.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
  }

  /// Creates a throwaway demo account and signs into it. The API caps these at five and
  /// evicts the oldest, so calling it repeatedly cannot grow the table.
  Future<Subscriber> signInAsNewDemo() async {
    final response = await _client.post(Uri.parse('$baseUrl/api/demo/generate'));
    if (response.statusCode != 201) {
      throw OrbitApiException(response.statusCode, _detail(response.body));
    }
    _captureSession(response);
    return fetchMe();
  }

  Future<Subscriber> fetchMe() async {
    final response = await _client.get(
      Uri.parse('$baseUrl/api/subscribers/me'),
      headers: {'Cookie': ?_sessionCookie},
    );
    if (response.statusCode != 200) {
      throw OrbitApiException(response.statusCode, _detail(response.body));
    }
    return Subscriber.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
  }

  void _captureSession(http.Response response) {
    // Null on web, always: httpOnly means JavaScript cannot see it. The browser has it
    // and withCredentials sends it, so there is nothing to capture and nothing wrong.
    final raw = response.headers['set-cookie'];
    if (raw == null) return;
    // Only the name=value pair travels back; the flags are instructions to a browser.
    _sessionCookie = raw.split(';').first;
  }

  String _detail(String body) {
    try {
      final decoded = jsonDecode(body);
      if (decoded is Map && decoded['detail'] is String) {
        return decoded['detail'] as String;
      }
    } on FormatException {
      // A proxy can return HTML. Fall through to the generic message.
    }
    return 'Request failed';
  }

  void dispose() => _client.close();
}
