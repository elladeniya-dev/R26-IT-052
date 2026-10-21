import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../core/responsive.dart';
import '../../core/support_info.dart';
import '../../core/theme.dart';

class HelpCenterScreen extends StatelessWidget {
  const HelpCenterScreen({super.key});

  static const List<({IconData icon, String title, String body})> _tips = [
    (
      icon: Icons.tune_rounded,
      title: 'Keep your preferences current',
      body:
          'Update styles, colours and brands in My Preferences whenever your '
          'taste changes.',
    ),
    (
      icon: Icons.bookmark_border_rounded,
      title: 'Save what you love, dislike the rest',
      body:
          'Tap Save on a piece you like and Dislike on ones you don\'t '
          'want. OutfitIQ learns from both.',
    ),
    (
      icon: Icons.trending_up_rounded,
      title: 'Check Trending',
      body:
          'See what Sri Lankan stores are stocking more of right now, '
          'matched to your style.',
    ),
  ];

  static const List<({String question, String answer})> _faqs = [
    (
      question: 'How does OutfitIQ choose my recommendations?',
      answer:
          'Each product gets a match score that blends three things: how well '
          'it fits your saved preferences, how similar it is to your taste '
          'according to our language model, and the quality of the product '
          'listing. Your preferences carry the most weight, and the app keeps '
          'learning from what you save, dislike and open.',
    ),
    (
      question: 'What does the Trending tab show?',
      answer:
          'It highlights colours, fabrics and garment types that Sri Lankan '
          'fashion stores are listing more of over the next few days, then '
          'shows pieces from your recommendations that match. It reflects '
          'what stores are stocking, not a guarantee of what will sell.',
    ),
    (
      question: 'What do the match percentage and confidence labels mean?',
      answer:
          'The percentage is how well a product fits you. The trend '
          'confidence (High, Medium or Low) is how strong the trend signal '
          'is. High has been right more often than Low, but no label is a '
          'promise.',
    ),
    (
      question: 'Can I undo a save or dislike?',
      answer:
          'Not yet. Each tap is recorded so the app can learn. If you change '
          'your mind, tap the opposite action and that becomes your latest '
          'choice for the item.',
    ),
    (
      question: 'Why do I see few or repeated products?',
      answer:
          'Recommendations are limited to products that match your '
          'preferences and filters. Try a wider price range, choose "All" '
          'under Explore styles, or add more styles and colours in My '
          'Preferences.',
    ),
    (
      question: 'Where do products and prices come from?',
      answer:
          'From Sri Lankan fashion retailers. Prices are in LKR and '
          'availability can change on the store\'s site, so check the store '
          'page before you buy. "Open store page" takes you to the '
          'retailer.',
    ),
    (
      question: 'How do trending picks notifications work?',
      answer:
          'On Android, if you allowed notifications, OutfitIQ can show '
          'trending pieces picked for you. You can turn them off any time in '
          'your phone\'s app settings.',
    ),
    (
      question: 'How do I change or delete my data?',
      answer:
          'Edit what the app knows about you in Profile > My Preferences. To '
          'remove your account and saved data permanently, use Profile > '
          'Delete Account. This cannot be undone.',
    ),
    (
      question: 'The app is slow or something looks wrong.',
      answer:
          'Pull down to refresh, check your connection and make sure you are '
          'on the latest version. If it continues, email us with what you '
          'did, your device and a screenshot.',
    ),
  ];

  Future<void> _emailSupport(BuildContext context) async {
    final Uri uri = Uri.parse(
      'mailto:${SupportInfo.email}'
      '?subject=${Uri.encodeComponent(SupportInfo.emailSubject)}'
      '&body=${Uri.encodeComponent(SupportInfo.emailBody)}',
    );

    bool opened = false;
    try {
      opened = await launchUrl(uri);
    } catch (_) {
      opened = false;
    }

    // No mail app (common on web and desktop): copy the address instead.
    if (!opened && context.mounted) {
      await _copyEmail(context);
    }
  }

