String canonicalFashionAttribute(String value, {String? dimension}) {
  String key = value
      .trim()
      .toLowerCase()
      .replaceAll(RegExp(r'[\s_\-/]+'), '_')
      .replaceAll(RegExp(r'^_+|_+$'), '');

  if (key.isEmpty) return '';
  final String collapsed = key.replaceAll('_', '');

  if (dimension == 'category') {
    const aliases = <String, String>{
      'top': 'top',
      'tops': 'top',
      'tshirt': 'tshirt',
      'tshirts': 'tshirt',
      'tee': 'tshirt',
      'tees': 'tshirt',
      'shirt': 'shirt',
      'shirts': 'shirt',
      'dress': 'dress',
      'dresses': 'dress',
      'jean': 'jeans',
      'jeans': 'jeans',
      'trouser': 'pants',
      'trousers': 'pants',
      'pant': 'pants',
      'pants': 'pants',
      'skirt': 'skirt',
      'skirts': 'skirt',
      'short': 'shorts',
      'shorts': 'shorts',
      'jacket': 'jacket',
      'jackets': 'jacket',
      'blazer': 'blazer',
      'blazers': 'blazer',
      'sweater': 'sweater',
      'sweaters': 'sweater',
      'hoodie': 'hoodie',
      'hoodies': 'hoodie',
      'legging': 'leggings',
      'leggings': 'leggings',
    };
    return aliases[collapsed] ?? key;
  }

  if (dimension == 'style') {
    const aliases = <String, String>{
      'smartcasual': 'smart_casual',
      'partywear': 'party',
      'party': 'party',
      'comfortwear': 'comfort',
      'comfort': 'comfort',
      'workwear': 'workwear',
    };
    return aliases[collapsed] ?? key;
  }

  return key;
}

String formatFashionAttribute(String value) {
  final String canonical = value.trim().toLowerCase().replaceAll('-', '_');
  const categoryLabels = <String, String>{
    'top': 'Tops',
    'tshirt': 'T-shirts',
    'shirt': 'Shirts',
    'dress': 'Dresses',
    'skirt': 'Skirts',
    'jacket': 'Jackets',
    'blazer': 'Blazers',
    'sweater': 'Sweaters',
    'hoodie': 'Hoodies',
  };
  if (categoryLabels.containsKey(canonical)) {
    return categoryLabels[canonical]!;
  }

  final String normalized = value.trim().replaceAll(RegExp(r'[_\-]+'), ' ');
  if (normalized.isEmpty) return '';

  return normalized
      .split(RegExp(r'\s+'))
      .where((word) => word.isNotEmpty)
      .map(
        (word) => '${word[0].toUpperCase()}${word.substring(1).toLowerCase()}',
      )
      .join(' ');
}

List<String> formatFashionAttributes(Iterable<String> values) => values
    .map(formatFashionAttribute)
    .where((value) => value.isNotEmpty)
    .toList();
