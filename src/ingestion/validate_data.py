from sqlalchemy import text

from src.database.connection import get_engine


def validate_table(table_name):
    """Run basic data quality checks on a PostgreSQL table."""

    engine = get_engine()

    try:
        with engine.connect() as connection:

            # 1. Check table exists
            table_check = connection.execute(
                text("""
                    SELECT EXISTS (
                        SELECT 1
                        FROM information_schema.tables
                        WHERE table_name = :table_name
                    );
                """),
                {"table_name": table_name}
            ).scalar()

            if not table_check:
                print(f"❌ Table '{table_name}' does not exist.")
                return

            print(f"\n✅ Table '{table_name}' exists.")

            # 2. Row count
            row_count = connection.execute(
                text(f"SELECT COUNT(*) FROM {table_name};")
            ).scalar()

            print(f"Rows: {row_count}")

            # 3. NULL check
            null_check = connection.execute(
                text(f"""
                    SELECT
                        COUNT(*) FILTER (WHERE customer_id IS NULL)
                    FROM {table_name};
                """)
            ).scalar()

            print(f"customer_id NULLs: {null_check}")

            # 4. Duplicate customer_id
            duplicate_count = connection.execute(
                text(f"""
                    SELECT COUNT(*)
                    FROM (
                        SELECT customer_id
                        FROM {table_name}
                        GROUP BY customer_id
                        HAVING COUNT(*) > 1
                    ) duplicates;
                """)
            ).scalar()

            print(f"Duplicate customer_id values: {duplicate_count}")

            print("\nValidation completed ✅")

    except Exception as e:
        print(f"❌ Validation failed: {e}")

    finally:
        engine.dispose()


if __name__ == "__main__":
    validate_table("customers")