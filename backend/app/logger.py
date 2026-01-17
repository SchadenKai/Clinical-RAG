import logging
from logging import StreamHandler

from app.core.config import settings

logging.basicConfig(
    level=logging.DEBUG if settings.dev_mode else logging.INFO,
    format=(
        "[%(asctime)s][%(levelname)s] %(message)s "
        "(MOD:%(module)s:FUNC:%(funcName)s:LINENO.%(lineno)d)"
    ),
    handlers=[StreamHandler()],
)
app_logger = logging.getLogger(__name__)
