import 'package:http/http.dart' as http;

/// Native platforms: the default client, plus manual cookie replay in the service.
http.Client createPlatformClient() => http.Client();
