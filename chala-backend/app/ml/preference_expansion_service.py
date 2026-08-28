from pathlib import Path
import json

import joblib
import pandas as pd


# ============================================================
# MODEL FILE LOCATIONS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "models"

MODEL_PATH = (
    MODEL_DIR
    / "outfitiq_preference_logistic_model.pkl"
)

FEATURE_NAMES_PATH = (
    MODEL_DIR
    / "logistic_feature_names.json"
)

OUTPUT_NAMES_PATH = (
    MODEL_DIR
    / "logistic_output_names.json"
)

EXPANSION_POLICY_PATH = (
    MODEL_DIR
    / "logistic_expansion_policy.json"
)

MODEL_METADATA_PATH = (
    MODEL_DIR
    / "logistic_model_metadata.json"
)


# ============================================================
# LOAD TRAINED MODEL + CONFIGURATION
# ============================================================

preference_model = joblib.load(
    MODEL_PATH
)

with open(
    FEATURE_NAMES_PATH,
    "r",
    encoding="utf-8"
) as file:
    feature_names = json.load(file)


with open(
    OUTPUT_NAMES_PATH,
    "r",
    encoding="utf-8"
) as file:
    output_names = json.load(file)


with open(
    EXPANSION_POLICY_PATH,
    "r",
    encoding="utf-8"
) as file:
    expansion_policy = json.load(file)


with open(
    MODEL_METADATA_PATH,
    "r",
    encoding="utf-8"
) as file:
    model_metadata = json.load(file)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def _unique(values):
    """
    Remove duplicates while keeping original order.
    """

    result = []

    for value in values:
        if value not in result:
            result.append(value)

    return result


def _remove_prefix(
    feature_name: str,
    prefix: str
) -> str:
    """
    Example:

    color_Cream -> Cream
    category_Jackets -> Jackets
    """

    if feature_name.startswith(prefix):
        return feature_name[len(prefix):]

    return feature_name


def _create_empty_model_input():
    """
    Creates the 45-feature input expected by
    the trained Logistic Regression model.
    """

    return pd.DataFrame(
        0.0,
        index=[0],
        columns=feature_names
    )


def _convert_to_model_features(
    values,
    prefix
):
    """
    Converts application preferences into
    feature names expected by the model.

    Example:

    Red -> color_Red
    Blazers -> category_Blazers
    """

    converted = []

    for value in values or []:

        # Temporary application/model naming match
        if value == "Comfort":
            value = "Comfort wear"

        feature = f"{prefix}{value}"

        if feature in feature_names:
            converted.append(feature)

    return converted


def _get_baseline_probabilities():
    """
    Model probabilities for an empty profile.

    Used to calculate uplift:
    probability with preference - baseline probability
    """

    empty_user = _create_empty_model_input()

    return preference_model.predict_proba(
        empty_user
    )[0]


baseline_probabilities = (
    _get_baseline_probabilities()
)


# ============================================================
# SINGLE GROUP ML EXPANSION
# ============================================================

def _expand_single_group(
    selected_values,
    prefix,
    method,
    top_k,
    excluded_values=None
):
    """
    Runs group-isolated Logistic Regression expansion.

    Example:

    Current categories
        ↓
    Only category features are sent to the model
        ↓
    Model predicts other likely categories.

    There is NO hard-coded same-family restriction.

    Therefore the model learns the pattern:

        Users who like X
        may also tend to like Y.
    """

    if not selected_values:
        return []


    excluded_values = set(
        excluded_values or []
    )


    selected_features = (
        _convert_to_model_features(
            selected_values,
            prefix
        )
    )


    if not selected_features:
        return []


    # --------------------------------------------------------
    # CREATE GROUP-ISOLATED INPUT
    # --------------------------------------------------------

    isolated_user = (
        _create_empty_model_input()
    )


    for feature in selected_features:

        isolated_user.loc[
            0,
            feature
        ] = 1.0


    # --------------------------------------------------------
    # RUN TRAINED LOGISTIC REGRESSION MODEL
    # --------------------------------------------------------

    probabilities = (
        preference_model.predict_proba(
            isolated_user
        )[0]
    )


    uplift = (
        probabilities
        - baseline_probabilities
    )


    # --------------------------------------------------------
    # FIND OUTPUTS FROM THIS ATTRIBUTE GROUP
    # --------------------------------------------------------

    group_indices = [
        index
        for index, output_name
        in enumerate(output_names)
        if output_name.startswith(prefix)
    ]


    candidates = []


    # --------------------------------------------------------
    # BUILD ML CANDIDATES
    # --------------------------------------------------------

    for index in group_indices:

        output_name = (
            output_names[index]
        )


        # Do not return something
        # already present in current preferences.
        if output_name in selected_features:
            continue


        plain_preference = (
            _remove_prefix(
                output_name,
                prefix
            )
        )


        # ----------------------------------------------------
        # NEGATIVE BEHAVIOR PROTECTION
        # ----------------------------------------------------

        # Explicit disliked/negative preferences
        # should not be automatically reintroduced.
        if plain_preference in excluded_values:
            continue


        probability = float(
            probabilities[index]
        )

        uplift_score = float(
            uplift[index]
        )


        # ----------------------------------------------------
        # USE FINAL VALIDATED RANKING POLICY
        # ----------------------------------------------------

        if method == "probability":

            ranking_score = probability

        elif method == "uplift":

            ranking_score = uplift_score

        else:

            continue


        candidates.append({
            "model_feature":
                output_name,

            "preference":
                plain_preference,

            "probability":
                round(
                    probability,
                    4
                ),

            "uplift":
                round(
                    uplift_score,
                    4
                ),

            "ranking_score":
                ranking_score,

            "ranking_method":
                method
        })


    # --------------------------------------------------------
    # SORT USING MODEL SCORE
    # --------------------------------------------------------

    candidates.sort(
        key=lambda item:
            item["ranking_score"],
        reverse=True
    )


    # --------------------------------------------------------
    # TAKE TOP-K
    # --------------------------------------------------------

    selected_candidates = (
        candidates[:top_k]
    )


    # Internal value is not needed by frontend.
    for candidate in selected_candidates:

        candidate.pop(
            "ranking_score",
            None
        )


    return selected_candidates


