/// A subscription status card for the ScaleSage Orbit mobile app.
///
/// Reads the same `GET /api/subscribers/me` the web dashboard reads. The point is not the
/// widget: it is that one API serves two clients from one contract, so the backend and the
/// mobile app cannot drift apart.
library;

export 'src/models/subscriber_model.dart';
export 'src/services/subscriber_service.dart';
export 'src/widgets/orbit_theme.dart';
export 'src/widgets/status_badge.dart';
export 'src/widgets/status_card.dart';
export 'src/widgets/status_states.dart';
