from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import timedelta

from app.database import engine, Base, get_db
from app import models, schemas
from app.ml_prediction_service import trend_ml_service

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Gividu Trend Analysis Engine",
    description="Trend Analysis backend service for Smart Fashion Assistant",
    version="1.0.0"
)


@app.get("/")
def home():
    return {
        "message": "Gividu Trend Analysis Engine is running successfully"
    }


@app.get("/test-db")
def test_database_connection(db: Session = Depends(get_db)):
    try:
        result = db.execute(text("SELECT 1"))
        value = result.scalar()

        return {
            "database_connected": True,
            "test_result": value,
            "message": "PostgreSQL connection successful"
        }

    except Exception as e:
        return {
            "database_connected": False,
            "error": str(e)
        }


@app.post("/products/", response_model=schemas.ProductResponse)
def create_product(product: schemas.ProductCreate, db: Session = Depends(get_db)):
    existing_product = db.query(models.Product).filter(
        models.Product.item_id == product.item_id
    ).first()

    if existing_product:
        raise HTTPException(
            status_code=400,
            detail="Product with this item_id already exists"
        )

    new_product = models.Product(
        item_id=product.item_id,
        title=product.title,
        category=product.category,
        subcategory=product.subcategory,
        color=product.color,
        style=product.style,
        brand=product.brand,
        price=product.price,
        currency=product.currency,
        material=product.material,
        pattern=product.pattern,
        fit_type=product.fit_type,
        target_gender=product.target_gender,
        image_url=product.image_url,
        product_url=product.product_url,
        source=product.source,
        description=product.description,
        availability=product.availability,
        collected_at=product.collected_at
    )

    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    return new_product


@app.get("/products/")
def get_all_products(db: Session = Depends(get_db)):
    products = db.query(models.Product).all()

    return {
        "total_products": len(products),
        "products": products
    }


@app.post("/product-metrics/", response_model=schemas.ProductTrendMetricResponse)
def create_product_metric(
    metric: schemas.ProductTrendMetricCreate,
    db: Session = Depends(get_db)
):
    product = db.query(models.Product).filter(
        models.Product.item_id == metric.item_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found. Add product before adding trend metrics."
        )

    new_metric = models.ProductTrendMetric(
        item_id=metric.item_id,
        view_count=metric.view_count,
        wishlist_count=metric.wishlist_count,
        sales_volume=metric.sales_volume,
        social_mentions=metric.social_mentions,
        availability=metric.availability,
        recorded_at=metric.recorded_at
    )

    db.add(new_metric)
    db.commit()
    db.refresh(new_metric)

    return new_metric


@app.get("/product-metrics/")
def get_all_product_metrics(db: Session = Depends(get_db)):
    metrics = db.query(models.ProductTrendMetric).all()

    return {
        "total_metrics": len(metrics),
        "metrics": metrics
    }

@app.post("/trend-observations/bulk")
def create_bulk_trend_observations(
    bulk_data: schemas.BulkTrendObservationCreate,
    db: Session = Depends(get_db)
):
    if not bulk_data.observations:
        raise HTTPException(
            status_code=400,
            detail="Observation list cannot be empty"
        )

    new_observations = []

    for observation in bulk_data.observations:
        new_observation = models.TrendObservation(
            source_name=observation.source_name,
            source_type=observation.source_type,
            attribute_type=observation.attribute_type,
            attribute_value=observation.attribute_value,
            keyword=observation.keyword,
            mention_count=observation.mention_count,
            rank_position=observation.rank_position,
            collected_at=observation.collected_at
        )

        db.add(new_observation)
        new_observations.append(new_observation)

    db.commit()

    for observation in new_observations:
        db.refresh(observation)

    return {
        "message": "Bulk trend observations inserted successfully",
        "inserted_count": len(new_observations),
        "observations": new_observations
    }

@app.post("/trend-observations/", response_model=schemas.TrendObservationResponse)
def create_trend_observation(
    observation: schemas.TrendObservationCreate,
    db: Session = Depends(get_db)
):
    new_observation = models.TrendObservation(
        source_name=observation.source_name,
        source_type=observation.source_type,
        attribute_type=observation.attribute_type,
        attribute_value=observation.attribute_value,
        keyword=observation.keyword,
        mention_count=observation.mention_count,
        rank_position=observation.rank_position,
        collected_at=observation.collected_at
    )

    db.add(new_observation)
    db.commit()
    db.refresh(new_observation)

    return new_observation


@app.get("/trend-observations/")
def get_all_trend_observations(db: Session = Depends(get_db)):
    observations = db.query(models.TrendObservation).all()

    return {
        "total_observations": len(observations),
        "observations": observations
    }

