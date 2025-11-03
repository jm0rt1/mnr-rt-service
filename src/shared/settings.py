

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

    # Operations
    OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
    LOGS_DIR.mkdir(exist_ok=True, parents=True)
    GLOBAL_LOGS_DIR.mkdir(exist_ok=True, parents=True)
    UI_LOGS_DIR.mkdir(exist_ok=True, parents=True)
