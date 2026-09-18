import os
import pandas as pd
from sqlalchemy import text

from src.database.connection import get_engine
from config.ingestion_config import INGESTION_CONFIG


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)

RAW_DATA_DIR = os.path.join(BASE_DIR, "data", "raw")


def get_source_row_count(file_name):
    """Return number of rows in source Excel file."""

    file_path = os.path.join(RAW_DATA_DIR, file_name)

    if file_name.endswith(".xlsx"):
        df = pd.read_excel(
            file_path,
            engine="openpyxl"
        )
    else:
        df = pd.read_excel(
            file_path,
            engine="xlrd"
        )

    return len(df)


def get_database_row_count(table_name):
    """Return number of rows in PostgreSQL table."""

    engine = get_engine()

    try:
        with engine.connect() as connection:
            result = connection.execute(
                text(f"SELECT COUNT(*) FROM {table_name}")
            )
            return result.scalar()

    finally:
        engine.dispose()


def validate_row_counts():

    all_valid = True

    print("\n" + "=" * 65)
    print("ROW COUNT VALIDATION")
    print("=" * 65)

    for table_name, config in INGESTION_CONFIG.items():

        file_name = config["file"]

        try:
            source_count = get_source_row_count(file_name)
            database_count = get_database_row_count(table_name)

            print(f"\nTable: {table_name}")
            print(f"Source rows:   {source_count}")
            print(f"Database rows: {database_count}")

            if source_count == database_count:
                print("✅ Row count matched")
            else:
                print("❌ Row count mismatch")
                all_valid = False

        except Exception as e:
            print(
                f"❌ Validation failed for "
                f"{table_name}: {e}"
            )
            all_valid = False

    print("\n" + "=" * 65)

    if all_valid:
        print("🎯 ALL ROW COUNTS VALIDATED SUCCESSFULLY")
    else:
        print("❌ ROW COUNT VALIDATION FAILED")


if __name__ == "__main__":
    validate_row_counts()