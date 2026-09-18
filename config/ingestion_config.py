INGESTION_CONFIG = {

    "customers": {
        "file": "olist_customers_dataset.xls",
        "primary_key": ["customer_id"]
    },

    "orders": {
        "file": "olist_orders_dataset.xls",
        "primary_key": ["order_id"]
    },

    "payments": {
        "file": "olist_order_payments_dataset.xls",
        "primary_key": ["order_id", "payment_sequential"]
    },

    "order_reviews": {
    "file": "olist_order_reviews_dataset_clean.xlsx",
    "primary_key": ["review_id", "order_id"]
},

    "products": {
        "file": "olist_products_dataset.xls",
        "primary_key": ["product_id"]
    }
}