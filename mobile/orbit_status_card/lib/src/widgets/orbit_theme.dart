import 'package:flutter/material.dart';

/// The tokens read off scalesage.ai, so the card matches the web dashboard exactly.
///
/// `textMuted` is deliberately NOT the site's own #6E7C8F: that measures 4.26:1 on this
/// background and fails WCAG AA for body text. #808D9E measures 5.37:1 and is visually
/// indistinguishable. The accessibility floor is not traded for brand fidelity, on any
/// platform.
abstract final class OrbitTheme {
  static const background = Color(0xFF0A1628);
  static const surface = Color(0x0DFFFFFF);
  static const surfaceRaised = Color(0x14F4F6F9);
  static const border = Color(0x1AF4F6F9);
  static const accent = Color(0xFF3DD9D0);
  static const onAccent = Color(0xFF04161B);
  static const text = Color(0xFFF4F6F9);
  static const textSecondary = Color(0xFFA8B2C0);
  static const textMuted = Color(0xFF808D9E);
  static const danger = Color(0xFFFF6B6B);
  static const warn = Color(0xFFF5A524);

  static const cardRadius = 16.0;
}
