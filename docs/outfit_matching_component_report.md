# Outfit Matching and Clothing Style Compatibility Engine

## 1. Component Overview

The Outfit Matching and Clothing Style Compatibility Engine is the individual research component responsible for generating complete outfit recommendations based on a clothing item selected by the user. Instead of recommending only individual fashion products, this component analyses relationships between clothing items from different categories, such as tops, bottoms, dresses, outerwear, footwear, and accessories.

The main purpose of this component is to identify clothing items that complement each other and present ranked outfit combinations to the user. The system considers item attributes such as category, colour, style, occasion, price, and availability. It then calculates compatibility scores and displays outfit suggestions with explanation tags so users can understand why an outfit was recommended.

This component extends the Smart Fashion Assistant from simple product recommendation to outfit-level fashion recommendation.

## 2. System Workflow

The implemented workflow is:

```text
User selects a clothing item
-> Backend identifies complementary categories
-> Backend retrieves candidate products
-> Outfit combinations are generated dynamically
-> Compatibility score is calculated
-> Outfits are ranked by score
-> Flutter frontend displays outfit suggestions
-> User can save or rate the outfit
-> Evaluation summary and feedback report are generated
```

For example, if the user selects a top, the system searches for suitable bottoms and optional outerwear. If the user selects a dress, the system can recommend outerwear or supporting outfit items. This allows the system to generate outfits dynamically instead of depending only on predefined outfit sets.

## 3. Backend Implementation

The backend was implemented using FastAPI, SQLAlchemy, PostgreSQL-compatible models, and Python-based compatibility logic.

Main backend files:

| File | Purpose |
|---|---|
| `backend/app/s_compatibility.py` | Calculates style, colour, category, and occasion compatibility scores |
| `backend/app/s_outfit_generator.py` | Generates outfit combinations and ranks them |
| `backend/app/s_ml_predictor.py` | Applies ML-based pair compatibility scoring |
| `backend/app/s_outfit_storage.py` | Stores generated and saved outfit records |
| `backend/app/s_outfit_feedback.py` | Stores outfit feedback and produces evaluation summaries |
| `backend/app/routers/outfit_router.py` | Provides outfit generation API endpoints |
| `backend/app/routers/outfit_feedback_router.py` | Provides feedback, summary, and report API endpoints |

### 3.1 Compatibility Scoring

The compatibility score is calculated using a hybrid approach:

```text
Final compatibility score =
rule-based compatibility score + ML compatibility score
```

The rule-based score considers:

- Style match
- Colour match
- Category structure
- Occasion suitability

The ML score is calculated using pairwise item compatibility. For a full outfit, the system compares every item pair and averages the predicted pair compatibility scores.

The frontend displays user-friendly score information such as style, colour, category, and occasion scores. Internal implementation scores such as rule-based score and ML score are not displayed to users.

### 3.2 Outfit Generation

The outfit generation process works as follows:

1. The selected item is retrieved from the product database.
2. The system identifies required and optional complementary categories.
3. Candidate products are retrieved according to category and filters.
4. Candidate products are ranked against the selected item.
5. Outfit combinations are generated.
6. Each outfit receives a compatibility score.
7. Outfits are sorted from highest score to lowest score.
8. The top ranked outfits are returned to the frontend.

Supported filters include:

- Occasion
- Minimum price
- Maximum price
- Preferred colours
- Excluded categories
- Maximum items per category

## 4. Frontend Implementation

The frontend was implemented using Flutter. It allows the user to view products, select an item, generate compatible outfits, inspect outfit details, save outfits, rate outfits, and view evaluation results.

Main frontend files:

| File | Purpose |
|---|---|
| `frontend/lib/screens/s_complete_the_look_screen.dart` | Displays generated outfit recommendations |
| `frontend/lib/widgets/s_outfit_card.dart` | Shows each outfit card with score, reason tags, save, details, and feedback buttons |
| `frontend/lib/screens/s_outfit_detail_screen.dart` | Shows detailed outfit items, score breakdown, filters, save, generate again, and feedback |
| `frontend/lib/screens/s_saved_outfits_screen.dart` | Displays saved outfits |
| `frontend/lib/screens/s_evaluation_summary_screen.dart` | Displays feedback-based evaluation results |
| `frontend/lib/services/s_outfit_api_service.dart` | Sends outfit generation requests |
| `frontend/lib/services/s_outfit_feedback_api_service.dart` | Sends feedback and loads evaluation summary |

### 4.1 User Interface Features

The frontend includes:

- Selected product display
- Occasion selection
- Price and colour filters
- Generated outfit cards
- Compatibility percentage
- Explanation reason tags
- Score breakdown
- Save outfit button
- Generate again button
- Good / Okay / Bad feedback buttons
- Evaluation summary dashboard

## 5. API Endpoints

The following endpoints support this component:

