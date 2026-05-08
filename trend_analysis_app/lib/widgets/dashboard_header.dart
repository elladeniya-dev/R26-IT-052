import 'package:flutter/material.dart';

class DashboardHeader extends StatelessWidget {
  const DashboardHeader({super.key});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        const Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Trend Analysis',
                style: TextStyle(
                  fontSize: 28,
                  fontWeight: FontWeight.w800,
                  color: Color(0xFF143D35),
                ),
              ),
              SizedBox(height: 4),
              Text(
                'Discover weekly fashion movements',
                style: TextStyle(
                  fontSize: 14,
                  color: Color(0xFF7A7A7A),
                ),
              ),
            ],
          ),
        ),
        Container(
          height: 46,
          width: 46,
          decoration: BoxDecoration(
            color: const Color(0xFF00796B),
            borderRadius: BorderRadius.circular(16),
          ),
          child: const Icon(
            Icons.auto_graph,
            color: Colors.white,
          ),
        ),
      ],
    );
  }
}