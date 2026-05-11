from fastapi import FastAPI, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.fashion_embedding_service import (
    get_image_embedding,
    create_user_preference_vector,
)

from app.database import engine, get_db
from app.models import Base, User, UserOnboardingPreference, UserLearnedPreference, UserInteraction, Product, UserMLPreference
from app.schemas import (
    GoogleLoginRequest,
    GoogleLoginResponse,
    OnboardingRequest,
    OnboardingResponse,
    ProfileResponse,
    InteractionRequest,
    InteractionResponse,
    InteractionHistoryResponse
)
from app.auth import verify_google_token, create_access_token, get_current_user
from app.learning_engine import calculate_learned_preferences

# Create database tables automatically
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Smart Fashion Assistant - Chala Backend",
    description="Backend for Google Sign-In, Onboarding, User Profile, and User Learning Engine",
    version="1.0.0"
)


@app.get("/")
def home():
    return {
        "message": "Chala backend is running successfully"
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "database": "connected",
        "module": "user-profiling-chalani"
    }


@app.post("/auth/google", response_model=GoogleLoginResponse)
def google_login(request: GoogleLoginRequest, db: Session = Depends(get_db)):
    """
    Google Sign-In endpoint.

    Frontend/mobile app sends Google ID token here.
    Backend verifies the token.
    Then backend creates/fetches user from PostgreSQL.
    Finally backend returns our own JWT token.
    """

    google_user = verify_google_token(request.token)

    existing_user = db.query(User).filter(
        User.google_sub == google_user["google_sub"]
    ).first()

    if existing_user:
        user = existing_user
    else:
        user = User(
            google_sub=google_user["google_sub"],
            full_name=google_user["full_name"],
            email=google_user["email"],
            profile_picture=google_user["profile_picture"],
            auth_provider="google"
        )

        db.add(user)
        db.commit()
        db.refresh(user)

    access_token = create_access_token(
        data={
            "sub": str(user.user_id),
            "email": user.email
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


@app.get("/google-test.html")
def google_test_page():
    return FileResponse("google-test.html")


@app.get("/auth/me")
def get_logged_in_user(current_user: User = Depends(get_current_user)):
    return {
        "user_id": current_user.user_id,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "auth_provider": current_user.auth_provider
    }

@app.post("/onboarding", response_model=OnboardingResponse)
def save_onboarding_preferences(
    request: OnboardingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Saves or updates onboarding preferences for the logged-in user.
    The user_id is taken from the JWT token, not from the request body.
    """

    existing_preferences = db.query(UserOnboardingPreference).filter(
        UserOnboardingPreference.user_id == current_user.user_id
    ).first()

    if existing_preferences:
        existing_preferences.preferred_categories = request.preferred_categories
        existing_preferences.preferred_colors = request.preferred_colors
        existing_preferences.preferred_styles = request.preferred_styles
        existing_preferences.occasions = request.occasions
        existing_preferences.choice_priorities = request.choice_priorities
        existing_preferences.preferred_brands = request.preferred_brands
        existing_preferences.extra_preferences = request.extra_preferences

        db.commit()
        db.refresh(existing_preferences)

        return existing_preferences

    new_preferences = UserOnboardingPreference(
        user_id=current_user.user_id,
        preferred_categories=request.preferred_categories,
        preferred_colors=request.preferred_colors,
        preferred_styles=request.preferred_styles,
        price_min=None,
        price_max=None,
        occasions=request.occasions,
        choice_priorities=request.choice_priorities,
        preferred_brands=request.preferred_brands,
        extra_preferences=request.extra_preferences
    )

    db.add(new_preferences)
    db.commit()
    db.refresh(new_preferences)

    return new_preferences


@app.get("/profile", response_model=ProfileResponse)
def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns the logged-in user's profile, onboarding preferences,
    and learned preferences.
    """

    onboarding_preferences = db.query(UserOnboardingPreference).filter(
        UserOnboardingPreference.user_id == current_user.user_id
    ).first()

    learned_preferences = db.query(UserLearnedPreference).filter(
        UserLearnedPreference.user_id == current_user.user_id
    ).first()

    return {
        "user": current_user,
        "onboarding_preferences": onboarding_preferences,
        "learned_preferences": learned_preferences
    }


def get_interaction_value(interaction_type: str) -> float:
    interaction_weights = {
        "view": 1.0,
        "click": 2.0,
        "save": 3.0,
        "select": 4.0,
        "dislike": -2.0
    }

    return interaction_weights.get(interaction_type.lower(), 1.0)


@app.post("/interactions", response_model=InteractionResponse)
def save_user_interaction(
    request: InteractionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Saves a user interaction with a product item.
    The user_id is taken from the JWT token.
    """

    interaction_value = request.interaction_value

    if interaction_value is None:
        interaction_value = get_interaction_value(request.interaction_type)

    new_interaction = UserInteraction(
        user_id=current_user.user_id,
        item_id=request.item_id,
        interaction_type=request.interaction_type.lower(),
        interaction_value=interaction_value
    )

    db.add(new_interaction)
    db.commit()
    db.refresh(new_interaction)

    return new_interaction







@app.get("/interactions/history", response_model=InteractionHistoryResponse)
def get_user_interaction_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns the logged-in user's interaction history with product details
    and interaction statistics.
    """

    interactions = db.query(UserInteraction).filter(
        UserInteraction.user_id == current_user.user_id
    ).order_by(UserInteraction.created_at.desc()).all()

    total_interactions = len(interactions)

    view_count = 0
    click_count = 0
    save_count = 0
    select_count = 0
    dislike_count = 0

    item_ids = []

    for interaction in interactions:
        interaction_type = interaction.interaction_type.lower()

        if interaction_type == "view":
            view_count += 1
        elif interaction_type == "click":
            click_count += 1
        elif interaction_type == "save":
            save_count += 1
        elif interaction_type == "select":
            select_count += 1
        elif interaction_type == "dislike":
            dislike_count += 1

        item_ids.append(interaction.item_id)

    products = db.query(Product).filter(
        Product.item_id.in_(item_ids)
    ).all()

    products_by_id = {
        product.item_id: product
        for product in products
    }

    history_items = []

    for interaction in interactions:
        product = products_by_id.get(interaction.item_id)

        history_items.append({
            "interaction_id": interaction.interaction_id,
            "item_id": interaction.item_id,
            "interaction_type": interaction.interaction_type,
            "interaction_value": interaction.interaction_value,
            "created_at": interaction.created_at,
            "product_name": product.product_name if product else None,
            "category": product.category if product else None,
            "color": product.color if product else None,
            "style": product.style if product else None,
            "brand": product.brand if product else None,
            "image_url": product.image_url if product else None,
            "product_url": product.product_url if product else None,
        })

    return {
        "stats": {
            "total_interactions": total_interactions,
            "view_count": view_count,
            "click_count": click_count,
            "save_count": save_count,
            "select_count": select_count,
            "dislike_count": dislike_count,
        },
        "interactions": history_items
    }








@app.post("/products/sample")
def create_sample_products(db: Session = Depends(get_db)):
    """
    Inserts sample product data for testing Chala's Learning Engine.
    Later, Koji's module will insert real product data into the products table.
    """

    sample_products = [
        Product(
            item_id="P001",
            product_name="White Cotton T-Shirt",
            category="Tops",
            color=["White"],
            style=["Casual"],
            brand="OutfitIQ Sample",
            product_url="https://example.com/products/P001",
            image_url="https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?auto=format&fit=crop&w=900&q=80"
        ),
        Product(
            item_id="P002",
            product_name="Grey Hoodie",
            category="Hoodies",
            color=["Grey"],
            style=["Comfort"],
            brand="OutfitIQ Sample",
            product_url="https://example.com/products/P002",
            image_url="https://images.unsplash.com/photo-1556821840-3a63f95609a7?auto=format&fit=crop&w=900&q=80"
        ),
        Product(
            item_id="P003",
            product_name="Blue Denim Jeans",
            category="Jeans",
            color=["Blue"],
            style=["Trendy"],
            brand="OutfitIQ Sample",
            product_url="https://example.com/products/P003",
            image_url="https://images.unsplash.com/photo-1542272604-787c3835535d?auto=format&fit=crop&w=900&q=80"
        ),
        Product(
            item_id="P004",
            product_name="Black Blazer",
            category="Blazers",
            color=["Black"],
            style=["Formal"],
            brand="OutfitIQ Sample",
            product_url="https://example.com/products/P004",
            image_url="https://images.unsplash.com/photo-1592878904946-b3cd8ae243d0?auto=format&fit=crop&w=900&q=80"
        ),
        Product(
            item_id="P005",
            product_name="Pink Party Skirt",
            category="Skirts",
            color=["Pink"],
            style=["Party wear"],
            brand="OutfitIQ Sample",
            product_url="https://example.com/products/P005",
            image_url="https://images.unsplash.com/photo-1583496661160-fb5886a13d44?auto=format&fit=crop&w=900&q=80"
        )
    ]

    inserted_count = 0
    skipped_count = 0

    for product in sample_products:
        existing_product = db.query(Product).filter(
            Product.item_id == product.item_id
        ).first()

        if existing_product:
            existing_product.product_name = product.product_name
            existing_product.category = product.category
            existing_product.color = product.color
            existing_product.style = product.style
            existing_product.brand = product.brand
            existing_product.product_url = product.product_url
            existing_product.image_url = product.image_url

            skipped_count += 1
            continue

        db.add(product)
        inserted_count += 1

    db.commit()

    return {
        "message": "Sample products processed successfully",
        "inserted_count": inserted_count,
        "skipped_count": skipped_count
    }









@app.post("/learning/update")
def update_learning_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Updates learned preferences for the logged-in user
    using saved interactions and product details.
    """

    interactions = db.query(UserInteraction).filter(
        UserInteraction.user_id == current_user.user_id
    ).all()

    if not interactions:
        return {
            "message": "No interactions found for this user",
            "learned_preferences": None
        }

    item_ids = [interaction.item_id for interaction in interactions]

    products = db.query(Product).filter(
        Product.item_id.in_(item_ids)
    ).all()

    products_by_id = {
        product.item_id: product
        for product in products
    }

    learned_data = calculate_learned_preferences(
        interactions=interactions,
        products_by_id=products_by_id
    )

    existing_learned_preferences = db.query(UserLearnedPreference).filter(
        UserLearnedPreference.user_id == current_user.user_id
    ).first()

    if existing_learned_preferences:
        existing_learned_preferences.category_weights = learned_data["category_weights"]
        existing_learned_preferences.color_weights = learned_data["color_weights"]
        existing_learned_preferences.style_weights = learned_data["style_weights"]
        existing_learned_preferences.brand_weights = learned_data["brand_weights"]

        db.commit()
        db.refresh(existing_learned_preferences)

        return {
            "message": "Learned preferences updated successfully",
            "learned_preferences": existing_learned_preferences
        }

    new_learned_preferences = UserLearnedPreference(
        user_id=current_user.user_id,
        category_weights=learned_data["category_weights"],
        color_weights=learned_data["color_weights"],
        style_weights=learned_data["style_weights"],
        brand_weights=learned_data["brand_weights"]
    )

    db.add(new_learned_preferences)
    db.commit()
    db.refresh(new_learned_preferences)

    return {
        "message": "Learned preferences created successfully",
        "learned_preferences": new_learned_preferences
    }





@app.post("/ml/test-image-embedding")
def test_image_embedding():
    """
    Temporary ML test endpoint.
    Creates a FashionCLIP embedding for one sample fashion image.
    """

    image_url = "https://images.unsplash.com/photo-1483985988355-763728e1935b?auto=format&fit=crop&w=900&q=80"

    embedding = get_image_embedding(image_url)

    return {
        "message": "Image embedding created successfully",
        "model_name": "McClain/fashion-embedder",
        "image_url": image_url,
        "embedding_dimension": len(embedding),
        "first_10_values": embedding[:10]
    }





@app.post("/ml/test-user-vector")
def test_user_preference_vector():
    """
    Temporary ML test endpoint.
    Creates a user preference vector from sample interacted fashion products.
    """

    interaction_items = [
        {
            "item_id": "P001",
            "image_url": "https://images.unsplash.com/photo-1543076447-215ad9ba6923?auto=format&fit=crop&w=900&q=80",
            "interaction_weight": 2.0
        },
        {
            "item_id": "P002",
            "image_url": "https://images.unsplash.com/photo-1483985988355-763728e1935b?auto=format&fit=crop&w=900&q=80",
            "interaction_weight": 3.0
        },
        {
            "item_id": "P003",
            "image_url": "https://images.unsplash.com/photo-1594223274512-ad4803739b7c?auto=format&fit=crop&w=900&q=80",
            "interaction_weight": 4.0
        }
    ]

    user_vector = create_user_preference_vector(interaction_items)

    return {
        "message": "User preference vector created successfully",
        "model_name": "McClain/fashion-embedder",
        "embedding_dimension": len(user_vector),
        "first_10_values": user_vector[:10],
        "used_items": interaction_items
    }




@app.post("/ml/update-current-user-vector")
def update_current_user_vector(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Creates and saves an ML-based user preference vector for the logged-in user
    using real saved interactions and product image URLs from the database.
    """

    interactions = db.query(UserInteraction).filter(
        UserInteraction.user_id == current_user.user_id
    ).all()

    if not interactions:
        return {
            "message": "No interactions found for this user",
            "user_id": current_user.user_id,
            "user_preference_vector": None
        }

    item_ids = [interaction.item_id for interaction in interactions]

    products = db.query(Product).filter(
        Product.item_id.in_(item_ids)
    ).all()

    products_by_id = {
        product.item_id: product
        for product in products
    }

    interaction_items = []

    for interaction in interactions:
        product = products_by_id.get(interaction.item_id)

        if product is None:
            continue

        if not product.image_url:
            continue

        interaction_items.append({
            "item_id": interaction.item_id,
            "image_url": product.image_url,
            "interaction_type": interaction.interaction_type,
            "interaction_weight": interaction.interaction_value
        })

    if not interaction_items:
        return {
            "message": "No valid product image URLs found for this user's interactions",
            "user_id": current_user.user_id,
            "user_preference_vector": None
        }

    user_vector = create_user_preference_vector(interaction_items)

    if not user_vector:
        return {
            "message": "Could not create user preference vector",
            "user_id": current_user.user_id,
            "user_preference_vector": None
        }

    existing_ml_preferences = db.query(UserMLPreference).filter(
        UserMLPreference.user_id == current_user.user_id
    ).first()

    if existing_ml_preferences:
        existing_ml_preferences.model_name = "McClain/fashion-embedder"
        existing_ml_preferences.embedding_dimension = len(user_vector)
        existing_ml_preferences.user_preference_vector = user_vector
        existing_ml_preferences.used_interaction_count = len(interaction_items)

        db.commit()
        db.refresh(existing_ml_preferences)

        saved_ml_preferences = existing_ml_preferences
        message = "Current user ML preference vector updated and saved successfully"

    else:
        new_ml_preferences = UserMLPreference(
            user_id=current_user.user_id,
            model_name="McClain/fashion-embedder",
            embedding_dimension=len(user_vector),
            user_preference_vector=user_vector,
            used_interaction_count=len(interaction_items)
        )

        db.add(new_ml_preferences)
        db.commit()
        db.refresh(new_ml_preferences)

        saved_ml_preferences = new_ml_preferences
        message = "Current user ML preference vector created and saved successfully"

    return {
        "message": message,
        "user_id": current_user.user_id,
        "model_name": saved_ml_preferences.model_name,
        "embedding_dimension": saved_ml_preferences.embedding_dimension,
        "first_10_values": saved_ml_preferences.user_preference_vector[:10],
        "used_interaction_count": saved_ml_preferences.used_interaction_count,
        "used_items": interaction_items
    }



@app.get("/ml/current-user-vector-summary")
def get_current_user_vector_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns a summary of the saved ML-based user preference vector
    for the logged-in user.
    """

    ml_preferences = db.query(UserMLPreference).filter(
        UserMLPreference.user_id == current_user.user_id
    ).first()

    if not ml_preferences:
        return {
            "message": "No saved ML preference vector found for this user",
            "user_id": current_user.user_id,
            "ml_preferences": None
        }

    return {
        "message": "Saved ML preference vector found",
        "user_id": current_user.user_id,
        "model_name": ml_preferences.model_name,
        "embedding_dimension": ml_preferences.embedding_dimension,
        "used_interaction_count": ml_preferences.used_interaction_count,
        "first_10_values": ml_preferences.user_preference_vector[:10],
        "updated_at": ml_preferences.updated_at
    }