| Endpoint | Method | Purpose |
|---|---|---|
| `/outfits/generate` | POST | Generate ranked outfit combinations |
| `/outfits/latest/{user_id}` | GET | Get latest generated outfit batch |
| `/saved-outfits/save/{outfit_id}` | POST | Save an outfit |
| `/saved-outfits/{user_id}` | GET | Get saved outfits |
| `/outfits/{outfit_id}/feedback` | POST | Save user feedback for an outfit |
| `/outfits/feedback/{user_id}` | GET | Get all feedback records for a user |
| `/outfits/feedback-summary/{user_id}` | GET | Get evaluation summary |
| `/outfits/feedback-report/{user_id}` | GET | Get report-ready feedback data |

## 6. Evaluation Method

The component is evaluated using both system testing and user feedback.

### 6.1 Functional Testing

The backend tests verify:

- Compatibility score calculation
- Style conflict detection
- Duplicate category penalty
- Outfit generation and ranking
- Preferred colour filtering
- Saved outfit storage
- Feedback saving
- Feedback summary calculation
- Feedback report generation

The latest backend test result:

```text
10 passed, 1 warning
```

The Flutter frontend analysis result:

```text
No issues found
```

### 6.2 User Feedback Evaluation

Users can rate generated outfits using:

```text
Good
Okay
Bad
```

These ratings are stored in the backend and used to calculate:

- Total feedback count
- Average rating
- Good match count
- Okay match count
- Bad match count
- Rating distribution
- Good match ratio

The evaluation summary can be viewed inside the Flutter application through the Evaluation screen. A report-ready version can also be retrieved from:

```text
GET /outfits/feedback-report/USR001
```

## 7. Sample Test Case Table

| Test Case | Selected Item | Occasion | Expected Output | Result |
|---|---|---|---|---|
| TC01 | Black Casual Crop Top | Casual | Casual bottom and optional outerwear | Pass |
| TC02 | White Formal Shirt | Office | Formal bottom and blazer-style outerwear | Pass |
| TC03 | Red Party Dress | Party | Dress-based outfit with suitable outerwear | Pass |
| TC04 | Casual Top with formal occasion | Formal | Lower score for weak style match | Pass |
| TC05 | Outfit feedback submission | Any generated outfit | Feedback saved successfully | Pass |
| TC06 | Evaluation summary | Rated outfits | Summary values are displayed | Pass |

## 8. Screenshots To Include

Add the following screenshots to the final report:

1. Product list screen
2. Product detail screen
3. Complete the Look screen
4. Generated outfit cards
5. Outfit detail screen
6. Feedback buttons
7. Saved outfits screen
8. Evaluation summary screen

## 9. Results Summary Template

Use the feedback report endpoint and fill this table after collecting user feedback:

| Metric | Value |
|---|---|
| Total feedback count |  |
| Average rating |  |
| Good matches |  |
| Okay matches |  |
| Bad matches |  |
| Good match ratio |  |

## 10. Demonstration Script

The following short script can be used during the project demonstration:

```text
My component is the Outfit Matching and Clothing Style Compatibility Engine.

The user selects a clothing item, and the backend identifies complementary categories for that item. The system retrieves candidate products, generates outfit combinations, calculates compatibility scores, and ranks the outfits.

The Flutter application displays the recommended outfits with compatibility percentage and explanation tags. The user can open outfit details, save outfits, generate another set of recommendations, and rate outfits as Good, Okay, or Bad.

The feedback ratings are stored in the backend and shown in the Evaluation Summary screen. This provides measurable research evidence for the quality of generated outfit recommendations.
```

## 11. Limitations

The current implementation has the following limitations:

- The quality of outfit recommendations depends on the size and quality of the clothing dataset.
- Rule-based compatibility may not fully capture subjective fashion preferences.
- The ML compatibility score depends on the quality of the trained model and available training data.
- The current feedback system uses simple Good / Okay / Bad inputs, which may not capture detailed user preferences.
- Image-based visual feature extraction is limited compared with deep fashion vision models.

## 12. Future Work

Future improvements can include:

- Training the compatibility model with a larger fashion outfit dataset.
- Adding image-based feature extraction using deep learning.
- Personalizing outfit ranking using user profile and interaction history.
- Integrating trend analysis scores into outfit ranking.
- Adding seasonal and weather-aware outfit recommendations.
- Adding more detailed feedback options such as colour issue, style issue, price issue, or category mismatch.
- Exporting evaluation results as CSV or PDF for research documentation.

## 13. Conclusion

The Outfit Matching and Clothing Style Compatibility Engine successfully extends the Smart Fashion Assistant from individual product recommendation to complete outfit recommendation. The implemented system can generate dynamic outfit combinations, calculate compatibility scores, rank outfit suggestions, explain recommendation reasons, collect user feedback, and produce evaluation summaries.

This component contributes to the overall research project by improving decision support in online fashion shopping and helping users identify clothing items that work well together as complete outfits.
