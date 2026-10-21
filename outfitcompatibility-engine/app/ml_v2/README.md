# OutfitIQ V2 Outfit Compatibility Engine

## Purpose

This model predicts the visual compatibility of normal clothing products.

Supported categories:

- tops
- bottoms
- outerwear
- all-body

It does not evaluate body fit, body shape, shoes, bags, accessories, or occasion suitability.

## Production Process

1. Read product image, item ID and category from the database.
2. Convert the image into a normalized 512-dimensional FashionCLIP embedding.
3. Send outfit embeddings and categories to the Outfit Transformer.
4. Generate a compatibility score.
5. Use the classification threshold of 0.505.
6. Rank compatible candidates.
7. Apply diversity reranking.
8. Return the final Top-5 outfits.

The database provides products. The trained model decides visual compatibility.

## Files

- fashionclip_encoder.py: Converts images and image URLs into FashionCLIP embeddings.
- outfit_transformer_model.py: Contains the PyTorch model architecture.
- outfit_inference.py: Loads the model, scores outfits and performs diversity reranking.
- model/: Contains production weights, configuration and final metrics.
- examples/: Contains the example Top-5 response and visualization.
- evaluation/: Contains evaluation plots and V1/V2 comparison.

## Final V2 Results

- Accuracy: 0.6616
- Balanced accuracy: 0.6616
- Precision: 0.6512
- Recall: 0.6961
- F1 score: 0.6729
- ROC-AUC: 0.7282
- Log loss: 0.6390
- Best validation ROC-AUC: 0.7514

The compatibility score is a ranking confidence score. It is not the model accuracy.

## Installation

Python 3.11 is recommended.

Windows:

    py -3.11 -m venv venv
    venv\Scripts\activate
    python -m pip install --upgrade pip
    pip install -r requirements.txt

macOS or Linux:

    python3 -m venv venv
    source venv/bin/activate
    python -m pip install --upgrade pip
    pip install -r requirements.txt

## Backend Integration

Import these classes:

    from fashionclip_encoder import FashionCLIPEncoder
    from outfit_inference import OutfitCompatibilityPredictor

Create them once when the backend starts:

    encoder = FashionCLIPEncoder()
    predictor = OutfitCompatibilityPredictor()

Use FashionCLIPEncoder to encode product images. Each item passed to the predictor must contain:

- item_id
- category
- embedding

Use predict_outfit() to score one outfit.

Use select_diverse_top_five() to return diverse Top-5 recommendations.

## Important Notes

- Do not load the models again for every request.
- Cache product embeddings in the backend or database.
- Regenerate an embedding when a product image changes.
- Do not use Polyvore test embeddings for real store products.
- Candidate products must come from the project product database.
- The first FashionCLIP load downloads approximately 600 MB.
- Diversity reranking only removes repeated items; the trained model still decides compatibility.