@app.get("/trends/analyze")
def analyze_trends(db: Session = Depends(get_db)):
    observations = db.query(models.TrendObservation).all()

    if not observations:
        raise HTTPException(
            status_code=404,
            detail="No trend observations found. Add trend observations first."
        )

    latest_date = max(obs.collected_at for obs in observations)

    current_start = latest_date - timedelta(days=7)
    current_end = latest_date

    previous_start = current_start - timedelta(days=7)
    previous_end = current_start

    current_counts = {}
    previous_counts = {}
    current_ranks = {}

    for obs in observations:
        key = (obs.attribute_type.lower(), obs.attribute_value.lower())

        if current_start <= obs.collected_at <= current_end:
            current_counts[key] = current_counts.get(key, 0) + obs.mention_count

            if obs.rank_position is not None:
                if key not in current_ranks:
                    current_ranks[key] = []
                current_ranks[key].append(obs.rank_position)

        elif previous_start <= obs.collected_at < previous_end:
            previous_counts[key] = previous_counts.get(key, 0) + obs.mention_count

    all_keys = set(current_counts.keys()) | set(previous_counts.keys())

    if not all_keys:
        raise HTTPException(
            status_code=404,
            detail="No observations found in current or previous analysis windows."
        )

    max_current_count = max(current_counts.values()) if current_counts else 1

    # Prevent duplicate trend signals for the same weekly period
    db.query(models.TrendSignal).filter(
        models.TrendSignal.time_window == "weekly",
        models.TrendSignal.start_date == current_start,
        models.TrendSignal.end_date == current_end
    ).delete(synchronize_session=False)

    analyzed_results = []

    for key in all_keys:
        attribute_type, attribute_value = key

        current_count = current_counts.get(key, 0)
        previous_count = previous_counts.get(key, 0)

        if previous_count == 0:
            growth_rate = 1.0 if current_count > 0 else 0.0
        else:
            growth_rate = (current_count - previous_count) / previous_count

        # 1. Growth score
        growth_score = max(min(growth_rate, 1.0), 0.0)

        # 2. Count score normalized based on highest count in this batch
        count_score = current_count / max_current_count if max_current_count > 0 else 0.0
        count_score = max(min(count_score, 1.0), 0.0)

        # 3. Rank score: lower rank_position means stronger trend
        ranks = current_ranks.get(key, [])

        if ranks:
            average_rank = sum(ranks) / len(ranks)
            rank_score = 1 - ((average_rank - 1) / 20)
            rank_score = max(min(rank_score, 1.0), 0.0)
        else:
            average_rank = None
            rank_score = 0.5

        trend_score = round(
            (0.50 * growth_score) +
            (0.30 * count_score) +
            (0.20 * rank_score),
            2
        )

        growth_rate = round(growth_rate, 2)

        new_signal = models.TrendSignal(
            attribute_type=attribute_type,
            attribute_value=attribute_value,
            trend_score=trend_score,
            growth_rate=growth_rate,
            time_window="weekly",
            start_date=current_start,
            end_date=current_end
        )

        db.add(new_signal)

        analyzed_results.append({
            "attribute_type": attribute_type,
            "attribute_value": attribute_value,
            "current_count": current_count,
            "previous_count": previous_count,
            "growth_rate": growth_rate,
            "growth_score": round(growth_score, 2),
            "count_score": round(count_score, 2),
            "rank_score": round(rank_score, 2),
            "average_rank": average_rank,
            "trend_score": trend_score,
            "time_window": "weekly",
            "start_date": current_start,
            "end_date": current_end
        })

    db.commit()

    analyzed_results.sort(
        key=lambda item: item["trend_score"],
        reverse=True
    )

    return {
        "message": "Trend analysis completed successfully",
        "total_trends_analyzed": len(analyzed_results),
        "formula": "trend_score = 0.50 * growth_score + 0.30 * count_score + 0.20 * rank_score",
        "current_period": {
            "start_date": current_start,
            "end_date": current_end
        },
        "previous_period": {
            "start_date": previous_start,
            "end_date": previous_end
        },
        "trends": analyzed_results
    }


@app.get("/trends")
def get_all_trends(db: Session = Depends(get_db)):
    latest_trend = db.query(models.TrendSignal).order_by(
        models.TrendSignal.end_date.desc()
    ).first()

    if not latest_trend:
        return {
            "total_trends": 0,
            "trends": []
        }

    trends = db.query(models.TrendSignal).filter(
        models.TrendSignal.time_window == latest_trend.time_window,
        models.TrendSignal.start_date == latest_trend.start_date,
        models.TrendSignal.end_date == latest_trend.end_date
    ).order_by(
        models.TrendSignal.trend_score.desc()
    ).all()

    return {
        "time_window": latest_trend.time_window,
        "start_date": latest_trend.start_date,
        "end_date": latest_trend.end_date,
        "total_trends": len(trends),
        "trends": trends
    }

