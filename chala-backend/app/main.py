from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from collections import defaultdict

from app.fashion_embedding_service import (
    get_image_embedding,
    create_user_preference_vector,
)

from app.database import engine, get_db

from app.models import (
    Base,
    User,
    UserOnboardingPreference,
    UserLearnedPreference,
    UserInteraction,
    Product,
    UserMLPreference,
)

from app.schemas import (
    GoogleLoginRequest,
    GoogleLoginResponse,
    OnboardingRequest,
    OnboardingResponse,
    ProfileResponse,
    InteractionRequest,
    InteractionResponse,
    InteractionHistoryResponse,
    CurrentPreferencesResponse,
    PreferenceExpansionResponse,
    EnrichedCurrentPreferencesResponse,
)

from app.auth import (
    verify_google_token,
    create_access_token,
    get_current_user,
)

from app.learning_engine import (
    calculate_learned_preferences,
)

from app.ml.preference_expansion_service import (
    expand_onboarding_preferences,
)


# ============================================================
# DATABASE
# ============================================================

Base.metadata.create_all(bind=engine)


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="Smart Fashion Assistant - Chala Backend",
    description=(
        "Backend for Google Sign-In, Onboarding, "
        "User Profile, and User Learning Engine"
    ),
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5000",
        "http://127.0.0.1:5000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# BASIC ENDPOINTS
# ============================================================

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
        "module": "user-profiling-chalani",
    }


# ============================================================
# GOOGLE AUTHENTICATION
# ============================================================