  Future<void> _copyEmail(BuildContext context) async {
    bool copied = true;
    try {
      await Clipboard.setData(const ClipboardData(text: SupportInfo.email));
    } catch (_) {
      copied = false;
    }
    if (!context.mounted) return;

    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(
        SnackBar(
          content: Text(
            copied
                ? 'Email address copied.'
                : 'Email us at ${SupportInfo.email}',
          ),
        ),
      );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundColor,
      body: ResponsiveCenter(
        maxWidth: 760,
        child: SafeArea(
          child: Column(
            children: [
              _buildHeader(context),
              Expanded(
                child: ListView(
                  padding: const EdgeInsets.fromLTRB(18, 8, 18, 24),
                  children: [
                    _buildIntroCard(),
                    const SizedBox(height: 22),
                    _sectionTitle('Quick tips'),
                    const SizedBox(height: 10),
                    for (final tip in _tips) _buildTip(tip),
                    const SizedBox(height: 14),
                    _sectionTitle('Common questions'),
                    const SizedBox(height: 10),
                    for (final faq in _faqs) _buildFaq(faq),
                    const SizedBox(height: 14),
                    _buildContactCard(context),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildHeader(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(8, 12, 20, 8),
      child: Row(
        children: [
          IconButton(
            onPressed: () => Navigator.pop(context),
            icon: const Icon(
              Icons.arrow_back_ios_new_rounded,
              size: 20,
              color: AppTheme.darkTextColor,
            ),
          ),
          const SizedBox(width: 4),
          const Text(
            'Help Center',
            style: TextStyle(
              fontSize: 21,
              fontWeight: FontWeight.bold,
              color: AppTheme.darkTextColor,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildIntroCard() {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [AppTheme.secondaryColor, AppTheme.darkAccentColor],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(24),
      ),
      child: Row(
        children: [
          Container(
            height: 48,
            width: 48,
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: 0.16),
              borderRadius: BorderRadius.circular(16),
            ),
            child: const Icon(
              Icons.support_agent_rounded,
              color: Colors.white,
              size: 26,
            ),
          ),
          const SizedBox(width: 14),
          const Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'How can we help?',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 17,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                SizedBox(height: 4),
                Text(
                  'Answers to common questions, tips for better '
                  'recommendations, and how to reach us.',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 12.5,
                    height: 1.4,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _sectionTitle(String text) {
    return Text(
      text,
      style: const TextStyle(
        fontSize: 17,
        fontWeight: FontWeight.w700,
        color: AppTheme.darkTextColor,
      ),
    );
  }

  Widget _buildTip(({IconData icon, String title, String body}) tip) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppTheme.cardBackgroundColor,
        borderRadius: BorderRadius.circular(18),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            height: 40,
            width: 40,
            decoration: BoxDecoration(
              color: AppTheme.softHighlightColor,
              borderRadius: BorderRadius.circular(13),
            ),
            child: Icon(tip.icon, color: AppTheme.primaryColor, size: 22),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  tip.title,
                  style: const TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                    color: AppTheme.darkTextColor,
                  ),
                ),
                const SizedBox(height: 3),
                Text(
                  tip.body,
                  style: const TextStyle(
                    fontSize: 12.5,
                    height: 1.4,
                    color: AppTheme.lightTextColor,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFaq(({String question, String answer}) faq) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      decoration: BoxDecoration(
        color: AppTheme.cardBackgroundColor,
        borderRadius: BorderRadius.circular(18),
      ),
      clipBehavior: Clip.antiAlias,
      child: Theme(
        // Remove the default divider lines around an expanded tile.
        data: ThemeData(dividerColor: Colors.transparent),
        child: ExpansionTile(
          tilePadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 2),
          childrenPadding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
          expandedCrossAxisAlignment: CrossAxisAlignment.start,
          iconColor: AppTheme.primaryColor,
          collapsedIconColor: AppTheme.inactiveColor,
          title: Text(
            faq.question,
            style: const TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.w600,
              color: AppTheme.darkTextColor,
            ),
          ),
          children: [
            Text(
              faq.answer,
              style: const TextStyle(
                fontSize: 13,
                height: 1.5,
                color: AppTheme.lightTextColor,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildContactCard(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: AppTheme.cardBackgroundColor,
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: AppTheme.softHighlightColor, width: 2),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: const [
              Icon(Icons.mail_outline_rounded, color: AppTheme.primaryColor),
              SizedBox(width: 10),
              Text(
                'Still need help?',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w700,
                  color: AppTheme.darkTextColor,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          const Text(
            'Email us and include the email you signed in with, what you were '
            'doing, and a screenshot if you can. It helps us fix things '
            'faster.',
            style: TextStyle(
              fontSize: 13,
              height: 1.5,
              color: AppTheme.lightTextColor,
            ),
          ),
          const SizedBox(height: 14),
          Row(
            children: [
              Expanded(
                child: SelectableText(
                  SupportInfo.email,
                  style: const TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                    color: AppTheme.primaryColor,
                  ),
                ),
              ),
              IconButton(
                tooltip: 'Copy email address',
                onPressed: () => _copyEmail(context),
                icon: const Icon(
                  Icons.copy_rounded,
                  size: 20,
                  color: AppTheme.lightTextColor,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              onPressed: () => _emailSupport(context),
              icon: const Icon(Icons.send_rounded, size: 18),
              label: const Text('Email support'),
            ),
          ),
        ],
      ),
    );
  }
}