# ============================================================
# MAIN PREFERENCE EXPANSION
# ============================================================

def expand_onboarding_preferences(
    preferred_colors=None,
    preferred_categories=None,
    preferred_styles=None,
    occasions=None,
    choice_priorities=None,
    preferred_brands=None,
    excluded_colors=None,
    excluded_categories=None,
    excluded_styles=None
):
    """
    Expands the user's current preferences using
    the trained Multi-label Logistic Regression model.

    ML interpretation:

        Users who currently show preference X
        may also tend to show preference Y.

    FINAL MODEL POLICY:

    Color:
        Top 1 using probability

    Category:
        Top 2 using uplift

    Style:
        Top 1 using uplift

    Occasion:
        No automatic expansion

    Brand:
        Not predicted by the ML model

    Choice priority:
        Not predicted by the ML model
    """


    preferred_colors = (
        preferred_colors or []
    )

    preferred_categories = (
        preferred_categories or []
    )

    preferred_styles = (
        preferred_styles or []
    )

    occasions = (
        occasions or []
    )

    choice_priorities = (
        choice_priorities or []
    )

    preferred_brands = (
        preferred_brands or []
    )

    excluded_colors = (
        excluded_colors or []
    )

    excluded_categories = (
        excluded_categories or []
    )

    excluded_styles = (
        excluded_styles or []
    )


    # ========================================================
    # COLOR ML EXPANSION
    # ========================================================

    color_policy = (
        expansion_policy["color"]
    )


    color_expansions = (
        _expand_single_group(
            selected_values=(
                preferred_colors
            ),
            prefix="color_",
            method=(
                color_policy["method"]
            ),
            top_k=(
                color_policy["top_k"]
            ),
            excluded_values=(
                excluded_colors
            )
        )
    )


    # ========================================================
    # CATEGORY ML EXPANSION
    # ========================================================

    category_policy = (
        expansion_policy["category"]
    )


    category_expansions = (
        _expand_single_group(
            selected_values=(
                preferred_categories
            ),
            prefix="category_",
            method=(
                category_policy["method"]
            ),
            top_k=(
                category_policy["top_k"]
            ),
            excluded_values=(
                excluded_categories
            )
        )
    )


    # ========================================================
    # STYLE ML EXPANSION
    # ========================================================

    style_policy = (
        expansion_policy["style"]
    )


    style_expansions = (
        _expand_single_group(
            selected_values=(
                preferred_styles
            ),
            prefix="style_",
            method=(
                style_policy["method"]
            ),
            top_k=(
                style_policy["top_k"]
            ),
            excluded_values=(
                excluded_styles
            )
        )
    )


    # ========================================================
    # OCCASION
    # ========================================================

    # Final validated policy:
    # no automatic occasion expansion.
    occasion_expansions = []


    # ========================================================
    # BUILD FINAL ENRICHED VALUES
    # ========================================================

    expanded_colors = [
        item["preference"]
        for item in color_expansions
    ]


    expanded_categories = [
        item["preference"]
        for item in category_expansions
    ]


    expanded_styles = [
        item["preference"]
        for item in style_expansions
    ]


    enriched_colors = (
        _unique(
            preferred_colors
            + expanded_colors
        )
    )


    enriched_categories = (
        _unique(
            preferred_categories
            + expanded_categories
        )
    )


    enriched_styles = (
        _unique(
            preferred_styles
            + expanded_styles
        )
    )


    # ========================================================
    # RESPONSE
    # ========================================================

    return {

        "original_preferences": {

            "preferred_colors":
                preferred_colors,

            "preferred_categories":
                preferred_categories,

            "preferred_styles":
                preferred_styles,

            "occasions":
                occasions,

            "choice_priorities":
                choice_priorities,

            "preferred_brands":
                preferred_brands
        },


        "ml_expansions": {

            "colors":
                color_expansions,

            "categories":
                category_expansions,

            "styles":
                style_expansions,

            "occasions":
                occasion_expansions
        },


        "enriched_preferences": {

            "preferred_colors":
                enriched_colors,

            "preferred_categories":
                enriched_categories,

            "preferred_styles":
                enriched_styles,

            "occasions":
                occasions,

            "choice_priorities":
                choice_priorities,

            "preferred_brands":
                preferred_brands
        }
    }


# ============================================================
# MODEL INFORMATION
# ============================================================

def get_preference_model_info():
    """
    Returns information about the trained model.
    """

    return {

        "model_loaded":
            True,

        "model_type":
            model_metadata.get(
                "model_type"
            ),

        "input_features":
            len(feature_names),

        "output_labels":
            len(output_names),

        "expansion_policy":
            expansion_policy
    }

