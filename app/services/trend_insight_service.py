def pluralize_fashion_term(value: str) -> str:
    value_lower = value.lower().strip()

    irregular_plural_map = {
        "dress": "Dresses",
        "column dress": "Column Dresses",
        "polo dress": "Polo Dresses",
        "wrap dress": "Wrap Dresses",
        "mini dress": "Mini Dresses",
        "maxi dress": "Maxi Dresses",
        "tshirt": "T-shirts",
        "crop top": "Crop Tops",
    }

    if value_lower in irregular_plural_map:
        return irregular_plural_map[value_lower]

    if value_lower.endswith("s"):
        return value.title()

    return f"{value.title()}s"


def build_trend_title(attribute_type: str, attribute_value: str, trend_status: str) -> str:
    value = attribute_value.title()

    if attribute_type.startswith("new_arrival_"):
        base_type = attribute_type.removeprefix("new_arrival_")
        label = pluralize_fashion_term(attribute_value) if base_type == "category" else f"{value} {base_type}s"
        if trend_status == "rising":
            return f"New arrivals in {label} are surging"
        if trend_status == "stable":
            return f"New arrivals in {label} are steady"
        return f"New arrivals in {label} have slowed down"

    if trend_status == "rising":
        if attribute_type == "category":
            return f"{pluralize_fashion_term(attribute_value)} are trending now"
        if attribute_type == "color":
            return f"{value} shades are gaining popularity"
        if attribute_type == "pattern":
            return f"{value} styles are trending"
        if attribute_type == "material":
            return f"{value} fabric is becoming popular"
        if attribute_type == "style":
            return f"{value} style is trending"

        return f"{value} is trending now"

    if trend_status == "stable":
        return f"{value} remains a steady fashion choice"

    return f"{value} is currently a weaker trend"


def build_trend_summary(
    attribute_type: str,
    attribute_value: str,
    trend_status: str,
) -> str:
    value = attribute_value.title()

    if trend_status == "rising":
        return (
            f"{value} is showing strong growth in recent women’s fashion trend data. "
            f"This means it is appearing more actively in current fashion collections."
        )

    if trend_status == "stable":
        return (
            f"{value} is maintaining a consistent presence in recent fashion data. "
            f"It is not rapidly increasing, but it remains relevant."
        )

    return (
        f"{value} is showing low or declining trend strength in the current fashion data. "
        f"It may not be a major style focus right now."
    )


def build_trend_reason(
    attribute_type: str,
    attribute_value: str,
    trend_status: str,
) -> str:
    value = attribute_value.title()

    if trend_status == "rising":
        return (
            f"The system detected increasing activity for {value} based on trend score, "
            f"growth rate, ranking movement, and ML classification."
        )

    if trend_status == "stable":
        return (
            f"The system detected that {value} has a balanced trend pattern without "
            f"major growth or decline."
        )

    return (
        f"The system detected that {value} has lower trend score or negative growth "
        f"compared with stronger trends."
    )


def get_display_badge(trend_status: str) -> str:
    if trend_status == "rising":
        return "🔥 Rising Trend"

    if trend_status == "stable":
        return "✨ Stable Trend"

    return "📉 Weak Trend"