@app.post(
    "/auth/google",
    response_model=GoogleLoginResponse,
)
def google_login(
    request: GoogleLoginRequest,
    db: Session = Depends(get_db),
):
    """
    Google Sign-In endpoint.

    Flutter sends Google ID token.
    Backend verifies it.
    Backend creates/fetches user.
    Backend returns JWT.
    """

    google_user = verify_google_token(
        request.token
    )

    existing_user = (
        db.query(User)
        .filter(
            User.google_sub
            == google_user["google_sub"]
        )
        .first()
    )

    if existing_user:
        user = existing_user

    else:
        user = User(
            google_sub=google_user[
                "google_sub"
            ],
            full_name=google_user[
                "full_name"
            ],
            email=google_user[
                "email"
            ],
            profile_picture=google_user[
                "profile_picture"
            ],
            auth_provider="google",
        )

        db.add(user)
        db.commit()
        db.refresh(user)

    access_token = create_access_token(
        data={
            "sub": str(user.user_id),
            "email": user.email,
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user,
    }


@app.get("/google-test.html")
def google_test_page():
    return FileResponse(
        "google-test.html"
    )


@app.get("/auth/me")
def get_logged_in_user(
    current_user: User = Depends(
        get_current_user
    ),
):
    return {
        "user_id":
            current_user.user_id,

        "full_name":
            current_user.full_name,

        "email":
            current_user.email,

        "auth_provider":
            current_user.auth_provider,
    }


# ============================================================
# DELETE ACCOUNT
# ============================================================

@app.delete("/account")
def delete_current_user_account(
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    """
    Permanently deletes the current user's account
    and personalization data.
    """

    user_id = current_user.user_id

    try:

        db.query(
            UserMLPreference
        ).filter(
            UserMLPreference.user_id
            == user_id
        ).delete(
            synchronize_session=False
        )

        db.query(
            UserLearnedPreference
        ).filter(
            UserLearnedPreference.user_id
            == user_id
        ).delete(
            synchronize_session=False
        )

        db.query(
            UserInteraction
        ).filter(
            UserInteraction.user_id
            == user_id
        ).delete(
            synchronize_session=False
        )

        db.query(
            UserOnboardingPreference
        ).filter(
            UserOnboardingPreference.user_id
            == user_id
        ).delete(
            synchronize_session=False
        )

        db.query(User).filter(
            User.user_id == user_id
        ).delete(
            synchronize_session=False
        )

        db.commit()

        return {
            "message": (
                "Account and all related data "
                "deleted successfully"
            )
        }

    except Exception:

        db.rollback()
        raise


# ============================================================
# ONBOARDING
# ============================================================

@app.post(
    "/onboarding",
    response_model=OnboardingResponse,
)
def save_onboarding_preferences(
    request: OnboardingRequest,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    """
    Saves or updates onboarding preferences.
    """

    existing_preferences = (
        db.query(
            UserOnboardingPreference
        )
        .filter(
            UserOnboardingPreference.user_id
            == current_user.user_id
        )
        .first()
    )

    if existing_preferences:

        existing_preferences.preferred_categories = (
            request.preferred_categories
        )

        existing_preferences.preferred_colors = (
            request.preferred_colors
        )

        existing_preferences.preferred_styles = (
            request.preferred_styles
        )

        existing_preferences.occasions = (
            request.occasions
        )

        existing_preferences.choice_priorities = (
            request.choice_priorities
        )

        existing_preferences.preferred_brands = (
            request.preferred_brands
        )

        existing_preferences.extra_preferences = (
            request.extra_preferences
        )

        db.commit()
        db.refresh(
            existing_preferences
        )

        return existing_preferences


    new_preferences = UserOnboardingPreference(
        user_id=current_user.user_id,

        preferred_categories=(
            request.preferred_categories
        ),

        preferred_colors=(
            request.preferred_colors
        ),

        preferred_styles=(
            request.preferred_styles
        ),

        price_min=None,
        price_max=None,

        occasions=(
            request.occasions
        ),

        choice_priorities=(
            request.choice_priorities
        ),

        preferred_brands=(
            request.preferred_brands
        ),

        extra_preferences=(
            request.extra_preferences
        ),
    )

    db.add(new_preferences)
    db.commit()
    db.refresh(new_preferences)

    return new_preferences


# ============================================================
# PROFILE
# ============================================================

@app.get(
    "/profile",
    response_model=ProfileResponse,
)
def get_profile(
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    """
    Returns user profile,
    onboarding preferences,
    and learned preferences.
    """

    onboarding_preferences = (
        db.query(
            UserOnboardingPreference
        )
        .filter(
            UserOnboardingPreference.user_id
            == current_user.user_id
        )
        .first()
    )

    learned_preferences = (
        db.query(
            UserLearnedPreference
        )
        .filter(
            UserLearnedPreference.user_id
            == current_user.user_id
        )
        .first()
    )

    return {
        "user":
            current_user,

        "onboarding_preferences":
            onboarding_preferences,

        "learned_preferences":
            learned_preferences,
    }


# ============================================================
# ORIGINAL CURRENT PREFERENCE LOGIC
# ============================================================

def get_onboarding_weight(
    interaction_count: int,
) -> float:
    """
    Gradually reduces onboarding influence
    as more interactions are collected.

    Original behavior:

    < 5 interactions  -> 1.00
    < 10              -> 0.75
    < 20              -> 0.50
    20+               -> 0.25
    """

    if interaction_count < 5:
        return 1.0

    if interaction_count < 10:
        return 0.75

    if interaction_count < 20:
        return 0.50

    return 0.25


def normalize_current_preference_scores(
    scores: dict,
    top_n: int = 3,
    minimum_score: float = 0.30,
) -> dict:
    """
    Original Current Preference normalization.

    1. Remove non-positive values
    2. Normalize strongest value to 1.0
    3. Remove values below 0.30
    4. Sort strongest -> weakest
    5. Return Top 3
    """

    if not scores:
        return {}

    positive_scores = {
        key: value
        for key, value
        in scores.items()
        if value > 0
    }

    if not positive_scores:
        return {}

    max_score = max(
        positive_scores.values()
    )

    normalized_scores = {
        key: round(
            value / max_score,
            2,
        )
        for key, value
        in positive_scores.items()
    }

    filtered_scores = {
        key: value
        for key, value
        in normalized_scores.items()
        if value >= minimum_score
    }

    sorted_scores = sorted(
        filtered_scores.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    return dict(
        sorted_scores[:top_n]
    )


def combine_current_preferences(
    onboarding_values,
    learned_weights,
    onboarding_weight: float,
) -> dict:
    """
    Original Current Preference behavior.

    Current preference =
        onboarding influence
        +
        learned interaction behavior

    Then normalized and Top 3 selected.
    """

    combined_scores = defaultdict(
        float
    )

    if onboarding_values:

        for value in onboarding_values:

            if value:
                combined_scores[
                    value
                ] += onboarding_weight


    if learned_weights:

        for key, value in (
            learned_weights.items()
        ):

            if (
                key
                and value is not None
            ):

                combined_scores[
                    key
                ] += float(value)


    return normalize_current_preference_scores(
        dict(combined_scores)
    )


# ============================================================
# CURRENT PREFERENCES
# ============================================================

@app.get(
    "/profile/current-preferences",
    response_model=CurrentPreferencesResponse,
)
def get_current_preferences(
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    """
    Returns the user's current dynamic fashion profile.

    IMPORTANT:

    This restores the original Current Preference
    behavior used before Logistic Regression
    preference expansion was added.

    Current Profile includes:

    - Category
    - Color
    - Style
    - Brand

    It combines:

    onboarding preferences
            +
    learned interaction behavior
            +
    recency/time decay

    and returns Top 3 current values.
    """

    # --------------------------------------------------------
    # ONBOARDING
    # --------------------------------------------------------

    onboarding_preferences = (
        db.query(
            UserOnboardingPreference
        )
        .filter(
            UserOnboardingPreference.user_id
            == current_user.user_id
        )
        .first()
    )


    # --------------------------------------------------------
    # INTERACTIONS
    # --------------------------------------------------------

    interactions = (
        db.query(
            UserInteraction
        )
        .filter(
            UserInteraction.user_id
            == current_user.user_id
        )
        .all()
    )

    interaction_count = len(
        interactions
    )


    # --------------------------------------------------------
    # DEFAULT LEARNED VALUES
    # --------------------------------------------------------

    learned_data = {
        "category_weights": {},
        "color_weights": {},
        "style_weights": {},
        "brand_weights": {},
        "occasion_weights": {},
    }


    # --------------------------------------------------------
    # RECALCULATE LEARNING FROM INTERACTIONS
    # --------------------------------------------------------

    if interactions:

        item_ids = [
            interaction.item_id
            for interaction
            in interactions
        ]

        products = (
            db.query(Product)
            .filter(
                Product.item_id.in_(
                    item_ids
                )
            )
            .all()
        )

        products_by_id = {
            product.item_id:
                product

            for product
            in products
        }


        # Interaction weight + time decay
        learned_data = (
            calculate_learned_preferences(
                interactions=interactions,
                products_by_id=products_by_id,
            )
        )


        # ----------------------------------------------------
        # SAVE UPDATED LEARNED PROFILE
        # ----------------------------------------------------

        learned_preferences = (
            db.query(
                UserLearnedPreference
            )
            .filter(
                UserLearnedPreference.user_id
                == current_user.user_id
            )
            .first()
        )


        if learned_preferences:

            learned_preferences.category_weights = (
                learned_data[
                    "category_weights"
                ]
            )

            learned_preferences.color_weights = (
                learned_data[
                    "color_weights"
                ]
            )

            learned_preferences.style_weights = (
                learned_data[
                    "style_weights"
                ]
            )

            learned_preferences.brand_weights = (
                learned_data[
                    "brand_weights"
                ]
            )

            learned_preferences.occasion_weights = (
                learned_data[
                    "occasion_weights"
                ]
            )


        else:

            learned_preferences = (
                UserLearnedPreference(
                    user_id=(
                        current_user.user_id
                    ),

                    category_weights=(
                        learned_data[
                            "category_weights"
                        ]
                    ),

                    color_weights=(
                        learned_data[
                            "color_weights"
                        ]
                    ),

                    style_weights=(
                        learned_data[
                            "style_weights"
                        ]
                    ),

                    brand_weights=(
                        learned_data[
                            "brand_weights"
                        ]
                    ),

                    occasion_weights=(
                        learned_data[
                            "occasion_weights"
                        ]
                    ),
                )
            )

            db.add(
                learned_preferences
            )


        db.commit()


    # --------------------------------------------------------
    # ORIGINAL GRADUAL ONBOARDING REDUCTION
    # --------------------------------------------------------

    onboarding_weight = (
        get_onboarding_weight(
            interaction_count
        )
    )


    # --------------------------------------------------------
    # GET ONBOARDING ATTRIBUTES
    # --------------------------------------------------------

    onboarding_categories = (
        onboarding_preferences
        .preferred_categories

        if onboarding_preferences
        else []
    )


    onboarding_colors = (
        onboarding_preferences
        .preferred_colors

        if onboarding_preferences
        else []
    )


    onboarding_styles = (
        onboarding_preferences
        .preferred_styles

        if onboarding_preferences
        else []
    )

    onboarding_brands = (
        onboarding_preferences
        .preferred_brands

        if onboarding_preferences
        else []
    )


    onboarding_occasions = (
        onboarding_preferences
        .occasions

        if onboarding_preferences
        else []
    )




    # --------------------------------------------------------
    # BUILD ORIGINAL CURRENT PROFILE
    # --------------------------------------------------------

    return {

        "category_scores":
            combine_current_preferences(
                onboarding_categories,
                learned_data[
                    "category_weights"
                ],
                onboarding_weight,
            ),


        "color_scores":
            combine_current_preferences(
                onboarding_colors,
                learned_data[
                    "color_weights"
                ],
                onboarding_weight,
            ),


        "style_scores":
            combine_current_preferences(
                onboarding_styles,
                learned_data[
                    "style_weights"
                ],
                onboarding_weight,
            ),


        "brand_scores":
            combine_current_preferences(
                onboarding_brands,
                learned_data[
                    "brand_weights"
                ],
            onboarding_weight,
        ),

        "occasion_scores":
            combine_current_preferences(
                onboarding_occasions,
                learned_data[
                    "occasion_weights"
                ],
            onboarding_weight,
        ),
    }


# ============================================================
# LOGISTIC REGRESSION ONBOARDING ML ENDPOINT
# ============================================================

@app.get(
    "/ml/preference-expansion",
    response_model=PreferenceExpansionResponse,
)
def get_ml_preference_expansion(
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    """
    Current Logistic Regression preference expansion.

    NOTE:
    Same-family filtering will be added
    in the NEXT stage.

    This endpoint is kept unchanged for now.
    """

    onboarding_preferences = (
        db.query(
            UserOnboardingPreference
        )
        .filter(
            UserOnboardingPreference.user_id
            == current_user.user_id
        )
        .first()
    )


    if not onboarding_preferences:

        raise HTTPException(
            status_code=404,
            detail=(
                "No onboarding preferences "
                "found for this user"
            ),
        )


    return expand_onboarding_preferences(

        preferred_colors=(
            onboarding_preferences
            .preferred_colors
        ),

        preferred_categories=(
            onboarding_preferences
            .preferred_categories
        ),

        preferred_styles=(
            onboarding_preferences
            .preferred_styles
        ),

        occasions=(
            onboarding_preferences
            .occasions
        ),

        choice_priorities=(
            onboarding_preferences
            .choice_priorities
        ),

        preferred_brands=(
            onboarding_preferences
            .preferred_brands
        ),
    )


# ============================================================
# INTERACTION VALUE
# ============================================================

def get_interaction_value(
    interaction_type: str,
) -> float:

    interaction_weights = {

        "view": 1.0,

        "click": 2.0,

        "save": 3.0,

        "select": 4.0,

        "dislike": -2.0,
    }


    return interaction_weights.get(
        interaction_type.lower(),
        1.0,
    )


# ============================================================
# ENRICHED CURRENT PROFILE
# ============================================================
#
# NOTE:
#
# Current Profile now uses the RESTORED original logic.
#
# But ML family filtering and final Koji-output cleanup
# will be done in the NEXT stages.
# ============================================================

@app.get(
    "/profile/enriched-current-preferences",
    response_model=EnrichedCurrentPreferencesResponse,
)
def get_enriched_current_preferences(
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    """
    Builds the current enriched profile.

    Current learned profile comes from the
    restored original Current Preference logic.

    For now:

    Current Profile:
        Category
        Color
        Style
        Brand

    ML currently receives:
        Category
        Color
        Style

    Brand is NOT used as an ML feature by
    the trained Logistic Regression model.

    More ML cleanup happens in Stage 2.
    """

    # ========================================================
    # 1. GET RESTORED CURRENT PROFILE
    # ========================================================

    current_preferences = (
        get_current_preferences(
            current_user=current_user,
            db=db,
        )
    )


    current_categories = list(
        current_preferences[
            "category_scores"
        ].keys()
    )


    current_colors = list(
        current_preferences[
            "color_scores"
        ].keys()
    )


    current_styles = list(
        current_preferences[
            "style_scores"
        ].keys()
    )

    current_brands = list(
        current_preferences[
            "brand_scores"
        ].keys()
    )

    current_occasions = list(
        current_preferences[
            "occasion_scores"
        ].keys()
    )


    # ========================================================
    # 2. GET EXISTING ONBOARDING INFORMATION
    # ========================================================
    #
    # These fields still exist here temporarily because
    # current response schemas expect them.
    #
    # They will be removed from the FINAL KOJI OUTPUT
    # in the later cleanup stage.
    # ========================================================

    onboarding_preferences = (
        db.query(
            UserOnboardingPreference
        )
        .filter(
            UserOnboardingPreference.user_id
            == current_user.user_id
        )
        .first()
    )


    if onboarding_preferences:

        choice_priorities = (
            onboarding_preferences
                .choice_priorities
            or []
        )

    else:

        choice_priorities = []

    # ========================================================
    # 3. NEGATIVE BEHAVIOR PROTECTION
    # ========================================================

    interactions = (
        db.query(
            UserInteraction
        )
        .filter(
            UserInteraction.user_id
            == current_user.user_id
        )
        .all()
    )


    excluded_categories = set()

    excluded_colors = set()

    excluded_styles = set()


    if interactions:

        item_ids = [
            interaction.item_id
            for interaction
            in interactions
        ]


        products = (
            db.query(Product)
            .filter(
                Product.item_id.in_(
                    item_ids
                )
            )
            .all()
        )


        products_by_id = {
            product.item_id:
                product

            for product
            in products
        }


        category_behavior = defaultdict(
            float
        )

        color_behavior = defaultdict(
            float
        )

        style_behavior = defaultdict(
            float
        )


        for interaction in interactions:

            product = (
                products_by_id.get(
                    interaction.item_id
                )
            )


            if product is None:
                continue


            interaction_value = float(
                interaction.interaction_value
            )


            # CATEGORY
            if product.category:

                category_behavior[
                    product.category
                ] += interaction_value


            # COLOR
            for color in (
                product.color or []
            ):

                color_behavior[
                    color
                ] += interaction_value


            # STYLE
            for style in (
                product.style or []
            ):

                style_behavior[
                    style
                ] += interaction_value


        excluded_categories = {
            category
            for category, score
            in category_behavior.items()
            if score < 0
        }


        excluded_colors = {
            color
            for color, score
            in color_behavior.items()
            if score < 0
        }


        excluded_styles = {
            style
            for style, score
            in style_behavior.items()
            if score < 0
        }


        # Temporary sample product uses "Comfort"
        # while trained model uses "Comfort wear".
        if "Comfort" in excluded_styles:

            excluded_styles.add(
                "Comfort wear"
            )


    # ========================================================
    # 4. RUN CURRENT ML EXPANSION
    # ========================================================
    #
    # Brand is NOT used as ML input.
    #
    # current_categories
    # current_colors
    # current_styles
    #
    # are the actual dynamic ML inputs.
    # ========================================================

    ml_result = (
        expand_onboarding_preferences(

            preferred_colors=(
                current_colors
            ),

            preferred_categories=(
                current_categories
            ),

            preferred_styles=(
                current_styles
            ),

            occasions=(
                current_occasions
            ),

            choice_priorities=(
                choice_priorities
            ),

            preferred_brands=(
                current_brands
            ),

            excluded_colors=list(
                excluded_colors
            ),

            excluded_categories=list(
                excluded_categories
            ),

            excluded_styles=list(
                excluded_styles
            ),
        )
    )


    # ========================================================
    # 5. RETURN EXISTING RESPONSE
    # ========================================================

    return {

        "current_preferences":
            current_preferences,

        "ml_expansions":
            ml_result[
                "ml_expansions"
            ],

        "enriched_preferences":
            ml_result[
                "enriched_preferences"
            ],
    }


# ============================================================
# SAVE USER INTERACTION
# ============================================================

@app.post(
    "/interactions",
    response_model=InteractionResponse,
)
def save_user_interaction(
    request: InteractionRequest,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    """
    Saves an interaction.

    Interaction weights:

    view     = 1
    click    = 2
    save     = 3
    select   = 4
    dislike  = -2
    """

    interaction_value = (
        request.interaction_value
    )


    if interaction_value is None:

        interaction_value = (
            get_interaction_value(
                request.interaction_type
            )
        )


    new_interaction = UserInteraction(

        user_id=(
            current_user.user_id
        ),

        item_id=(
            request.item_id
        ),

        interaction_type=(
            request
            .interaction_type
            .lower()
        ),

        interaction_value=(
            interaction_value
        ),
    )


    db.add(new_interaction)

    db.commit()

    db.refresh(new_interaction)


    return new_interaction


# ============================================================
# INTERACTION HISTORY
# ============================================================

@app.get(
    "/interactions/history",
    response_model=InteractionHistoryResponse,
)
def get_user_interaction_history(
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    """
    Returns interaction history and statistics.
    """

    interactions = (
        db.query(
            UserInteraction
        )
        .filter(
            UserInteraction.user_id
            == current_user.user_id
        )
        .order_by(
            UserInteraction
            .created_at
            .desc()
        )
        .all()
    )


    total_interactions = len(
        interactions
    )


    view_count = 0
    click_count = 0
    save_count = 0
    select_count = 0
    dislike_count = 0

    item_ids = []


    for interaction in interactions:

        interaction_type = (
            interaction
            .interaction_type
            .lower()
        )


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


        item_ids.append(
            interaction.item_id
        )


    products = (
        db.query(Product)
        .filter(
            Product.item_id.in_(
                item_ids
            )
        )
        .all()
    )


    products_by_id = {
        product.item_id:
            product

        for product
        in products
    }


    history_items = []


    for interaction in interactions:

        product = (
            products_by_id.get(
                interaction.item_id
            )
        )


        history_items.append({

            "interaction_id":
                interaction.interaction_id,

            "item_id":
                interaction.item_id,

            "interaction_type":
                interaction.interaction_type,

            "interaction_value":
                interaction.interaction_value,

            "created_at":
                interaction.created_at,

            "product_name":
                (
                    product.product_name
                    if product
                    else None
                ),

            "category":
                (
                    product.category
                    if product
                    else None
                ),

            "color":
                (
                    product.color
                    if product
                    else None
                ),

            "style":
                (
                    product.style
                    if product
                    else None
                ),

            "brand":
                (
                    product.brand
                    if product
                    else None
                ),

            "image_url":
                (
                    product.image_url
                    if product
                    else None
                ),

            "product_url":
                (
                    product.product_url
                    if product
                    else None
                ),
        })


    return {

        "stats": {

            "total_interactions":
                total_interactions,

            "view_count":
                view_count,

            "click_count":
                click_count,

            "save_count":
                save_count,

            "select_count":
                select_count,

            "dislike_count":
                dislike_count,
        },

        "interactions":
            history_items,
    }


# ============================================================
# SAMPLE PRODUCTS
# ============================================================

@app.post("/products/sample")
def create_sample_products(
    db: Session = Depends(get_db),
):
    """
    Sample products used to test Chala's Learning Engine.

    Later Koji provides real products.
    """

    sample_products = [

        Product(
            item_id="P001",
            product_name=(
                "White Cotton T-Shirt"
            ),
            category="Tops",
            color=["White"],
            style=["Casual"],
            brand="Gflock",
            occasions=[
                    "Daily wear",
                    "University / college",
                    "Casual outing",
            ],
            product_url=(
                "https://example.com/products/P001"
            ),
            image_url=(
                "https://images.unsplash.com/"
                "photo-1521572163474-6864f9cf17ab"
                "?auto=format&fit=crop&w=900&q=80"
            ),
        ),


        Product(
            item_id="P002",
            product_name="Grey Hoodie",
            category="Hoodies",
            color=["Grey"],
            style=["Comfort"],
            brand="Carnage",
            occasions=[
                    "Daily wear",
                    "University / college",
                    "Travel",
            ],
            product_url=(
                "https://example.com/products/P002"
            ),
            image_url=(
                "https://images.unsplash.com/"
                "photo-1556821840-3a63f95609a7"
                "?auto=format&fit=crop&w=900&q=80"
            ),
        ),


        Product(
            item_id="P003",
            product_name=(
                "Blue Denim Jeans"
            ),
            category="Jeans",
            color=["Blue"],
            style=["Trendy"],
            brand="Kelly Felder",
            occasions=[
                 "Daily wear",
                 "Casual outing",
                 "Travel",
            ],
            product_url=(
                "https://example.com/products/P003"
            ),
            image_url=(
                "https://images.unsplash.com/"
                "photo-1542272604-787c3835535d"
                "?auto=format&fit=crop&w=900&q=80"
            ),
        ),


        Product(
            item_id="P004",
            product_name="Black Blazer",
            category="Blazers",
            color=["Black"],
            style=["Formal"],
            brand="Gflock",
            occasions=[
                    "Office / work",
                    "Special events",
            ],
            product_url=(
                "https://example.com/products/P004"
            ),
            image_url=(
                "https://images.unsplash.com/"
                "photo-1592878904946-b3cd8ae243d0"
                "?auto=format&fit=crop&w=900&q=80"
            ),
        ),


        Product(
            item_id="P005",
            product_name=(
                "Pink Party Skirt"
            ),
            category="Skirts",
            color=["Pink"],
            style=["Party wear"],
            brand="Kelly Felder",
            occasions=[
                    "Party",
                    "Special events",
            ],
            product_url=(
                "https://example.com/products/P005"
            ),
            image_url=(
                "https://images.unsplash.com/"
                "photo-1583496661160-fb5886a13d44"
                "?auto=format&fit=crop&w=900&q=80"
            ),
        ),
    ]


    inserted_count = 0

    skipped_count = 0


    for product in sample_products:

        existing_product = (
            db.query(Product)
            .filter(
                Product.item_id
                == product.item_id
            )
            .first()
        )


        if existing_product:

            existing_product.product_name = (
                product.product_name
            )

            existing_product.category = (
                product.category
            )

            existing_product.color = (
                product.color
            )

            existing_product.style = (
                product.style
            )

            existing_product.brand = (
                product.brand
            )

            existing_product.occasions = (
                product.occasions
            )

            existing_product.product_url = (
                product.product_url
            )

            existing_product.image_url = (
                product.image_url
            )

            skipped_count += 1

            continue


        db.add(product)

        inserted_count += 1


    db.commit()


    return {

        "message":
            "Sample products processed successfully",

        "inserted_count":
            inserted_count,

        "skipped_count":
            skipped_count,
    }


# ============================================================
# UPDATE LEARNING PROFILE
# ============================================================

@app.post("/learning/update")
def update_learning_preferences(
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    """
    Updates learned preferences from
    interaction weight + recency.
    """

    interactions = (
        db.query(
            UserInteraction
        )
        .filter(
            UserInteraction.user_id
            == current_user.user_id
        )
        .all()
    )


    if not interactions:

        return {

            "message":
                "No interactions found for this user",

            "learned_preferences":
                None,
        }


    item_ids = [
        interaction.item_id
        for interaction
        in interactions
    ]


    products = (
        db.query(Product)
        .filter(
            Product.item_id.in_(
                item_ids
            )
        )
        .all()
    )


    products_by_id = {
        product.item_id:
            product

        for product
        in products
    }


    learned_data = (
        calculate_learned_preferences(
            interactions=interactions,
            products_by_id=products_by_id,
        )
    )


    existing_learned_preferences = (
        db.query(
            UserLearnedPreference
        )
        .filter(
            UserLearnedPreference.user_id
            == current_user.user_id
        )
        .first()
    )


    if existing_learned_preferences:

        existing_learned_preferences.category_weights = (
            learned_data[
                "category_weights"
            ]
        )

        existing_learned_preferences.color_weights = (
            learned_data[
                "color_weights"
            ]
        )

        existing_learned_preferences.style_weights = (
            learned_data[
                "style_weights"
            ]
        )

        existing_learned_preferences.brand_weights = (
            learned_data[
                "brand_weights"
            ]
        )

        existing_learned_preferences.occasion_weights = (
            learned_data[
                "occasion_weights"
            ]
        )


        db.commit()

        db.refresh(
            existing_learned_preferences
        )


        return {

            "message": (
                "Learned preferences "
                "updated successfully"
            ),

            "learned_preferences":
                existing_learned_preferences,
        }


    new_learned_preferences = (
        UserLearnedPreference(

            user_id=(
                current_user.user_id
            ),

            category_weights=(
                learned_data[
                    "category_weights"
                ]
            ),

            color_weights=(
                learned_data[
                    "color_weights"
                ]
            ),

            style_weights=(
                learned_data[
                    "style_weights"
                ]
            ),

            brand_weights=(
                learned_data[
                    "brand_weights"
                ]
            ),
            occasion_weights=(
                learned_data[
                    "occasion_weights"
                ]
            ),

        )
    )


    db.add(
        new_learned_preferences
    )

    db.commit()

    db.refresh(
        new_learned_preferences
    )


    return {

        "message": (
            "Learned preferences "
            "created successfully"
        ),

        "learned_preferences":
            new_learned_preferences,
    }


# ============================================================
# OLD FASHION EMBEDDING TEST ENDPOINTS
# ============================================================

@app.post("/ml/test-image-embedding")
def test_image_embedding():
    """
    Temporary FashionEmbedder test endpoint.
    """

    image_url = (
        "https://images.unsplash.com/"
        "photo-1483985988355-763728e1935b"
        "?auto=format&fit=crop&w=900&q=80"
    )


    embedding = get_image_embedding(
        image_url
    )


    return {

        "message":
            "Image embedding created successfully",

        "model_name":
            "McClain/fashion-embedder",

        "image_url":
            image_url,

        "embedding_dimension":
            len(embedding),

        "first_10_values":
            embedding[:10],
    }


@app.post("/ml/test-user-vector")
def test_user_preference_vector():
    """
    Temporary FashionEmbedder user-vector test.
    """

    interaction_items = [

        {
            "item_id": "P001",
            "image_url": (
                "https://images.unsplash.com/"
                "photo-1543076447-215ad9ba6923"
                "?auto=format&fit=crop&w=900&q=80"
            ),
            "interaction_weight": 2.0,
        },

        {
            "item_id": "P002",
            "image_url": (
                "https://images.unsplash.com/"
                "photo-1483985988355-763728e1935b"
                "?auto=format&fit=crop&w=900&q=80"
            ),
            "interaction_weight": 3.0,
        },

        {
            "item_id": "P003",
            "image_url": (
                "https://images.unsplash.com/"
                "photo-1594223274512-ad4803739b7c"
                "?auto=format&fit=crop&w=900&q=80"
            ),
            "interaction_weight": 4.0,
        },
    ]


    user_vector = (
        create_user_preference_vector(
            interaction_items
        )
    )


    return {

        "message": (
            "User preference vector "
            "created successfully"
        ),

        "model_name":
            "McClain/fashion-embedder",

        "embedding_dimension":
            len(user_vector),

        "first_10_values":
            user_vector[:10],

        "used_items":
            interaction_items,
    }


@app.post(
    "/ml/update-current-user-vector"
)
def update_current_user_vector(
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    """
    Creates and saves an embedding-based
    user preference vector.
    """

    interactions = (
        db.query(
            UserInteraction
        )
        .filter(
            UserInteraction.user_id
            == current_user.user_id
        )
        .all()
    )


    if not interactions:

        return {

            "message":
                "No interactions found for this user",

            "user_id":
                current_user.user_id,

            "user_preference_vector":
                None,
        }


    item_ids = [
        interaction.item_id
        for interaction
        in interactions
    ]


    products = (
        db.query(Product)
        .filter(
            Product.item_id.in_(
                item_ids
            )
        )
        .all()
    )


    products_by_id = {
        product.item_id:
            product

        for product
        in products
    }


    interaction_items = []


    for interaction in interactions:

        product = (
            products_by_id.get(
                interaction.item_id
            )
        )


        if product is None:
            continue


        if not product.image_url:
            continue


        interaction_items.append({

            "item_id":
                interaction.item_id,

            "image_url":
                product.image_url,

            "interaction_type":
                interaction.interaction_type,

            "interaction_weight":
                interaction.interaction_value,
        })


    if not interaction_items:

        return {

            "message": (
                "No valid product image URLs "
                "found for this user's interactions"
            ),

            "user_id":
                current_user.user_id,

            "user_preference_vector":
                None,
        }


    user_vector = (
        create_user_preference_vector(
            interaction_items
        )
    )


    if not user_vector:

        return {

            "message":
                "Could not create user preference vector",

            "user_id":
                current_user.user_id,

            "user_preference_vector":
                None,
        }


    existing_ml_preferences = (
        db.query(
            UserMLPreference
        )
        .filter(
            UserMLPreference.user_id
            == current_user.user_id
        )
        .first()
    )


    if existing_ml_preferences:

        existing_ml_preferences.model_name = (
            "McClain/fashion-embedder"
        )

        existing_ml_preferences.embedding_dimension = (
            len(user_vector)
        )

        existing_ml_preferences.user_preference_vector = (
            user_vector
        )

        existing_ml_preferences.used_interaction_count = (
            len(interaction_items)
        )


        db.commit()

        db.refresh(
            existing_ml_preferences
        )


        saved_ml_preferences = (
            existing_ml_preferences
        )

        message = (
            "Current user ML preference vector "
            "updated and saved successfully"
        )


    else:

        new_ml_preferences = (
            UserMLPreference(

                user_id=(
                    current_user.user_id
                ),

                model_name=(
                    "McClain/fashion-embedder"
                ),

                embedding_dimension=(
                    len(user_vector)
                ),

                user_preference_vector=(
                    user_vector
                ),

                used_interaction_count=(
                    len(interaction_items)
                ),
            )
        )


        db.add(
            new_ml_preferences
        )

        db.commit()

        db.refresh(
            new_ml_preferences
        )


        saved_ml_preferences = (
            new_ml_preferences
        )

        message = (
            "Current user ML preference vector "
            "created and saved successfully"
        )


    return {

        "message":
            message,

        "user_id":
            current_user.user_id,

        "model_name":
            saved_ml_preferences.model_name,

        "embedding_dimension":
            saved_ml_preferences
            .embedding_dimension,

        "first_10_values":
            saved_ml_preferences
            .user_preference_vector[:10],

        "used_interaction_count":
            saved_ml_preferences
            .used_interaction_count,

        "used_items":
            interaction_items,
    }


@app.get(
    "/ml/current-user-vector-summary"
)
def get_current_user_vector_summary(
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    """
    Returns summary of saved
    FashionEmbedder user vector.
    """

    ml_preferences = (
        db.query(
            UserMLPreference
        )
        .filter(
            UserMLPreference.user_id
            == current_user.user_id
        )
        .first()
    )


    if not ml_preferences:

        return {

            "message": (
                "No saved ML preference vector "
                "found for this user"
            ),

            "user_id":
                current_user.user_id,

            "ml_preferences":
                None,
        }


    return {

        "message":
            "Saved ML preference vector found",

        "user_id":
            current_user.user_id,

        "model_name":
            ml_preferences.model_name,

        "embedding_dimension":
            ml_preferences.embedding_dimension,

        "used_interaction_count":
            ml_preferences.used_interaction_count,

        "first_10_values":
            ml_preferences
            .user_preference_vector[:10],

        "updated_at":
            ml_preferences.updated_at,
    }