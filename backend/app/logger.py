import logging
from logging import StreamHandler

from app.core.config import settings

logging.basicConfig(
    level=logging.DEBUG if settings.dev_mode else logging.INFO,
    format=(
        "[%(asctime)s][%(levelname)s] %(module)s:%(funcName)s:%(lineno)d"
        "             %(message)s"
    ),
    handlers=[StreamHandler()],
)
app_logger = logging.getLogger(__name__)
