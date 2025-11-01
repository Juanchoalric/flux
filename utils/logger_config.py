import logging
import sys

def setup_logger():
    """
    Configura el logger raíz para la aplicación.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout, 
    )
    logging.info("Logger configurado exitosamente.")