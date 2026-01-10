import logging
from os.path import isfile

import dotenv

logger = logging.getLogger()
try:
    from shared.shared import logger

    logger = logger('main')

    import os
    import threading
    import subprocess
    import time
    import psutil
    from shared.config import Config
    from shared.cache import ResultCache
    import collector
    import publisher
    from pathlib import Path

    if __name__ == "__main__":
        app_path = Path(__file__).resolve().parent.parent.parent

        dotenv_path = os.path.join(app_path, ".env")
        if isfile(dotenv_path):
            logger.info('loading .env file')
            dotenv.load_dotenv(dotenv_path=dotenv_path)
        else:
            logger.info('no .env found')

        result_cache = ResultCache()
        config = Config(os.path.join(app_path, "config.yml"))

        collector_thread = threading.Thread(target=collector.invoke, args=(config, result_cache), name='data-collector')
        collector_thread.start()

        try:
            publisher.invoke(config, result_cache)
        except KeyboardInterrupt:
            psutil.Process(os.getpid()).terminate()
        except BaseException as exception:
            logger.exception(exception)
            psutil.Process(os.getpid()).terminate()

except BaseException as exception:
    logger.exception(exception)
    psutil.Process(os.getpid()).terminate()
