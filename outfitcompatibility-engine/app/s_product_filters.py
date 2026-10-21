from app import s_models


NON_CRAWLED_PRODUCT_SOURCES = {"test", "sample_data", "sample_crawler"}


def apply_real_product_filter(query):
    return query.filter(
        s_models.Product.source.isnot(None),
        ~s_models.Product.source.in_(NON_CRAWLED_PRODUCT_SOURCES),
        s_models.Product.availability == True,
        s_models.Product.image_url.isnot(None),
        s_models.Product.product_url.isnot(None),
        ~s_models.Product.image_url.ilike("%example.com%"),
        ~s_models.Product.product_url.ilike("%example.com%"),
    )
