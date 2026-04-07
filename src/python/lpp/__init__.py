from .predictor import lpp_refined_predictor, lpp_seed
from .version import VERSION


__version__ = VERSION


def get_version() -> str:
    return VERSION


__all__ = ["get_version", "lpp_refined_predictor", "lpp_seed"]
