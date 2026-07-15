from copy import deepcopy
from typing import Any, Dict, Iterable

import logging

logger = logging.getLogger(__name__)


def fix_query_list(
    request_query: Iterable,
    key_list: list[str]
) -> Dict[str, Any]:
    """
    Normalize query parameters.

    - Converts keys ending with '[]' to their base name.
    - Ensures parameters in key_list are always returned as lists.
    - Converts comma-separated values into lists.
    - Returns single values for parameters not in key_list.
    """
    try:
        query_dict = dict(request_query)
        new_query_dict = deepcopy(query_dict)

        for param_name, value in query_dict.items():

            # Skip empty values
            if not value:
                continue

            normalized_param = param_name

            # Remove [] suffix from parameter names
            if normalized_param.endswith("[]"):
                normalized_param = normalized_param[:-2]
                new_query_dict[normalized_param] = new_query_dict.pop(param_name)

            # Parameters expected to be lists
            if normalized_param in key_list:

                if isinstance(value, list):
                    if len(value) == 1 and "," in value[0]:
                        new_query_dict[normalized_param] = value[0].split(",")
                    else:
                        new_query_dict[normalized_param] = value
                else:
                    new_query_dict[normalized_param] = [value]

            # Parameters expected to be scalar values
            else:
                if isinstance(value, list):
                    new_query_dict[normalized_param] = value[0]
                else:
                    new_query_dict[normalized_param] = value

        return new_query_dict

    except Exception:
        logger.exception("Failed to normalize query parameters.")
        raise


def str2bool(value: Any) -> bool:
    """
    Convert common string representations to boolean.
    """
    return str(value).strip().lower() in {
        "yes",
        "true",
        "t",
        "1",
        "y",
        "on",
    }
