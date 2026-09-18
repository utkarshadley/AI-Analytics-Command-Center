from sqlalchemy import text

from src.database.connection import get_engine
from config.ingestion_config import INGESTION_CONFIG
from src.ingestion.logging_config import get_logger


logger = get_logger("data_quality")


def check_duplicate_primary_keys(connection, table_name, primary_keys):
    """Check duplicate primary-key combinations."""

    columns = ", ".join(primary_keys)

    query = text(f"""
        SELECT {columns}, COUNT(*) AS duplicate_count
        FROM {table_name}
        GROUP BY {columns}
        HAVING COUNT(*) > 1
        LIMIT 10;
    """)

    result = connection.execute(query).fetchall()

    if result:
        logger.error(
            f"Duplicate primary keys found in {table_name}"
        )

        for row in result:
            logger.error(f"Duplicate record: {row}")

        return False

    logger.info(
        f"No duplicate primary keys: {table_name}"
    )

    return True


def check_null_primary_keys(connection, table_name, primary_keys):
    """Check NULL values in primary-key columns."""

    all_valid = True

    for column in primary_keys:

        query = text(f"""
            SELECT COUNT(*)
            FROM {table_name}
            WHERE {column} IS NULL;
        """)

        null_count = connection.execute(query).scalar()

        if null_count > 0:

            logger.error(
                f"NULL values found: "
                f"{table_name}.{column} = {null_count}"
            )

            all_valid = False

        else:

            logger.info(
                f"No NULL values: "
                f"{table_name}.{column}"
            )

    return all_valid


def check_business_rules(connection):
    """Check important business/data rules."""

    all_valid = True

    # ---------------------------------------------------------
    # Review score must be between 1 and 5
    # ---------------------------------------------------------

    query = text("""
        SELECT COUNT(*)
        FROM order_reviews
        WHERE review_score IS NOT NULL
          AND (review_score < 1 OR review_score > 5);
    """)

    invalid_reviews = connection.execute(query).scalar()

    if invalid_reviews > 0:

        logger.error(
            f"Invalid review scores found: {invalid_reviews}"
        )

        all_valid = False

    else:

        logger.info("Review scores are valid")

    # ---------------------------------------------------------
    # Payment value should not be negative
    # ---------------------------------------------------------

    query = text("""
        SELECT COUNT(*)
        FROM payments
        WHERE payment_value < 0;
    """)

    negative_payments = connection.execute(query).scalar()

    if negative_payments > 0:

        logger.error(
            f"Negative payment values found: "
            f"{negative_payments}"
        )

        all_valid = False

    else:

        logger.info("Payment values are valid")

    return all_valid


def validate_data_quality():

    """Run all data quality checks."""

    engine = get_engine()
    all_valid = True

    logger.info("=" * 65)
    logger.info("DATA QUALITY VALIDATION STARTED")
    logger.info("=" * 65)

    try:

        with engine.connect() as connection:

            # -------------------------------------------------
            # Primary key checks
            # -------------------------------------------------

            for table_name, config in INGESTION_CONFIG.items():

                primary_keys = config["primary_key"]

                logger.info(
                    f"Checking table: {table_name}"
                )

                if not check_duplicate_primary_keys(
                    connection,
                    table_name,
                    primary_keys
                ):
                    all_valid = False

                if not check_null_primary_keys(
                    connection,
                    table_name,
                    primary_keys
                ):
                    all_valid = False

            # -------------------------------------------------
            # Business rules
            # -------------------------------------------------

            logger.info("Checking business rules")

            if not check_business_rules(connection):
                all_valid = False

    except Exception as e:

        logger.exception(
            f"Data quality validation failed: {e}"
        )

        all_valid = False

    finally:

        engine.dispose()

    logger.info("=" * 65)

    if all_valid:

        logger.info(
            "ALL DATA QUALITY CHECKS PASSED"
        )

    else:

        logger.error(
            "DATA QUALITY CHECKS FAILED"
        )

    logger.info("=" * 65)

    return all_valid


if __name__ == "__main__":
    validate_data_quality()