def get_logger():
    import logging

    # Setup logger
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)5s:%(filename)25s"
        ":%(lineno)3s %(funcName)30s(): %(message)s",
    )
    return logging