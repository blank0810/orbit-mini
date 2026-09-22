import 'package:flutter/material.dart';
import 'package:orbit_status_card/orbit_status_card.dart';

/// Every state the card can be in, with no server involved.
///
/// This is the point of the widget taking a [Subscriber] rather than a URL: each state
/// below is a fabricated object, so reviewing the component does not require a running
/// API, a Stripe key, or a subscriber who happens to be past due today. Three of these
/// states are genuinely hard to reach any other way.
class GalleryPage extends StatelessWidget {
  const GalleryPage({super.key});

  static Subscriber _fixture({
    required String status,
    String plan = 'ScaleSage Pro',
    String? periodEnd = '2026-10-22T14:47:58Z',
    bool cancelAtPeriodEnd = false,
  }) =>
      Subscriber.fromJson({
        'id': '11111111-1111-1111-1111-111111111111',
        'email': 'nina@example.com',
        'first_name': 'Nina',
        'last_name': 'Reyes',
        'full_name': 'Nina Reyes',
        'plan_name': plan,
        'status': status,
        'current_period_end': periodEnd,
        'cancel_at_period_end': cancelAtPeriodEnd,
      });

  @override
  Widget build(BuildContext context) {
    final cases = <(String, String, Widget)>[
      (
        'Active',
        'The ordinary case. Plan, status, renewal date.',
        OrbitStatusCard(subscriber: _fixture(status: 'active')),
      ),
      (
        'Active on Starter',
        'The plan name comes from the server, never from the client.',
        OrbitStatusCard(
          subscriber: _fixture(status: 'active', plan: 'ScaleSage Starter'),
        ),
      ),
      (
        'Cancellation scheduled',
        'Still active, but the date is an ending. Stripe keeps a cancelled subscription '
            'active until the period lapses, so status alone cannot tell these apart.',
        OrbitStatusCard(
          subscriber: _fixture(status: 'active', cancelAtPeriodEnd: true),
        ),
      ),
      (
        'Past due',
        'A payment failed. Amber, and the word says so.',
        OrbitStatusCard(subscriber: _fixture(status: 'past_due')),
      ),
      (
        'Canceled',
        'The date becomes access-until rather than renews.',
        OrbitStatusCard(subscriber: _fixture(status: 'canceled')),
      ),
      (
        'No billing period yet',
        'The row is absent, not a dash. A line reading "Renews —" tells the reader '
            'nothing and looks broken.',
        OrbitStatusCard(
          subscriber: _fixture(status: 'active', periodEnd: null),
        ),
      ),
      (
        'Registered, never paid',
        'The empty state.',
        OrbitStatusCard(subscriber: _fixture(status: 'incomplete')),
      ),
      (
        'Loading',
        'A skeleton in the shape of what is coming, never a spinner.',
        const OrbitStatusLoading(),
      ),
      (
        'Failed',
        'The reason, and a way out.',
        OrbitStatusError(message: 'Not authenticated', onRetry: () {}),
      ),
    ];

    return Scaffold(
      backgroundColor: OrbitTheme.background,
      body: SafeArea(
        child: ListView.separated(
          padding: const EdgeInsets.fromLTRB(20, 28, 20, 48),
          itemCount: cases.length + 1,
          separatorBuilder: (_, _) => const SizedBox(height: 34),
          itemBuilder: (context, index) {
            if (index == 0) return const _Header();
            final (title, note, card) = cases[index - 1];
            return Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title.toUpperCase(),
                  style: const TextStyle(
                    color: OrbitTheme.accent,
                    fontSize: 11.5,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 1.6,
                    fontFamily: 'monospace',
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  note,
                  style: const TextStyle(
                    color: OrbitTheme.textMuted,
                    fontSize: 13,
                    height: 1.45,
                  ),
                ),
                const SizedBox(height: 14),
                card,
              ],
            );
          },
        ),
      ),
    );
  }
}

class _Header extends StatelessWidget {
  const _Header();

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            const Text(
              'OrbitStatusCard',
              style: TextStyle(
                color: OrbitTheme.text,
                fontSize: 26,
                fontWeight: FontWeight.w700,
                letterSpacing: -0.5,
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
        const SizedBox(height: 8),
        const Text(
          'Every state, with no server running. The widget takes a Subscriber rather '
          'than a URL, so past due and canceled can be reviewed without waiting for a '
          'failed card or a lapsed period.',
          style: TextStyle(
            color: OrbitTheme.textSecondary,
            fontSize: 14,
            height: 1.5,
          ),
        ),
      ],
    );
  }
}
