# OutfitIQ - Smart Fashion Assistant

OutfitIQ is a mobile-based Smart Fashion Assistant system that recommends suitable fashion products to users based on their preferences, product details, and recommendation scores.

This project is part of the Final Year Research Project:

**Smart Fashion Assistant: Intelligent Personalized and Trend-Aware Fashion Recommendation System**

The system is not a direct e-commerce platform. It helps users discover suitable fashion products and redirects them to the original online store page for purchasing.

---

## Component Overview

This component focuses on:

**Data Collection / Web Crawling + Recommendation Engine + Flutter Frontend Integration**

The main purpose of this component is to collect real fashion product data from online fashion stores, store the collected data in a shared PostgreSQL database, and recommend suitable products to users through a Flutter mobile application.

---

## Main Features

- Collects fashion product data from selected online fashion websites
- Stores product details in PostgreSQL database
- Supports product details such as:
  - Product title
  - Category
  - Subcategory
  - Color
  - Style
  - Brand
  - Price
  - Currency
  - Image URL
  - Product URL
  - Source website
  - Description
  - Availability
- Generates product recommendations based on user preferences
- Uses a hybrid recommendation scoring method
- Includes ML-based semantic similarity scoring
- Displays recommendation scores in the Flutter mobile app
- Provides explainable recommendation reason tags
- Allows users to open the original product page from the store

---

## Technologies Used

### Frontend

- Flutter
- Dart
- HTTP package
- Cached Network Image
- URL Launcher
- Google Fonts

### Backend

- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- Uvicorn

### Machine Learning

- Sentence Transformers
- Pre-trained embedding model
- Cosine similarity

### Database

- PostgreSQL

### Testing Tools

- Swagger UI
- Browser testing
- iPhone physical device testing

---

## System Architecture

The system follows this flow:

```text
Flutter Mobile App
        ↓
FastAPI Backend
        ↓
Recommendation Engine
        ↓
PostgreSQL Database
        ↓
Crawled Product Data