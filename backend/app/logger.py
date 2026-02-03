import logging
from logging import StreamHandler


logging.basicConfig(
    level=logging.INFO,
    format=(
        "[%(asctime)s][%(levelname)s] %(module)s:%(funcName)s:%(lineno)d"
        "             %(message)s"
    ),
    handlers=[StreamHandler()],
)
app_logger = logging.getLogger(__name__)
