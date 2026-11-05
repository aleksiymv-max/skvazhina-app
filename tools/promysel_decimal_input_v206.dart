import 'package:flutter/services.dart';
import 'package:flutter/widgets.dart';

/// Shared numeric input for field measurements. Accepts a comma or dot
/// regardless of mobile keyboard locale; never rewrites text while typing.
class PromyselDecimalInput {
  PromyselDecimalInput._();

  static final TextInputFormatter decimal = TextInputFormatter.withFunction(
    (previous, incoming) {
      if (RegExp(r'^\d*(?:[,.]\d*)?$').hasMatch(incoming.text)) {
        return incoming;
      }
      return previous;
    },
  );

  static final TextInputFormatter integer = TextInputFormatter.withFunction(
    (previous, incoming) {
      if (RegExp(r'^\d*$').hasMatch(incoming.text)) return incoming;
      return previous;
    },
  );

  static double? parse(String? value) =>
      double.tryParse((value ?? '').trim().replaceAll(',', '.'));

  static void insertComma(TextEditingController controller) {
    final value = controller.value;
    if (value.text.contains(',') || value.text.contains('.')) return;
    final position = value.selection;
    final from = position.isValid ? position.start : value.text.length;
    final to = position.isValid ? position.end : value.text.length;
    final next = value.text.replaceRange(from, to, ',');
    controller.value = TextEditingValue(
      text: next,
      selection: TextSelection.collapsed(offset: from + 1),
    );
  }
}
