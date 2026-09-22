import 'package:http/http.dart' as http;

import 'http_client_factory_stub.dart'
    if (dart.library.js_interop) 'http_client_factory_web.dart' as impl;

/// Returns the right client for the platform.
///
/// The session is an httpOnly cookie, and the two platforms reach it very differently:
///
/// **Native** (iOS, Android, desktop) has no browser and no cookie jar. `Set-Cookie` is
/// readable on the response, so [SubscriberService] captures it and replays it by hand.
///
/// **Web** cannot read `Set-Cookie` at all — that is the whole point of httpOnly, and it
/// is the protection working, not a bug. The browser already holds the cookie; it just
/// will not attach it cross-origin unless the request opts in. `withCredentials` is that
/// opt-in, and it is exactly what the Next.js client does with `credentials: "include"`.
http.Client createHttpClient() => impl.createPlatformClient();
