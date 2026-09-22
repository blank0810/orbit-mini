import 'package:flutter/material.dart';

import 'orbit_theme.dart';

/// The wait. A skeleton rather than a spinner, so the shape of what is coming is already
/// on screen when it arrives (Doherty Threshold).
class OrbitStatusLoading extends StatelessWidget {
  const OrbitStatusLoading({super.key});

  @override
  Widget build(BuildContext context) {
    return _Shell(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _bar(width: 70, height: 11),
          const SizedBox(height: 14),
          _bar(width: 170, height: 24),
          const SizedBox(height: 26),
          _bar(width: 60, height: 11),
          const SizedBox(height: 12),
          _bar(width: 130, height: 17),
        ],
      ),
    );
  }

  Widget _bar({required double width, required double height}) => Container(
        width: width,
        height: height,
        decoration: BoxDecoration(
          color: OrbitTheme.surfaceRaised,
          borderRadius: BorderRadius.circular(6),
        ),
      );
}

/// A failure the person can act on, with the reason and a way to try again.
class OrbitStatusError extends StatelessWidget {
  const OrbitStatusError({super.key, required this.message, this.onRetry});

  final String message;
  final VoidCallback? onRetry;

  @override
  Widget build(BuildContext context) {
    return _Shell(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.error_outline_rounded,
                  size: 18, color: OrbitTheme.danger),
              const SizedBox(width: 8),
              Text(
                'Could not load',
                style: const TextStyle(
                  color: OrbitTheme.text,
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Text(
            message,
            style: const TextStyle(color: OrbitTheme.textSecondary, fontSize: 14),
          ),
          if (onRetry != null) ...[
            const SizedBox(height: 18),
            TextButton(
              onPressed: onRetry,
              style: TextButton.styleFrom(
                foregroundColor: OrbitTheme.accent,
                // 44 high: a primary action has to be thumb-sized (Fitts's Law), and
                // WCAG 2.2 puts the floor for any target at 24.
                minimumSize: const Size(0, 44),
                padding: const EdgeInsets.symmetric(horizontal: 4),
              ),
              child: const Text('Try again'),
            ),
          ],
        ],
      ),
    );
  }
}

/// Signed in, but nothing bought yet.
class OrbitStatusEmpty extends StatelessWidget {
  const OrbitStatusEmpty({super.key});

  @override
  Widget build(BuildContext context) {
    return const _Shell(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'No plan yet',
            style: TextStyle(
              color: OrbitTheme.text,
              fontSize: 22,
              fontWeight: FontWeight.w600,
            ),
          ),
          SizedBox(height: 8),
          Text(
            'This account exists but no payment has been recorded.',
            style: TextStyle(color: OrbitTheme.textMuted, fontSize: 14),
          ),
        ],
      ),
    );
  }
}

class _Shell extends StatelessWidget {
  const _Shell({required this.child});
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(22),
      decoration: BoxDecoration(
        color: OrbitTheme.surface,
        borderRadius: BorderRadius.circular(OrbitTheme.cardRadius),
        border: Border.all(color: OrbitTheme.border),
      ),
      child: child,
    );
  }
}
