/// The four states the dashboard renders.
///
/// Deliberately the same vocabulary as the API and the web client. Stripe has eight
/// subscription statuses; the server normalises them to these four before they ever
/// reach a client, so this enum cannot drift from what the web dashboard shows.
enum SubscriberStatus {
  incomplete,
  active,
  pastDue,
  canceled;

  static SubscriberStatus fromApi(String value) {
    switch (value) {
      case 'active':
        return SubscriberStatus.active;
      case 'past_due':
        return SubscriberStatus.pastDue;
      case 'canceled':
        return SubscriberStatus.canceled;
      default:
        // An unknown status is treated as not-yet-paid rather than guessed at. Inventing
        // a fifth state here is how a client starts disagreeing with its own server.
        return SubscriberStatus.incomplete;
    }
  }
}

/// One subscriber, exactly as `GET /api/subscribers/me` returns it.
class Subscriber {
  const Subscriber({
    required this.id,
    required this.email,
    required this.firstName,
    required this.lastName,
    required this.fullName,
    required this.planName,
    required this.status,
    required this.currentPeriodEnd,
    required this.cancelAtPeriodEnd,
  });

  final String id;
  final String email;
  final String firstName;
  final String lastName;
  final String fullName;
  final String planName;
  final SubscriberStatus status;
  final DateTime? currentPeriodEnd;
  final bool cancelAtPeriodEnd;

  /// There is no password field to forget to exclude: the API's read shape has none.
  factory Subscriber.fromJson(Map<String, dynamic> json) {
    final rawEnd = json['current_period_end'] as String?;
    return Subscriber(
      id: json['id'] as String,
      email: json['email'] as String,
      firstName: json['first_name'] as String,
      lastName: json['last_name'] as String,
      fullName: json['full_name'] as String? ??
          '${json['first_name']} ${json['last_name']}',
      planName: json['plan_name'] as String,
      status: SubscriberStatus.fromApi(json['status'] as String),
      currentPeriodEnd: rawEnd == null ? null : DateTime.tryParse(rawEnd)?.toLocal(),
      cancelAtPeriodEnd: json['cancel_at_period_end'] as bool? ?? false,
    );
  }

  bool get isSubscribed => status != SubscriberStatus.incomplete;
}
