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


def load_excel(file_name):
    """Read an Excel file from the raw data directory."""

    file_path = os.path.join(RAW_DATA_DIR, file_name)

    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

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

    print(f"File loaded: {file_name}")
    print(f"Rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")

    return df


def upsert_to_postgresql(df, table_name, primary_keys):
    """
    Load DataFrame into PostgreSQL using
    staging table + ON CONFLICT UPSERT.
    """

    engine = get_engine()

    try:
        with engine.begin() as connection:

            # -------------------------------------------------
            # 1. Create temporary staging table
            # -------------------------------------------------

            staging_table = f"{table_name}_staging"

            connection.execute(
                text(f"""
                    CREATE TEMP TABLE {staging_table}
                    (LIKE {table_name} INCLUDING DEFAULTS)
                    ON COMMIT DROP;
                """)
            )

            # -------------------------------------------------
            # 2. Load DataFrame into staging table
            # -------------------------------------------------

            df.to_sql(
                name=staging_table,
                con=connection,
                if_exists="append",
                index=False,
                method="multi"
            )

            # -------------------------------------------------
            # 3. Build column list
            # -------------------------------------------------

            columns = list(df.columns)

            column_list = ", ".join(
                columns
            )

            # -------------------------------------------------
            # 4. Build conflict columns
            # -------------------------------------------------

            conflict_columns = ", ".join(
                primary_keys
            )

            # -------------------------------------------------
            # 5. Build update columns
            # -------------------------------------------------

            update_columns = [
                column
                for column in columns
                if column not in primary_keys
            ]

            # -------------------------------------------------
            # 6. Build UPDATE clause
            # -------------------------------------------------

            if update_columns:

                update_clause = ", ".join(
                    f"{column} = EXCLUDED.{column}"
                    for column in update_columns
                )

                conflict_action = f"""
                    DO UPDATE SET
                        {update_clause}
                """

            else:

                conflict_action = """
                    DO NOTHING
                """

            # -------------------------------------------------
            # 7. UPSERT into main table
            # -------------------------------------------------

            upsert_query = text(f"""
                INSERT INTO {table_name} (
                    {column_list}
                )
                SELECT
                    {column_list}
                FROM {staging_table}
                ON CONFLICT ({conflict_columns})
                {conflict_action};
            """)

            connection.execute(upsert_query)

            print(
                f"UPSERT completed successfully: "
                f"{table_name} ✅"
            )

    except Exception as e:

        print(
            f"❌ UPSERT failed for "
            f"'{table_name}': {e}"
        )

        raise

    finally:
        engine.dispose()


def load_table(table_name):
    """Load one configured table into PostgreSQL."""

    if table_name not in INGESTION_CONFIG:
        raise ValueError(
            f"Table '{table_name}' not found "
            f"in INGESTION_CONFIG"
        )

    config = INGESTION_CONFIG[table_name]

    file_name = config["file"]
    primary_keys = config["primary_key"]

    print("\n" + "=" * 60)
    print(f"INGESTING TABLE: {table_name}")
    print("=" * 60)

    df = load_excel(file_name)

    upsert_to_postgresql(
        df,
        table_name,
        primary_keys
    )


if __name__ == "__main__":

    try:

        for table_name in INGESTION_CONFIG:

            load_table(table_name)

        print(
            "\n🎯 ALL TABLES INGESTED SUCCESSFULLY!"
        )

    except Exception as e:

        print(
            f"\n❌ Ingestion pipeline failed: {e}"
        )