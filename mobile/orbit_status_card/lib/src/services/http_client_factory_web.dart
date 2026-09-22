import 'package:http/browser_client.dart';
import 'package:http/http.dart' as http;

/// Web: let the browser attach the httpOnly session cookie itself.
http.Client createPlatformClient() => BrowserClient()..withCredentials = true;
