# OutfitIQ - Smart Fashion Assistant

## Project Title

**Smart Fashion Assistant: Intelligent Personalized and Trend-Aware Fashion Recommendation System**

## Project Overview

OutfitIQ is a mobile-based smart fashion assistant developed as a Final Year Research Project. The system provides personalized fashion recommendations and outfit suggestions based on user preferences, user behavior, fashion trends, and outfit compatibility.

The application does not directly sell products. Instead, it recommends suitable clothing items and redirects users to the original external fashion store through product links.

The system is divided into four main research components. Each component focuses on a separate intelligent function of the complete fashion assistant system. All components are integrated using a shared backend and PostgreSQL database.

## Group Members

| Student ID | Name                |
| ---------- | ------------------- |
| IT22189608 | Kojitha Gunathilake |
| IT22247636 | Chalani Ramanayake  |
| IT22202840 | Givindu Elladeniya  |
| IT22218476 | Senuja Rajapaksha   |

## Main Components

The system consists of four main components:

1. User Management and User Learning Engine
2. Data Collection and Recommendation Engine
3. Trend Analysis Engine
4. Outfit Compatibility Engine

# 1. User Preference Analysis & Dynamic Modeling Engine (ML)

## Component Owner

**IT22247636 | Chalani Ramanayake**

## Component Overview

This component handles user authentication, onboarding, profile management, interaction tracking, and dynamic user preference learning.

The main purpose of this component is to understand each user's fashion preferences and improve those preferences over time based on user behavior in the application.

## Main Responsibilities

- Manage user authentication using Google Sign-In.
- Store user profile details.
- Collect initial fashion preferences through onboarding.
- Track user interactions with fashion items.
- Dynamically update user preference weights.
- Provide learned user preference data to the recommendation engine.

## Key Features

### Google Sign-In Authentication

Users can log in to the system using their Google account. The frontend receives a Google ID token and sends it to the backend. The backend verifies the token and creates or retrieves the relevant user account.

### User Onboarding

After login, users answer onboarding questions related to their fashion preferences.

Example onboarding data includes:

- Preferred clothing categories
- Favorite colors
- Preferred fashion styles
- Dressing occasions
- Brand preferences
- Important factors when choosing clothes

### User Profile Management

The system stores and manages user details such as full name, email, onboarding preferences, and learned preferences.

### User Interaction Tracking

The system records user behavior when users interact with recommended fashion items.

Example interaction types:

| Interaction Type | Meaning |
|---|---|
| View | User viewed an item |
| Click | User clicked an item |
| Save | User saved an item |
| Select | User selected an item |
| Dislike | User disliked an item |

### Dynamic User Learning

The learning engine updates user preference weights based on interaction behavior.

For example, if a user frequently views and saves black casual tops, the system increases the user's preference weights for:

- Category: Tops
- Color: Black
- Style: Casual

This allows the system to provide more personalized recommendations over time.

## Related Database Tables

- users
- user_onboarding_preferences
- user_interactions
- user_learned_preferences

## Example Output

Example learned user preference output:

- User ID: 1
- Category preference: Tops = 0.9, Dresses = 0.4
- Color preference: Black = 1.0, White = 0.7
- Style preference: Casual = 0.8, Formal = 0.3

# 2. Intelligent Web Crawling Module for Personalized Fashion Data (ML + Data Mining)

## Component Owner

**IT22189608 | Kojitha Gunathilake**

## Component Overview

This component is responsible for collecting fashion product data from online sources and generating personalized product recommendations for users.

The recommendation engine uses user preferences, learned behavior, trend signals, and product quality to rank fashion items.

## Main Responsibilities

- Collect product data from online fashion websites.
- Store product details in the shared database.
- Read user preference data from the database.
- Read trend signal data from the trend analysis component.
- Calculate recommendation scores.
- Return ranked fashion recommendations to the frontend.

## Key Features

### Product Data Collection

The system collects clothing product information from external fashion stores.

Collected product details may include:

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
- Availability
- Collected date

### Product Storage

Collected products are stored in the shared PostgreSQL database so that other components can also use them.

### Personalized Recommendation

The recommendation engine recommends products based on:

- User onboarding preferences
- Learned user preferences
- User interaction behavior
- Current trend scores
- Product quality

### Recommendation Score Calculation

The recommendation engine calculates a final score for each product.

Example scoring formula:

final_score = 0.50 * user_match_score + 0.20 * behavior_score + 0.20 * trend_score + 0.10 * product_quality_score

### User Match Score

The user match score checks how well a product matches the user's preferences.

Example checks:

- Product category matches the user's preferred category.
- Product color matches the user's preferred color.
- Product style matches the user's preferred style.
- Product brand matches the user's preferred brand.

### Behavior Score

The behavior score uses the user's past interactions to improve recommendation ranking.

Example interaction weights:

| Interaction Type | Example Weight |
|---|---|
| View | 1 |
| Click | 2 |
| Save | 4 |
| Select | 5 |
| Dislike | -3 |

### Trend Score

The trend score uses trend signals generated by the Trend Analysis Engine.

For example, if oversized clothing is currently trending, products with the oversized style may receive a higher trend score.

### Product Quality Score

The product quality score checks whether product data is complete and useful.

Example checks:

- Product has an image.
- Product has a valid product URL.
- Product has a price.
- Product is available.

## Related Database Tables

- products
- users
- user_onboarding_preferences
- user_interactions
- user_learned_preferences
- trend_signals

## Example Output

Example recommendation output:

- User ID: 1
- Recommended item: Black Casual Shirt
- Category: Tops
- Color: Black
- Style: Casual
- Final score: 0.87
- Product URL: External store product link

# 3. Trend Analysis & Trend–Preference Fusion Engine (ML)

