from fastapi import FastAPI, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import engine, get_db
from app.models import Base, User, UserOnboardingPreference, UserLearnedPreference, UserInteraction, Product
from app.schemas import (
    GoogleLoginRequest,
    GoogleLoginResponse,
    OnboardingRequest,
    OnboardingResponse,
    ProfileResponse,
    InteractionRequest,
    InteractionResponse
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
        existing_preferences.price_min = request.price_min
        existing_preferences.price_max = request.price_max
        existing_preferences.occasions = request.occasions
        existing_preferences.preferred_patterns = request.preferred_patterns
        existing_preferences.extra_preferences = request.extra_preferences

        db.commit()
        db.refresh(existing_preferences)

        return existing_preferences

    new_preferences = UserOnboardingPreference(
        user_id=current_user.user_id,
        preferred_categories=request.preferred_categories,
        preferred_colors=request.preferred_colors,
        preferred_styles=request.preferred_styles,
        price_min=request.price_min,
        price_max=request.price_max,
        occasions=request.occasions,
        preferred_patterns=request.preferred_patterns,
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










@app.post("/products/sample")
def create_sample_products(db: Session = Depends(get_db)):
    """
    Inserts sample product data for testing Chala's Learning Engine.
    Later, Koji's module will insert real product data into the products table.
    """

    sample_products = [
        Product(
            item_id="P001",
            product_name="Black Casual Top",
            category="Tops",
            color=["Black"],
            style=["Casual"],
            brand="H&M",
            product_url="https://example.com/products/P001",
            image_url="https://example.com/images/P001.jpg"
        ),
        Product(
            item_id="P002",
            product_name="White Elegant Dress",
            category="Dresses",
            color=["White"],
            style=["Elegant"],
            brand="H&M",
            product_url="https://example.com/products/P002",
            image_url="https://example.com/images/P002.jpg"
        ),
        Product(
            item_id="P003",
            product_name="Blue Formal Shirt",
            category="Shirts",
            color=["Blue"],
            style=["Formal"],
            brand="H&M",
            product_url="https://example.com/products/P003",
            image_url="https://example.com/images/P003.jpg"
        ),
        Product(
            item_id="P004",
            product_name="Grey Sporty Hoodie",
            category="Hoodies",
            color=["Grey"],
            style=["Sporty"],
            brand="H&M",
            product_url="https://example.com/products/P004",
            image_url="https://example.com/images/P004.jpg"
        ),
        Product(
            item_id="P005",
            product_name="Pink Party Skirt",
            category="Skirts",
            color=["Pink"],
            style=["Party wear"],
            brand="H&M",
            product_url="https://example.com/products/P005",
            image_url="https://example.com/images/P005.jpg"
        )
    ]

    inserted_count = 0
    skipped_count = 0

    for product in sample_products:
        existing_product = db.query(Product).filter(
            Product.item_id == product.item_id
        ).first()

        if existing_product:
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