@app.get("/trends/history")
def get_trend_history(db: Session = Depends(get_db)):
    trends = db.query(models.TrendSignal).order_by(
        models.TrendSignal.end_date.desc(),
        models.TrendSignal.trend_score.desc()
    ).all()

    return {
        "total_trends": len(trends),
        "trends": trends
    }

@app.get("/trends/{attribute_type}")
def get_trends_by_attribute_type(
    attribute_type: str,
    db: Session = Depends(get_db)
):
    latest_trend = db.query(models.TrendSignal).order_by(
        models.TrendSignal.end_date.desc()
    ).first()

    if not latest_trend:
        raise HTTPException(
            status_code=404,
            detail="No trend data found"
        )

    trends = db.query(models.TrendSignal).filter(
        models.TrendSignal.attribute_type == attribute_type.lower(),
        models.TrendSignal.time_window == latest_trend.time_window,
        models.TrendSignal.start_date == latest_trend.start_date,
        models.TrendSignal.end_date == latest_trend.end_date
    ).order_by(
        models.TrendSignal.trend_score.desc()
    ).all()

    if not trends:
        raise HTTPException(
            status_code=404,
            detail=f"No latest trends found for attribute_type: {attribute_type}"
        )

    return {
        "attribute_type": attribute_type.lower(),
        "time_window": latest_trend.time_window,
        "start_date": latest_trend.start_date,
        "end_date": latest_trend.end_date,
        "total_trends": len(trends),
        "trends": trends
    }

@app.post("/ml/predict-trend", response_model=schemas.TrendPredictionResponse)
def predict_trend_with_ml(request: schemas.TrendPredictionRequest):
    prediction = trend_ml_service.predict_trend_label(
        attribute_type=request.attribute_type,
        attribute_value=request.attribute_value,
        purchase_count=request.purchase_count,
        previous_purchase_count=request.previous_purchase_count,
        mention_growth=request.mention_growth,
        growth_rate=request.growth_rate,
        weekly_rank=request.weekly_rank,
        previous_rank=request.previous_rank,
        rank_change=request.rank_change,
        count_score=request.count_score,
        growth_score=request.growth_score,
        rank_score=request.rank_score,
        trend_score=request.trend_score,
    )

    return prediction

@app.get("/ml/latest-trend-predictions", response_model=schemas.LatestTrendPredictionsResponse)
def get_latest_trend_predictions(db: Session = Depends(get_db)):
    latest_trend = db.query(models.TrendSignal).order_by(
        models.TrendSignal.end_date.desc()
    ).first()

    if not latest_trend:
        return {
            "total_predictions": 0,
            "predictions": []
        }

    latest_signals = db.query(models.TrendSignal).filter(
        models.TrendSignal.time_window == latest_trend.time_window,
        models.TrendSignal.start_date == latest_trend.start_date,
        models.TrendSignal.end_date == latest_trend.end_date
    ).order_by(models.TrendSignal.trend_score.desc()).all()

    predictions = []

    for index, signal in enumerate(latest_signals, start=1):
        trend_score = float(signal.trend_score or 0)
        growth_rate = float(signal.growth_rate or 0)

        # Convert trend signal values into ML-compatible feature values.
        # These are signal-derived proxy features because our local collector
        # produces mention-based trend signals, while the ML model was trained
        # using H&M purchase-count based historical trend data.
        purchase_count = max(1, int(trend_score * 1000))
        previous_purchase_count = max(
            1,
            int(purchase_count / (1 + growth_rate))
        ) if growth_rate > -0.95 else purchase_count

        mention_growth = purchase_count - previous_purchase_count

        weekly_rank = index
        previous_rank = index + 2 if growth_rate > 0 else index
        rank_change = weekly_rank - previous_rank

        count_score = min(1.0, trend_score)
        growth_score = min(1.0, max(0.0, growth_rate))
        rank_score = 1 / weekly_rank

        prediction = trend_ml_service.predict_trend_label(
            attribute_type=signal.attribute_type,
            attribute_value=signal.attribute_value,
            purchase_count=purchase_count,
            previous_purchase_count=previous_purchase_count,
            mention_growth=mention_growth,
            growth_rate=growth_rate,
            weekly_rank=weekly_rank,
            previous_rank=previous_rank,
            rank_change=rank_change,
            count_score=count_score,
            growth_score=growth_score,
            rank_score=rank_score,
            trend_score=trend_score,
        )

        predictions.append({
            "trend_id": signal.trend_id,
            "attribute_type": signal.attribute_type,
            "attribute_value": signal.attribute_value,
            "trend_score": trend_score,
            "growth_rate": growth_rate,
            "predicted_trend_label": prediction["predicted_trend_label"],
            "confidence_scores": prediction["confidence_scores"],
            "model_type": prediction["model_type"],
        })

    return {
        "total_predictions": len(predictions),
        "predictions": predictions
    }

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

    if trend_status == "rising":
        if attribute_type == "category":
            return f"{pluralize_fashion_term(attribute_value)} are trending now"
        if attribute_type == "color":
            return f"{value} shades are gaining popularity"
        if attribute_type == "pattern":
            return f"{value} styles are trending"
        if attribute_type == "material":
            return f"{value} fabric is becoming popular"
        if attribute_type == "fit_type":
            return f"{value} fits are gaining attention"
        if attribute_type == "style":
            return f"{value} style is trending"

        return f"{value} is trending now"

    if trend_status == "stable":
        return f"{value} remains a steady fashion choice"

    return f"{value} is currently a weaker trend"