## Component Owner

**IT22202840 | Givindu Elladeniya**

## Component Overview

This component analyzes fashion product data and identifies current or growing fashion trends.

The main purpose of this component is to make the recommendation system trend-aware. This helps users receive suggestions that are not only personalized but also relevant to current fashion trends.

## Main Responsibilities

- Analyze collected product data.
- Identify trending fashion attributes.
- Calculate trend scores.
- Calculate growth rates over a selected time period.
- Store trend signals in the shared database.
- Provide trend data to the recommendation engine and frontend.

## Key Features

### Fashion Trend Detection

The system checks product attributes to identify what is currently popular.

Example trend attributes:

- Category
- Color
- Style
- Brand
- Material
- Pattern

### Weekly Trend Analysis

The trend engine can analyze changes over time, such as weekly growth in product availability or popularity.

For example, if the number of products with the style "Oversized" increases this week compared to last week, the trend engine can identify it as a growing trend.

### Trend Score Calculation

A trend score is calculated to represent how strong a fashion trend is.

The trend score can be based on:

- Attribute frequency
- Recent popularity
- Growth rate
- Time window

### Growth Rate Calculation

Growth rate measures how much a fashion attribute has increased or decreased over time.

Example formula:

growth_rate = (current_period_count - previous_period_count) / previous_period_count

### ML-Based Trend Classification

The component can use machine learning to classify or predict trend behavior.

Example trend labels:

- Rising trend
- Stable trend
- Declining trend

### Trend Signal Storage

Generated trend results are stored in the database as trend signals. These trend signals can then be used by the recommendation engine and frontend.

## Related Database Tables

- products
- trend_signals

## Example Output

Example trend signal output:

- Trend ID: 1
- Attribute type: Style
- Attribute value: Oversized
- Trend score: 0.91
- Growth rate: 0.35
- Time window: Weekly
- Status: Rising

# 4. Outfit Matching & Clothing Style Compatibility Engine (ML)

## Component Owner

**IT22218476 | Senuja Rajapaksha**

## Component Overview

This component generates complete outfit suggestions based on a selected fashion item.

The main purpose of this component is to help users create matching outfits instead of recommending only single clothing items.

## Main Responsibilities

- Accept a selected fashion item from the user.
- Find compatible fashion items from the product database.
- Check color compatibility.
- Check style compatibility.
- Check category compatibility.
- Check occasion suitability.
- Apply optional user filters.
- Generate complete outfit combinations.
- Allow users to save, remove, and reuse outfit combinations.

## Key Features

### Selected Item-Based Outfit Generation

The user selects one fashion item, and the outfit compatibility engine generates matching outfit combinations around that item.

For example, if the user selects a black casual top, the system may suggest:

- Matching jeans
- Matching shoes
- Matching accessories

### Color Compatibility

The engine checks whether item colors match well together.

Example:

- Black can match with white, grey, blue, beige, and other neutral colors.
- Neutral colors can match with many outfit combinations.

### Style Compatibility

The engine checks whether the styles of selected items are suitable together.

Example:

- Casual top + casual jeans + sneakers
- Formal shirt + formal trousers + formal shoes

### Category Compatibility

The engine avoids unsuitable category combinations and builds proper outfit structures.

Example outfit structure:

- Top
- Bottom
### Occasion Suitability

The engine checks whether the generated outfit is suitable for the selected occasion.

Example occasions:

- Casual
- Formal
- Party
- Office

### User Filters

Users can apply filters when generating outfits.

Example filters:

- Minimum price
- Maximum price
- Preferred colors
- Excluded categories
- Maximum number of outfits
- Maximum items per category

### Saved Outfits

Users can save outfit combinations they like and view them later.

Saved outfit features include:

- Save liked outfit
- View saved outfit list
- Remove saved outfit
- Reuse saved outfit

## Related Database Tables

- products
- saved_outfits

## Example Output

Example generated outfit output:

- Selected item: Black Casual Top
- Suggested bottom: Blue Denim Jeans
- Outfit score: 0.89

# Component Integration

All four components are connected through the same backend and shared PostgreSQL database.

System integration flow:

1. User logs in using Google Sign-In.
2. User completes onboarding preferences.
3. Product data is collected from fashion websites.
4. Trend Analysis Engine analyzes product data and generates trend signals.
5. User interactions are tracked in the mobile app.
6. User Learning Engine updates learned preference weights.
7. Recommendation Engine reads user data, product data, interaction data, and trend signals.
8. Recommendation Engine returns ranked product recommendations.
9. User selects a fashion item.
10. Outfit Compatibility Engine generates matching outfit combinations.
11. User can save, remove, or reuse outfit combinations.

# Shared Database

The project uses a shared PostgreSQL database named:

fashion_assistant

## Main Shared Tables

- users
- user_onboarding_preferences
- user_interactions
- user_learned_preferences
- products
- trend_signals
- saved_outfits

# Technology Stack

## Frontend Technologies

- Flutter
- Dart
- Google Sign-In
- REST API integration

## Backend Technologies

- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- Uvicorn

## Machine Learning and Intelligence

- Fashion embeddings
- Similarity scoring
- User preference weighting
- Trend classification
- Recommendation scoring
- Rule-based outfit compatibility

## Development Tools

- Visual Studio Code
- Postman
- pgAdmin
- GitHub
- GitHub Desktop
- Google Colab
- Microsoft Planner

# Final Output of the System

The final system provides:

- Personalized fashion recommendations
- Trend-aware product suggestions
- Behavior-based user learning
- Compatible outfit generation
- Saved outfit management
- External product store redirection

# Academic Purpose

This project is developed as a Final Year Research Project for academic and research purposes.