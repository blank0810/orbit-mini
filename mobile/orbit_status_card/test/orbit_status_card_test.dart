import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:orbit_status_card/orbit_status_card.dart';

Subscriber _subscriber({
  String status = 'active',
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

Future<void> _pump(WidgetTester tester, Widget child) => tester.pumpWidget(
      MaterialApp(home: Scaffold(body: child)),
    );

void main() {
  group('Subscriber', () {
    test('maps every Stripe status the server can send', () {
      expect(SubscriberStatus.fromApi('active'), SubscriberStatus.active);
      expect(SubscriberStatus.fromApi('past_due'), SubscriberStatus.pastDue);
      expect(SubscriberStatus.fromApi('canceled'), SubscriberStatus.canceled);
      expect(SubscriberStatus.fromApi('incomplete'), SubscriberStatus.incomplete);
    });

    test('an unknown status falls back rather than inventing a fifth state', () {
      expect(SubscriberStatus.fromApi('something_new'), SubscriberStatus.incomplete);
    });

    test('a null period end is tolerated', () {
      expect(_subscriber(periodEnd: null).currentPeriodEnd, isNull);
    });

    test('incomplete means not subscribed', () {
      expect(_subscriber(status: 'incomplete').isSubscribed, isFalse);
      expect(_subscriber().isSubscribed, isTrue);
    });
  });

  group('OrbitStatusCard', () {
    testWidgets('shows the plan, the status word and the renewal date', (tester) async {
      await _pump(tester, OrbitStatusCard(subscriber: _subscriber()));

      expect(find.text('ScaleSage Pro'), findsOneWidget);
      expect(find.text('Active'), findsOneWidget);
      expect(find.text('RENEWS'), findsOneWidget);
      expect(find.text('22 October 2026'), findsOneWidget);
    });

    testWidgets('status is never colour alone: the word is present too', (tester) async {
      await _pump(tester, OrbitStatusCard(subscriber: _subscriber(status: 'past_due')));

      expect(find.text('Past due'), findsOneWidget);
      expect(find.byIcon(Icons.error_outline_rounded), findsOneWidget);
    });

    testWidgets('a scheduled cancellation reads as ENDS, not RENEWS', (tester) async {
      await _pump(
        tester,
        OrbitStatusCard(subscriber: _subscriber(cancelAtPeriodEnd: true)),
      );

      expect(find.text('ENDS'), findsOneWidget);
      expect(find.text('RENEWS'), findsNothing);
    });

    testWidgets('a cancelled subscription reads as ACCESS UNTIL', (tester) async {
      await _pump(tester, OrbitStatusCard(subscriber: _subscriber(status: 'canceled')));

      expect(find.text('ACCESS UNTIL'), findsOneWidget);
    });

    testWidgets('no date means no period row, never a dash', (tester) async {
      await _pump(tester, OrbitStatusCard(subscriber: _subscriber(periodEnd: null)));

      expect(find.text('RENEWS'), findsNothing);
      expect(find.textContaining('—'), findsNothing);
    });

    testWidgets('an unpaid account gets the empty state', (tester) async {
      await _pump(tester, OrbitStatusCard(subscriber: _subscriber(status: 'incomplete')));

      expect(find.text('No plan yet'), findsOneWidget);
    });
  });
}
