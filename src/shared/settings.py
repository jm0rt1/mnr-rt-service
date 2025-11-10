

from pathlib import Path


class GlobalSettings():
    ##
    # Paths ---------
    APP_DIR = Path("./").resolve()

    # Output Directory
    OUTPUT_DIR = APP_DIR/"output"
    # Logging Related Paths
    LOGS_DIR = OUTPUT_DIR/"logs"
    GLOBAL_LOGS_DIR = LOGS_DIR/"global"
    UI_LOGS_DIR = LOGS_DIR/"ui"
    # GTFS Data Paths
    GTFS_DIR = APP_DIR/".gtfs_temp"
    GTFS_MNR_DIR = GTFS_DIR/"metro-north-railroad"
    GTFS_MNR_DATA_DIR = GTFS_MNR_DIR/"gtfsmnr"
    # Paths ---------
    ##

    class LoggingParams():
        BACKUP_COUNT = 10
        GLOBAL_FILE_NAME = "global.log"

    class FeatureFlags():
        GPT_5_CODEX_PREVIEW_ENABLED = True
        GPT_5_CODEX_PREVIEW_ROLLOUT = "all_clients"
        GPT_5_CODEX_PREVIEW_STAGE = "preview"

        @classmethod
        def as_dict(cls):
            return {
                "gpt_5_codex_preview": {
                    "enabled": cls.GPT_5_CODEX_PREVIEW_ENABLED,
                    "rollout": cls.GPT_5_CODEX_PREVIEW_ROLLOUT,
                    "stage": cls.GPT_5_CODEX_PREVIEW_STAGE
                }
            }

    class GTFSDownloadSettings():
        # URL for MTA Metro-North Railroad GTFS static schedule data
        GTFS_FEED_URL = "https://rrgtfsfeeds.s3.amazonaws.com/gtfsmnr.zip"
        # Minimum interval between downloads (in seconds) - 1 day
        MIN_DOWNLOAD_INTERVAL = 24 * 60 * 60  # 24 hours
        # Maximum interval - auto-update if data is older than this (7 days)
        MAX_DATA_AGE = 7 * 24 * 60 * 60  # 7 days

    # Operations
    OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
    LOGS_DIR.mkdir(exist_ok=True, parents=True)
    GLOBAL_LOGS_DIR.mkdir(exist_ok=True, parents=True)
    UI_LOGS_DIR.mkdir(exist_ok=True, parents=True)
