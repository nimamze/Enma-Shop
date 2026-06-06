import logging
from Core.utils.elasticsearch.client import es

logger = logging.getLogger(__name__)
PRODUCTS_INDEX = "products"


def create_products_index():
    if es.indices.exists(index=PRODUCTS_INDEX):
        logger.info("Elasticsearch index '%s' already exists.", PRODUCTS_INDEX)
        return False
    es.indices.create(
        index=PRODUCTS_INDEX,
        mappings={
            "properties": {
                "id": {"type": "integer"},
                "name": {
                    "type": "text",
                    "fields": {"keyword": {"type": "keyword"}},
                },
                "description": {"type": "text"},
                "price": {"type": "long"},
                "stock": {"type": "integer"},
                "is_active": {"type": "boolean"},
                "shop_id": {"type": "integer"},
                "shop_name": {
                    "type": "text",
                    "fields": {"keyword": {"type": "keyword"}},
                },
                "category_id": {"type": "integer"},
                "category_name": {
                    "type": "text",
                    "fields": {"keyword": {"type": "keyword"}},
                },
                "thumbnail": {"type": "keyword"},
                "created_at": {"type": "date"},
                "updated_at": {"type": "date"},
            }
        },
    )
    logger.info("Elasticsearch index '%s' created successfully.", PRODUCTS_INDEX)
    return True


def create_all_indexes():
    create_products_index()
