import 'package:flutter/material.dart';

import '../../core/theme.dart';
import '../../services/onboarding_service.dart';
import '../home/home_screen.dart';

class OnboardingScreen extends StatefulWidget {
  const OnboardingScreen({super.key});

  @override
  State<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends State<OnboardingScreen> {
  final OnboardingService _onboardingService = OnboardingService();

  int _currentStep = 0;
  bool _isSubmitting = false;

  final Set<String> _selectedCategories = {};
  final Set<String> _selectedColors = {};
  final Set<String> _selectedStyles = {};
  final Set<String> _selectedOccasions = {};
  final Set<String> _selectedPatterns = {};
  String? _selectedBudget;

  final List<String> _categories = [
    'Tops',
    'T-shirts',
    'Shirts',
    'Dresses',
    'Jeans',
    'Trousers',
    'Skirts',
    'Shorts',
    'Jackets',
    'Blazers',
    'Sweaters',
    'Hoodies',
    'Leggings',
  ];

  final List<String> _colors = [
    'Black',
    'White',
    'Blue',
    'Beige',
    'Pink',
    'Red',
    'Green',
    'Grey',
    'Brown',
    'Yellow',
    'Purple',
    'Orange',
    'Navy',
    'Cream',
  ];

  final List<String> _styles = [
    'Casual',
    'Formal',
    'Trendy',
    'Classic',
    'Sporty',
    'Elegant',
    'Streetwear',
    'Minimal',
    'Party wear',
    'Comfort wear',
    'Modest',
  ];

  final List<String> _occasions = [
    'Daily wear',
    'Office / work',
    'University / college',
    'Party',
    'Casual outing',
    'Sports / gym',
    'Travel',
    'Special events',
  ];

  final List<String> _budgets = [
    'Below 2,000 LKR',
    '2,000 - 5,000 LKR',
    '5,000 - 10,000 LKR',
    '10,000 - 20,000 LKR',
    'Above 20,000 LKR',
  ];

  final List<String> _patterns = [
    'Plain / solid',
    'Floral',
    'Striped',
    'Checked',
    'Printed',
    'Graphic',
    'Polka dot',
    'Animal print',
  ];

  bool get _canGoNext {
    switch (_currentStep) {
      case 0:
        return _selectedCategories.isNotEmpty;
      case 1:
        return _selectedColors.isNotEmpty;
      case 2:
        return _selectedStyles.isNotEmpty;
      case 3:
        return _selectedOccasions.isNotEmpty;
      case 4:
        return _selectedBudget != null;
      case 5:
        return _selectedPatterns.isNotEmpty;
      default:
        return false;
    }
  }

  String get _stepTitle {
    switch (_currentStep) {
      case 0:
        return 'What type of clothing do you usually prefer?';
      case 1:
        return 'Which colors do you like most?';
      case 2:
        return 'What fashion styles match you?';
      case 3:
        return 'What occasions do you dress for?';
      case 4:
        return 'What is your usual budget range?';
      case 5:
        return 'What patterns do you prefer?';
      default:
        return '';
    }
  }

  List<String> get _currentOptions {
    switch (_currentStep) {
      case 0:
        return _categories;
      case 1:
        return _colors;
      case 2:
        return _styles;
      case 3:
        return _occasions;
      case 4:
        return _budgets;
      case 5:
        return _patterns;
      default:
        return [];
    }
  }

  Set<String> get _currentSelectedSet {
    switch (_currentStep) {
      case 0:
        return _selectedCategories;
      case 1:
        return _selectedColors;
      case 2:
        return _selectedStyles;
      case 3:
        return _selectedOccasions;
      case 5:
        return _selectedPatterns;
      default:
        return {};
    }
  }

  void _toggleOption(String option) {
    setState(() {
      if (_currentStep == 4) {
        _selectedBudget = option;
        return;
      }

      final selectedSet = _currentSelectedSet;

      if (selectedSet.contains(option)) {
        selectedSet.remove(option);
      } else {
        selectedSet.add(option);
      }
    });
  }

  bool _isSelected(String option) {
    if (_currentStep == 4) {
      return _selectedBudget == option;
    }

    return _currentSelectedSet.contains(option);
  }

  Future<void> _goNext() async {
  if (!_canGoNext || _isSubmitting) {
    return;
  }

  if (_currentStep < 5) {
    setState(() {
      _currentStep++;
    });
    return;
  }

  setState(() {
    _isSubmitting = true;
  });

  try {
    await _onboardingService.submitOnboarding(
      preferredCategories: _selectedCategories.toList(),
      preferredColors: _selectedColors.toList(),
      preferredStyles: _selectedStyles.toList(),
      occasions: _selectedOccasions.toList(),
      budgetRange: _selectedBudget!,
      preferredPatterns: _selectedPatterns.toList(),
    );

    if (!mounted) {
      return;
    }

    ScaffoldMessenger.of(context).showSnackBar(
  const SnackBar(
    content: Text('Preferences saved successfully.'),
  ),
);

Navigator.pushReplacement(
  context,
  MaterialPageRoute(
    builder: (context) => HomeScreen(),
  ),
);

  } catch (e) {
    if (!mounted) {
      return;
    }

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(e.toString()),
      ),
    );
  } finally {
    if (mounted) {
      setState(() {
        _isSubmitting = false;
      });
    }
  }
}

  void _goBack() {
    if (_currentStep == 0) {
      Navigator.pop(context);
    } else {
      setState(() {
        _currentStep--;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final options = _currentOptions;

    return Scaffold(
      backgroundColor: Colors.white,
      body: SafeArea(
        child: Column(
          children: [
            _buildHeader(),
            _buildProgressSection(),
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.symmetric(horizontal: 12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const SizedBox(height: 26),
                    Text(
                      _stepTitle,
                      style: const TextStyle(
                        fontSize: 23,
                        height: 1.25,
                        fontWeight: FontWeight.bold,
                        color: AppTheme.darkTextColor,
                      ),
                    ),
                    const SizedBox(height: 26),
                    _buildOptionsGrid(options),
                    const SizedBox(height: 24),
                  ],
                ),
              ),
            ),
            _buildBottomButton(),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader() {
    return Padding(
      padding: const EdgeInsets.fromLTRB(12, 12, 18, 8),
      child: Row(
        children: [
          IconButton(
            onPressed: _goBack,
            icon: const Icon(
              Icons.arrow_back_ios_new,
              size: 20,
              color: AppTheme.darkTextColor,
            ),
          ),
          const SizedBox(width: 4),
          const Text(
            'Preferences',
            style: TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.bold,
              color: AppTheme.darkTextColor,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildProgressSection() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: List.generate(6, (index) {
              final bool isActive = index <= _currentStep;

              return Expanded(
                child: Container(
                  height: 4,
                  margin: EdgeInsets.only(
                    right: index == 5 ? 0 : 5,
                  ),
                  decoration: BoxDecoration(
                    color: isActive
                        ? AppTheme.primaryColor
                        : const Color(0xFFE5E7EB),
                    borderRadius: BorderRadius.circular(10),
                  ),
                ),
              );
            }),
          ),
          const SizedBox(height: 10),
          Text(
            'Step ${_currentStep + 1} of 6',
            style: const TextStyle(
              fontSize: 13,
              color: AppTheme.lightTextColor,
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildOptionsGrid(List<String> options) {
    return GridView.builder(
      itemCount: options.length,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 2,
        crossAxisSpacing: 12,
        mainAxisSpacing: 12,
        childAspectRatio: 3.25,
      ),
      itemBuilder: (context, index) {
        final option = options[index];
        final selected = _isSelected(option);

        return GestureDetector(
          onTap: () => _toggleOption(option),
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 180),
            alignment: Alignment.center,
            decoration: BoxDecoration(
              color: selected
                  ? AppTheme.primaryColor.withOpacity(0.12)
                  : Colors.white,
              borderRadius: BorderRadius.circular(14),
              border: Border.all(
                color: selected
                    ? AppTheme.primaryColor
                    : const Color(0xFFE5E7EB),
                width: selected ? 1.6 : 1,
              ),
            ),
            child: Text(
              option,
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 14,
                fontWeight: selected ? FontWeight.w700 : FontWeight.w500,
                color: selected
                    ? AppTheme.primaryColor
                    : AppTheme.darkTextColor,
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _buildBottomButton() {
    return Container(
      padding: const EdgeInsets.fromLTRB(12, 16, 12, 18),
      decoration: const BoxDecoration(
        color: Colors.white,
        border: Border(
          top: BorderSide(
            color: Color(0xFFE5E7EB),
            width: 1,
          ),
        ),
      ),
      child: SizedBox(
        width: double.infinity,
        height: 54,
        child: ElevatedButton(
          onPressed: _canGoNext ? _goNext : null,
          style: ElevatedButton.styleFrom(
            backgroundColor: AppTheme.primaryColor,
            disabledBackgroundColor: AppTheme.primaryColor.withOpacity(0.35),
            foregroundColor: Colors.white,
            disabledForegroundColor: Colors.white,
            elevation: 0,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(28),
            ),
          ),
          
          child: _isSubmitting
    ? const SizedBox(
        width: 22,
        height: 22,
        child: CircularProgressIndicator(
          strokeWidth: 2.4,
          color: Colors.white,
        ),
      )
    : Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(
            _currentStep == 5 ? 'Finish' : 'Next',
            style: const TextStyle(
              fontSize: 15,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(width: 8),
          Icon(
            _currentStep == 5
                ? Icons.check_rounded
                : Icons.arrow_forward_ios_rounded,
            size: 16,
          ),
        ],
      ),
        ),
      ),
    );
  }
}