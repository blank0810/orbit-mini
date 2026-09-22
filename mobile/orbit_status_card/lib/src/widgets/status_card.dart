import 'package:flutter/material.dart';

import '../models/subscriber_model.dart';
import 'orbit_theme.dart';
import 'status_badge.dart';
import 'status_states.dart';

/// The subscription status card.
///
/// Takes a [Subscriber], never a URL. Fetching is the service's job, so this renders
/// identically in a test, a preview, or the real app, and one API call is not made twice
/// because two widgets both wanted the data.
class OrbitStatusCard extends StatelessWidget {
  const OrbitStatusCard({super.key, required this.subscriber});

  final Subscriber subscriber;

  @override
  Widget build(BuildContext context) {
    if (!subscriber.isSubscribed) return const OrbitStatusEmpty();

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(22),
      decoration: BoxDecoration(
        color: OrbitTheme.surface,
        borderRadius: BorderRadius.circular(OrbitTheme.cardRadius),
        border: Border.all(color: OrbitTheme.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const _Label('PLAN'),
                    const SizedBox(height: 8),
                    Text(
                      subscriber.planName,
                      style: const TextStyle(
                        color: OrbitTheme.text,
                        fontSize: 24,
                        fontWeight: FontWeight.w600,
                        letterSpacing: -0.3,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 12),
              StatusBadge(status: subscriber.status),
            ],
          ),

          // The period row only appears when there IS a date. A row reading "Renews —"
          // tells the reader nothing and looks broken; its absence is the honest signal.
          if (subscriber.currentPeriodEnd != null) ...[
            const SizedBox(height: 22),
            const Divider(height: 1, color: OrbitTheme.border),
            const SizedBox(height: 18),
            _Label(_periodLabel),
            const SizedBox(height: 8),
            Text(
              _formatDate(subscriber.currentPeriodEnd!),
              style: const TextStyle(color: OrbitTheme.text, fontSize: 17),
            ),
          ],

          if (subscriber.cancelAtPeriodEnd) ...[
            const SizedBox(height: 18),
            Text(
              'Ends on this date. You keep everything until then.',
              style: TextStyle(color: OrbitTheme.warn, fontSize: 13.5),
            ),
          ],
        ],
      ),
    );
  }

  /// Stripe keeps a cancelled subscription active until the period lapses, so status
  /// alone cannot tell a renewal from an ending.
  String get _periodLabel {
    if (subscriber.status == SubscriberStatus.canceled) return 'ACCESS UNTIL';
    if (subscriber.cancelAtPeriodEnd) return 'ENDS';
    return 'RENEWS';
  }

  static const _months = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December',
  ];

  /// Formatted by hand rather than with intl: one date format does not justify a
  /// dependency, and the web client renders the same en-GB shape.
  static String _formatDate(DateTime date) =>
      '${date.day} ${_months[date.month - 1]} ${date.year}';
}

class _Label extends StatelessWidget {
  const _Label(this.text);
  final String text;

  @override
  Widget build(BuildContext context) => Text(
        text,
        style: const TextStyle(
          color: OrbitTheme.textMuted,
          fontSize: 11.5,
          fontWeight: FontWeight.w600,
          letterSpacing: 1.6,
          fontFamily: 'monospace',
        ),
      );
}
