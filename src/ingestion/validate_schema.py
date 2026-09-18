import os
import pandas as pd
from sqlalchemy import inspect

from src.database.connection import get_engine
from config.ingestion_config import INGESTION_CONFIG


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)

RAW_DATA_DIR = os.path.join(BASE_DIR, "data", "raw")


def validate_schema(table_name, file_name):
    """Compare source file columns with PostgreSQL table columns."""

    engine = get_engine()

    try:
        # --------------------------------
        # 1. Read source file columns
        # --------------------------------
        file_path = os.path.join(RAW_DATA_DIR, file_name)

        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return False

        if file_name.endswith(".xlsx"):
            df = pd.read_excel(
                file_path,
                engine="openpyxl",
                nrows=0
            )
        else:
            df = pd.read_excel(
                file_path,
                engine="xlrd",
                nrows=0
            )

        source_columns = list(df.columns)

        # --------------------------------
        # 2. Read PostgreSQL columns
        # --------------------------------
        inspector = inspect(engine)

        db_columns = [
            column["name"]
            for column in inspector.get_columns(table_name)
        ]

        print(f"\nTable: {table_name}")
        print(f"Source columns: {source_columns}")
        print(f"DB columns:     {db_columns}")

        # --------------------------------
        # 3. Find missing columns
        # --------------------------------
        missing_in_db = [
            col
            for col in source_columns
            if col not in db_columns
        ]

        missing_in_source = [
            col
            for col in db_columns
            if col not in source_columns
        ]

        # --------------------------------
        # 4. Validation result
        # --------------------------------
        if missing_in_db:
            print(
                f"❌ Columns missing in PostgreSQL: "
                f"{missing_in_db}"
            )

        if missing_in_source:
            print(
                f"❌ Columns missing in source file: "
                f"{missing_in_source}"
            )

        if not missing_in_db and not missing_in_source:
            print("✅ Schema matched successfully!")
            return True

        return False

    except Exception as e:
        print(
            f"❌ Schema validation failed for "
            f"'{table_name}': {e}"
        )
        return False

    finally:
        engine.dispose()


if __name__ == "__main__":

    all_valid = True

    for table_name, config in INGESTION_CONFIG.items():

        result = validate_schema(
            table_name,
            config["file"]
        )

        if not result:
            all_valid = False

    print("\n" + "=" * 50)

    if all_valid:
        print("🎯 ALL SCHEMAS VALIDATED SUCCESSFULLY")
    else:
        print("❌ SCHEMA VALIDATION FAILED")