import asyncio

from loguru import logger

from golden_butterfly_updater.config import load_config_from_yaml


async def run() -> None:
    logger.info("Starting Golden Butterfly Updater...")

    logger.info("Loading configuration...")
    try:
        config = load_config_from_yaml()
    except ValueError as e:
        logger.exception(f"Error while loading configuration: {e}")
        return
    logger.debug(config)
    logger.info("Configuration loaded")

    logger.info("Running Golden Butterfly Updater...")

    logger.info("Running supervisor...")


def main() -> None:
    logger.add(
        "golden_butterfly_updater.log",
        rotation="1 day",
        retention="7 days",
        level="DEBUG",
    )
    asyncio.run(run())


if __name__ == "__main__":
    main()
