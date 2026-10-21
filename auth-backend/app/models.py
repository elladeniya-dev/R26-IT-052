from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Float,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    google_sub = Column(
        String,
        unique=True,
        nullable=False,
        index=True,
    )

    full_name = Column(
        String,
        nullable=False,
    )

    email = Column(
        String,
        unique=True,
        nullable=False,
        index=True,
    )

    profile_picture = Column(
        String,
        nullable=True,
    )

    auth_provider = Column(
        String,
        nullable=False,
        default="google",
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class UserOnboardingPreference(Base):
    __tablename__ = "user_onboarding_preferences"

    preference_id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    user_id = Column(
        Integer,
        ForeignKey("users.user_id"),
        nullable=False,
    )

    preferred_categories = Column(
        JSONB,
        nullable=False,
    )

    preferred_colors = Column(
        JSONB,
        nullable=False,
    )

    preferred_styles = Column(
        JSONB,
        nullable=False,
    )

    price_min = Column(
        Float,
        nullable=True,
    )

    price_max = Column(
        Float,
        nullable=True,
    )

    occasions = Column(
        JSONB,
        nullable=False,
    )

    preferred_patterns = Column(
        JSONB,
        nullable=True,
    )

    choice_priorities = Column(
        JSONB,
        nullable=True,
    )

    preferred_brands = Column(
        JSONB,
        nullable=True,
    )

    extra_preferences = Column(
        JSONB,
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class UserInteraction(Base):
    __tablename__ = "user_interactions"

    interaction_id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    user_id = Column(
        Integer,
        ForeignKey("users.user_id"),
        nullable=False,
    )

    item_id = Column(
        String,
        nullable=False,
    )

    interaction_type = Column(
        String,
        nullable=False,
    )

    interaction_value = Column(
        Float,
        nullable=False,
        default=1.0,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class UserLearnedPreference(Base):
    __tablename__ = "user_learned_preferences"

    learned_id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    user_id = Column(
        Integer,
        ForeignKey("users.user_id"),
        nullable=False,
        unique=True,
    )

    category_weights = Column(
        JSONB,
        nullable=False,
    )

    color_weights = Column(
        JSONB,
        nullable=False,
    )

    style_weights = Column(
        JSONB,
        nullable=False,
    )

    # Dynamically learned from product brands.
    brand_weights = Column(
        JSONB,
        nullable=True,
    )

    # NEW:
    # Dynamically learned from product occasions.
    occasion_weights = Column(
        JSONB,
        nullable=True,
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class Product(Base):
    """
    Product data mainly belongs to Koji's module.

    Chala's Learning Engine reads these attributes
    using item_id to learn user preferences.
    """

    __tablename__ = "products"

    item_id = Column(
        String,
        primary_key=True,
        index=True,
    )

    product_name = Column(
        String,
        nullable=True,
    )

    category = Column(
        String,
        nullable=False,
    )

    color = Column(
        JSONB,
        nullable=True,
    )

    style = Column(
        JSONB,
        nullable=True,
    )

    brand = Column(
        String,
        nullable=True,
    )

    # NEW:
    # Example:
    # ["Daily wear", "University / college"]
    #
    # or:
    # ["Office / work", "Special events"]
    occasions = Column(
        JSONB,
        nullable=True,
    )

    product_url = Column(
        String,
        nullable=True,
    )

    image_url = Column(
        String,
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )