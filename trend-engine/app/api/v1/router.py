from fastapi import APIRouter

from app.api.v1 import admin, brands, products, stats, trends

router = APIRouter(prefix="/api/v1")
router.include_router(trends.router)
router.include_router(products.router)
router.include_router(brands.router)
router.include_router(stats.router)
router.include_router(admin.router)
