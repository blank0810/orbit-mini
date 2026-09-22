import 'package:flutter/material.dart';

import '../models/subscriber_model.dart';
import 'orbit_theme.dart';

/// A status pill carrying an icon AND a word.
///
/// Never colour alone: WCAG 1.4.1 requires it, and it also survives a greyscale screen or
/// a compressed demo video, which is where this card is most likely to be seen.
class StatusBadge extends StatelessWidget {
  const StatusBadge({super.key, required this.status});

  final SubscriberStatus status;

  @override
  Widget build(BuildContext context) {
    final (label, color, icon) = switch (status) {
      SubscriberStatus.active => ('Active', OrbitTheme.accent, Icons.check_rounded),
      SubscriberStatus.pastDue =>
        ('Past due', OrbitTheme.warn, Icons.error_outline_rounded),
      SubscriberStatus.canceled =>
        ('Canceled', OrbitTheme.danger, Icons.close_rounded),
      SubscriberStatus.incomplete =>
        ('Incomplete', OrbitTheme.textMuted, Icons.schedule_rounded),
    };

    return Semantics(
      label: 'Subscription status: $label',
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 7),
        decoration: BoxDecoration(
          color: OrbitTheme.surfaceRaised,
          borderRadius: BorderRadius.circular(999),
          border: Border.all(color: color.withValues(alpha: 0.4)),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 16, color: color),
            const SizedBox(width: 6),
            Text(
              label,
              style: TextStyle(
                color: color,
                fontSize: 14,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
