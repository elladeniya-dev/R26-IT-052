import 'package:flutter/material.dart';

import '../models/product_model.dart';

class SearchScreen extends StatefulWidget {
  final List<ProductModel> allProducts;
  final List<String> searchHistory;
  final void Function(String query, List<ProductModel> results,
      List<String> updatedHistory) onSearch;

  const SearchScreen({
    super.key,
    required this.allProducts,
    required this.searchHistory,
    required this.onSearch,
  });

  @override
  State<SearchScreen> createState() => _SearchScreenState();
}

class _SearchScreenState extends State<SearchScreen> {
  late final TextEditingController _controller;
  late List<String> _history;
  bool _showHistory = true;

  static const _accent = Color(0xFF0B5D85);
  static const _accentLight = Color(0xFF5AB4D6);

  static const List<String> _discoveryTerms = [
    'casual top',
    'formal wear',
    'denim jeans',
    'white jacket',
    'blazer',
    'trendy outfit',
    'summer look',
    'streetwear',
  ];

  @override
  void initState() {
    super.initState();
    _controller = TextEditingController();
    _history = List<String>.from(widget.searchHistory);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _doSearch(String raw) {
    final query = raw.trim();
    if (query.isEmpty) return;

    final results = widget.allProducts.where((p) {
      final text = [
        p.itemId,
        p.title,
        p.role,
        p.brand,
        p.description,
        ...p.color,
        ...p.style,
      ].join(' ').toLowerCase();
      return text.contains(query.toLowerCase());
    }).toList();

    final updated = [
      query,
      ..._history.where((h) => h != query),
    ].take(10).toList();

    setState(() {
      _history = updated;
      _showHistory = false;
    });

    widget.onSearch(query, results, updated);
    Navigator.pop(context);
  }

  void _clearHistory() {
    setState(() {
      _history = [];
    });
  }

  @override
  Widget build(BuildContext context) {
    final safePad = MediaQuery.paddingOf(context);

    return Scaffold(
      backgroundColor: Colors.white,
      body: Column(
        children: [
          // ── Top bar ──────────────────────────────────────
          Container(
            color: Colors.white,
            padding: EdgeInsets.only(
              top: safePad.top + 8,
              left: 8,
              right: 12,
              bottom: 12,
            ),
            child: Row(
              children: [
                // Back arrow
                IconButton(
                  icon: const Icon(Icons.arrow_back_ios_new, size: 20),
                  color: const Color(0xFF111827),
                  onPressed: () => Navigator.pop(context),
                ),

                // Text field
                Expanded(
                  child: Container(
                    height: 46,
                    decoration: BoxDecoration(
                      border: Border.all(color: _accent, width: 2),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Row(
                      children: [
                        Expanded(
                          child: TextField(
                            controller: _controller,
                            autofocus: true,
                            textInputAction: TextInputAction.search,
                            style: const TextStyle(
                              fontSize: 15,
                              fontWeight: FontWeight.w500,
                              color: Color(0xFF111827),
                            ),
                            decoration: InputDecoration(
                              hintText: 'Search products, brands, styles…',
                              hintStyle: TextStyle(
                                fontSize: 13.5,
                                color: Colors.grey.shade400,
                                fontWeight: FontWeight.w400,
                              ),
                              border: InputBorder.none,
                              contentPadding: const EdgeInsets.symmetric(
                                horizontal: 12,
                                vertical: 12,
                              ),
                              isDense: true,
                            ),
                            onChanged: (_) {
                              setState(() {
                                _showHistory = _controller.text.isEmpty;
                              });
                            },
                            onSubmitted: _doSearch,
                          ),
                        ),
                        // Camera / scan icon inside field
                        Padding(
                          padding: const EdgeInsets.only(right: 8),
                          child: Icon(
                            Icons.qr_code_scanner_rounded,
                            size: 22,
                            color: Colors.grey.shade400,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),

                const SizedBox(width: 10),

                // Orange Search button
                SizedBox(
                  height: 46,
                  child: ElevatedButton(
                    onPressed: () => _doSearch(_controller.text),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: _accent,
                      foregroundColor: Colors.white,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(10),
                      ),
                      padding: const EdgeInsets.symmetric(horizontal: 16),
                      elevation: 0,
                    ),
                    child: const Text(
                      'Search',
                      style: TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),

          const Divider(height: 1, thickness: 0.5, color: Color(0xFFE5E7EB)),

          // ── Scrollable body ────────────────────────────────
          Expanded(
            child: ListView(
              padding:
                  const EdgeInsets.symmetric(horizontal: 18, vertical: 16),
              children: [
                // Search History section
                if (_history.isNotEmpty && _showHistory) ...[
                  Row(
                    children: [
                      const Text(
                        'Search History',
                        style: TextStyle(
                          fontSize: 15,
                          fontWeight: FontWeight.w800,
                          color: Color(0xFF111827),
                        ),
                      ),
                      const Spacer(),
                      GestureDetector(
                        onTap: _clearHistory,
                        child: Row(
                          children: [
                            Text(
                              'Clear All',
                              style: TextStyle(
                                fontSize: 12.5,
                                fontWeight: FontWeight.w600,
                                color: Colors.grey.shade500,
                              ),
                            ),
                            const SizedBox(width: 4),
                            Icon(
                              Icons.delete_outline_rounded,
                              size: 15,
                              color: Colors.grey.shade500,
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 14),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: _history.map((term) {
                      return GestureDetector(
                        onTap: () {
                          _controller.text = term;
                          _doSearch(term);
                        },
                        child: _Chip(label: term),
                      );
                    }).toList(),
                  ),
                  const SizedBox(height: 28),
                ],

                // Search Discovery section
                if (_showHistory) ...[
                  Row(
                    children: [
                      const Text(
                        'Search Discovery',
                        style: TextStyle(
                          fontSize: 15,
                          fontWeight: FontWeight.w800,
                          color: Color(0xFF111827),
                        ),
                      ),
                      const Spacer(),
                      GestureDetector(
                        onTap: () {},
                        child: Text(
                          'Hide',
                          style: TextStyle(
                            fontSize: 12.5,
                            fontWeight: FontWeight.w600,
                            color: Colors.grey.shade500,
                          ),
                        ),
                      ),
                      const SizedBox(width: 4),
                      Icon(
                        Icons.visibility_off_outlined,
                        size: 15,
                        color: Colors.grey.shade500,
                      ),
                    ],
                  ),
                  const SizedBox(height: 14),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: _discoveryTerms.map((term) {
                      return GestureDetector(
                        onTap: () {
                          _controller.text = term;
                          _doSearch(term);
                        },
                        child: _Chip(label: term, isDiscovery: true),
                      );
                    }).toList(),
                  ),
                ],

                // Show "no history yet" if empty
                if (_history.isEmpty && _showHistory) ...[
                  const SizedBox(height: 60),
                  Center(
                    child: Column(
                      children: [
                        Icon(
                          Icons.manage_search_rounded,
                          size: 52,
                          color: _accentLight.withValues(alpha: 0.5),
                        ),
                        const SizedBox(height: 14),
                        const Text(
                          'No search history yet',
                          style: TextStyle(
                            fontSize: 15,
                            fontWeight: FontWeight.w700,
                            color: Color(0xFF6B7280),
                          ),
                        ),
                        const SizedBox(height: 6),
                        const Text(
                          'Your recent searches will appear here.',
                          style: TextStyle(
                            fontSize: 13,
                            color: Color(0xFF9CA3AF),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _Chip extends StatelessWidget {
  final String label;
  final bool isDiscovery;

  const _Chip({required this.label, this.isDiscovery = false});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 7),
      decoration: BoxDecoration(
        color: isDiscovery
            ? const Color(0xFFF3F4F6)
            : Colors.white,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: isDiscovery
              ? const Color(0xFFE5E7EB)
              : const Color(0xFFD1D5DB),
        ),
      ),
      child: Text(
        label,
        style: TextStyle(
          fontSize: 13,
          fontWeight: FontWeight.w600,
          color: isDiscovery
              ? const Color(0xFF374151)
              : const Color(0xFF111827),
        ),
      ),
    );
  }
}