def build_trend_summary(attribute_type: str, attribute_value: str, trend_status: str) -> str:
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


def build_trend_reason(attribute_type: str, attribute_value: str, trend_status: str) -> str:
    value = attribute_value.title()

    if trend_status == "rising":
        return (
            f"The system detected increasing activity for {value} based on trend score, "
            f"growth rate, ranking movement, and ML classification."
        )

    if trend_status == "stable":
        return (
            f"The system detected that {value} has a balanced trend pattern without major growth or decline."
        )

    return (
        f"The system detected that {value} has lower trend score or negative growth compared with stronger trends."
    )


def get_display_badge(trend_status: str) -> str:
    if trend_status == "rising":
        return "🔥 Rising Trend"

    if trend_status == "stable":
        return "✨ Stable Trend"

    return "📉 Weak Trend"


@app.get("/trend-insights", response_model=schemas.TrendInsightsResponse)
def get_trend_insights(db: Session = Depends(get_db)):
    latest_trend = db.query(models.TrendSignal).order_by(
        models.TrendSignal.end_date.desc()
    ).first()

    if not latest_trend:
        return {
            "total_insights": 0,
            "insights": []
        }

    latest_signals = db.query(models.TrendSignal).filter(
        models.TrendSignal.time_window == latest_trend.time_window,
        models.TrendSignal.start_date == latest_trend.start_date,
        models.TrendSignal.end_date == latest_trend.end_date
    ).order_by(models.TrendSignal.trend_score.desc()).limit(20).all()

    insights = []

    for index, signal in enumerate(latest_signals, start=1):
        trend_score = float(signal.trend_score or 0)
        growth_rate = float(signal.growth_rate or 0)

        purchase_count = max(1, int(trend_score * 1000))

        if growth_rate > -0.95:
            previous_purchase_count = max(
                1,
                int(purchase_count / (1 + growth_rate))
            )
        else:
            previous_purchase_count = purchase_count

        mention_growth = purchase_count - previous_purchase_count

        weekly_rank = index
        previous_rank = index + 2 if growth_rate > 0 else index
        rank_change = weekly_rank - previous_rank

        count_score = min(1.0, trend_score)
        growth_score = min(1.0, max(0.0, growth_rate))
        rank_score = 1 / weekly_rank

        prediction = trend_ml_service.predict_trend_label(
            attribute_type=signal.attribute_type,
            attribute_value=signal.attribute_value,
            purchase_count=purchase_count,
            previous_purchase_count=previous_purchase_count,
            mention_growth=mention_growth,
            growth_rate=growth_rate,
            weekly_rank=weekly_rank,
            previous_rank=previous_rank,
            rank_change=rank_change,
            count_score=count_score,
            growth_score=growth_score,
            rank_score=rank_score,
            trend_score=trend_score,
        )

        trend_status = prediction["predicted_trend_label"]
        confidence_scores = prediction["confidence_scores"]
        confidence = float(confidence_scores.get(trend_status, 0))

        insights.append({
            "trend_id": signal.trend_id,
            "title": build_trend_title(
                signal.attribute_type,
                signal.attribute_value,
                trend_status,
            ),
            "summary": build_trend_summary(
                signal.attribute_type,
                signal.attribute_value,
                trend_status,
            ),
            "reason": build_trend_reason(
                signal.attribute_type,
                signal.attribute_value,
                trend_status,
            ),
            "attribute_type": signal.attribute_type,
            "attribute_value": signal.attribute_value,
            "trend_score": trend_score,
            "growth_rate": growth_rate,
            "trend_status": trend_status,
            "confidence": round(confidence, 4),
            "display_badge": get_display_badge(trend_status),
        })

    return {
        "total_insights": len(insights),
        "insights": insights
    }