def get_logger():
    import logging

    # Setup logger
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s:%(levelname)7s:%(filename)25s"
        ":%(lineno)3s %(funcName)30s(): %(message)s",
    )
    logging.getLogger().addHandler(logging.StreamHandler())
    return logging