from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import timedelta

from app.database import engine, Base, get_db
from app import models, schemas

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

    for obs in observations:
        key = (obs.attribute_type.lower(), obs.attribute_value.lower())

        if current_start <= obs.collected_at <= current_end:
            current_counts[key] = current_counts.get(key, 0) + obs.mention_count

        elif previous_start <= obs.collected_at < previous_end:
            previous_counts[key] = previous_counts.get(key, 0) + obs.mention_count

    all_keys = set(current_counts.keys()) | set(previous_counts.keys())

    if not all_keys:
        raise HTTPException(
            status_code=404,
            detail="No observations found in current or previous analysis windows."
        )

    analyzed_results = []

    for key in all_keys:
        attribute_type, attribute_value = key

        current_count = current_counts.get(key, 0)
        previous_count = previous_counts.get(key, 0)

        if previous_count == 0:
            if current_count > 0:
                growth_rate = 1.0
            else:
                growth_rate = 0.0
        else:
            growth_rate = (current_count - previous_count) / previous_count

        count_score = min(current_count / 100, 1.0)
        growth_score = max(min(growth_rate, 1.0), 0.0)

        trend_score = round((0.6 * count_score) + (0.4 * growth_score), 2)
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
    trends = db.query(models.TrendSignal).order_by(
        models.TrendSignal.trend_score.desc()
    ).all()

    return {
        "total_trends": len(trends),
        "trends": trends
    }