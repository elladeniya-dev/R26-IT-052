# Outfit Matching Demo and Submission Guide

## 1. Final Demo Flow

Use this flow during the project demonstration:

```text
1. Open the Smart Fashion Assistant app.
2. Select a clothing item from the product list.
3. Open the product detail screen.
4. Tap Complete the Look.
5. Show the generated outfit suggestions.
6. Point out compatibility percentage and reason tags.
7. Open an outfit detail screen.
8. Show the item list and score breakdown.
9. Rate the outfit as Good, Okay, or Bad.
10. Save one outfit.
11. Open the Evaluation Summary screen.
12. Show feedback count, average rating, and Good / Okay / Bad counts.
```

## 2. Short Presentation Script

You can use this script for a 1-2 minute explanation:

```text
My individual component is the Outfit Matching and Clothing Style Compatibility Engine.

The user first selects a clothing item. Based on that selected item, the backend identifies complementary clothing categories, such as bottoms for a top or outerwear for a dress.

The system then retrieves candidate products from the clothing dataset and generates outfit combinations dynamically. Each generated outfit is evaluated using compatibility scoring based on style, colour, category structure, occasion suitability, and model-based compatibility.

The highest scoring outfits are ranked and displayed in the Flutter application. The user can view compatibility percentages, explanation tags, outfit details, save outfits, and generate another set of recommendations.

To support research evaluation, I added a feedback feature where users can rate each outfit as Good, Okay, or Bad. These feedback records are stored in the backend and shown in the Evaluation Summary screen. This gives measurable evidence such as average rating, good match count, bad match count, and rating distribution.

Therefore, my component improves the system by moving from individual product recommendation to intelligent multi-item outfit recommendation with evaluation support.
```

## 3. Screenshots To Capture

Capture these screenshots from the running app:

| Screenshot | Purpose |
|---|---|
| Product list screen | Shows available clothing items |
| Product detail screen | Shows selected item before outfit generation |
| Complete the Look screen | Shows outfit generation feature |
| Generated outfit cards | Shows ranked outfit suggestions |
| Outfit detail screen | Shows full outfit details and score breakdown |
| Feedback buttons | Shows Good / Okay / Bad evaluation feature |
| Saved outfits screen | Shows saved outfit functionality |
| Evaluation Summary screen | Shows research evaluation results |

## 4. Result Values To Record

After rating at least 10-20 outfits, open the Evaluation Summary screen and record:

| Metric | Value |
|---|---|
| Total feedback count |  |
| Average rating |  |
| Good matches |  |
| Okay matches |  |
| Bad matches |  |
| Good match ratio |  |

You can also use this backend endpoint:

```text
GET /outfits/feedback-report/USR001
```

## 5. Final Testing Commands

Backend:

```powershell
cd D:\R26-IT-052
backend\venv\Scripts\python.exe -m pytest backend\tests
```

Frontend:

```powershell
cd D:\R26-IT-052\frontend
C:\flutter\bin\cache\dart-sdk\bin\dart.exe analyze
```

## 6. Final Submission Checklist

Before submission, confirm:

- Backend starts without errors.
- Flutter app starts without errors.
- Outfit generation works.
- Compatibility score and reason tags display correctly.
- Rule-based and ML internal scores are not shown to the user.
- Save outfit works.
- Good / Okay / Bad feedback works.
- Evaluation Summary updates after feedback.
- Report includes screenshots.
- Report includes real feedback result values.
- Final tests pass.
