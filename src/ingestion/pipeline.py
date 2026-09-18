from src.ingestion.load_data import load_table
from src.ingestion.validate_schema import validate_schema
from src.ingestion.validate_row_counts import validate_row_counts
from src.ingestion.validate_data_quality import validate_data_quality

from config.ingestion_config import INGESTION_CONFIG
from src.ingestion.logging_config import get_logger


logger = get_logger("pipeline")


def run_pipeline():

    logger.info("=" * 70)
    logger.info("AI ANALYTICS COMMAND CENTER - INGESTION PIPELINE")
    logger.info("=" * 70)

    try:

        # --------------------------------------------------
        # STEP 1: INGESTION
        # --------------------------------------------------

        logger.info("STEP 1: STARTING DATA INGESTION")

        for table_name in INGESTION_CONFIG:

            load_table(table_name)

        logger.info("STEP 1 COMPLETED: DATA INGESTION SUCCESSFUL")

        # --------------------------------------------------
        # STEP 2: SCHEMA VALIDATION
        # --------------------------------------------------

        logger.info("STEP 2: STARTING SCHEMA VALIDATION")

        schema_valid = True

        for table_name, config in INGESTION_CONFIG.items():

            result = validate_schema(
                table_name,
                config["file"]
            )

            if not result:
                schema_valid = False

        if not schema_valid:
            raise Exception("Schema validation failed")

        logger.info("STEP 2 COMPLETED: SCHEMA VALIDATION SUCCESSFUL")

        # --------------------------------------------------
        # STEP 3: ROW COUNT VALIDATION
        # --------------------------------------------------

        logger.info("STEP 3: STARTING ROW COUNT VALIDATION")

        validate_row_counts()

        logger.info("STEP 3 COMPLETED: ROW COUNT VALIDATION FINISHED")

        # --------------------------------------------------
        # STEP 4: DATA QUALITY
        # --------------------------------------------------

        logger.info("STEP 4: STARTING DATA QUALITY VALIDATION")

        quality_valid = validate_data_quality()

        if not quality_valid:
            raise Exception("Data quality validation failed")

        logger.info(
            "STEP 4 COMPLETED: DATA QUALITY VALIDATION SUCCESSFUL"
        )

        # --------------------------------------------------
        # FINAL STATUS
        # --------------------------------------------------

        logger.info("=" * 70)
        logger.info("🎯 INGESTION PIPELINE COMPLETED SUCCESSFULLY")
        logger.info("=" * 70)

        return True

    except Exception as e:

        logger.exception(
            f"❌ INGESTION PIPELINE FAILED: {e}"
        )

        return False


if __name__ == "__main__":

    success = run_pipeline()

    if not success:
        raise SystemExit(1)