/// Validation must use the very same pad-scoped parameter selection as the
/// visible well walk form and the saved measurement snapshot.
class WalkParameterSaveRules {
  WalkParameterSaveRules._();

  static bool requiresProgramConfirmation(
    Set<String> selected, {
    required bool pkvConfirmed,
    required bool pidConfirmed,
  }) =>
      (selected.contains('pkv') && !pkvConfirmed) ||
      (selected.contains('pid') && !pidConfirmed);

  static List<String> capturedParameters(Set<String> selected) {
    // Freeze the pad configuration for this measurement; later edits to the
    // template must not silently mutate historical reports.
    final snapshot = selected.toList()..sort();
    return List<String>.unmodifiable(snapshot);
  }
}
