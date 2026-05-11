from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)

    # Google Sign-In unique user ID
    google_sub = Column(String, unique=True, nullable=False, index=True)

    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    profile_picture = Column(String, nullable=True)

    # For now this will always be "google"
    auth_provider = Column(String, nullable=False, default="google")

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class UserOnboardingPreference(Base):
    __tablename__ = "user_onboarding_preferences"

    preference_id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)

    preferred_categories = Column(JSONB, nullable=False)
    preferred_colors = Column(JSONB, nullable=False)
    preferred_styles = Column(JSONB, nullable=False)

    price_min = Column(Float, nullable=True)
    price_max = Column(Float, nullable=True)

    occasions = Column(JSONB, nullable=False)
    preferred_patterns = Column(JSONB, nullable=True)
    extra_preferences = Column(JSONB, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class UserInteraction(Base):
    __tablename__ = "user_interactions"

    interaction_id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)

    # This item_id comes from Koji's products table
    item_id = Column(String, nullable=False)

    # Example: view, click, save, select, dislike
    interaction_type = Column(String, nullable=False)

    # Example: view = 1, click = 2, save = 3, dislike = -2
    interaction_value = Column(Float, nullable=False, default=1.0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class UserLearnedPreference(Base):
    __tablename__ = "user_learned_preferences"

    learned_id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, unique=True)

    category_weights = Column(JSONB, nullable=False)
    color_weights = Column(JSONB, nullable=False)
    style_weights = Column(JSONB, nullable=False)
    brand_weights = Column(JSONB, nullable=True)

    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Product(Base):
    """
    This table belongs mainly to Koji's module.

    We include this model here only so Chala's Learning Engine can read product details
    using item_id when updating user preferences.
    """

    __tablename__ = "products"

    item_id = Column(String, primary_key=True, index=True)

    product_name = Column(String, nullable=True)
    category = Column(String, nullable=False)

    # Example: ["black", "white"]
    color = Column(JSONB, nullable=True)

    # Example: ["casual", "formal"]
    style = Column(JSONB, nullable=True)

    brand = Column(String, nullable=True)
    product_url = Column(String, nullable=True)
    image_url = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

class UserMLPreference(Base):
    __tablename__ = "user_ml_preferences"

    ml_preference_id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, unique=True)

    model_name = Column(String, nullable=False)
    embedding_dimension = Column(Integer, nullable=False)

    # Stores the 768-dimensional user preference vector
    user_preference_vector = Column(JSONB, nullable=False)

    used_interaction_count = Column(Integer, nullable=False, default=0)

    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())