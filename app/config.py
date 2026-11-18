import os

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "querygenius.db")
APP_DATABASE_URL = os.environ.get(
    "APP_DATABASE_URL",
    f"sqlite:///{os.path.join(DATA_DIR, 'accounts.sqlite3')}",
)
APP_ENV = os.environ.get("APP_ENV", "development").lower()
SECRET_KEY = os.environ.get("SECRET_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
MAX_ROWS = int(os.environ.get("MAX_ROWS", "1000"))
QUERY_TIMEOUT_SECONDS = int(os.environ.get("QUERY_TIMEOUT_SECONDS", "20"))
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_pre_ping": True,
    "pool_recycle": 280,
    "pool_timeout": 30,
}
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = os.environ.get(
    "SESSION_COOKIE_SECURE", str(APP_ENV == "production")
).lower() in {"1", "true", "yes"}
if not 1 <= MAX_ROWS <= 10000:
    raise ValueError("MAX_ROWS must be between 1 and 10000.")
if not 1 <= QUERY_TIMEOUT_SECONDS <= 300:
    raise ValueError("QUERY_TIMEOUT_SECONDS must be between 1 and 300.")
ALLOWED_SCHEMAS = {"main"}
ALLOWED_TABLES = {"customers", "orders", "order_items", "products", "categories"}
ALLOWED_COLUMNS = {
    "customers": {"customer_id", "customer_name", "segment", "signup_date", "region"},
    "orders": {"order_id", "customer_id", "order_date", "total_amount", "status"},
    "order_items": {
        "order_item_id", "order_id", "product_id", "quantity", "unit_price", "discount"
    },
    "products": {"product_id", "product_name", "category", "unit_price"},
    "categories": {"category_id", "category_name", "region"},
}
