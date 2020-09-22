import os
import sys
import logging
import inspect
import traceback

import toscaparser.utils.urlutils
from toscaparser.tosca_template import ToscaTemplate
from toscaparser.common.exception import ValidationError

from submitter import micado_validator as Validator
from submitter.utils import resolve_get_inputs


logger = logging.getLogger("submitter." + __name__)


def set_template(path, parsed_params=None):
    """ the method that will parse the YAML and return ToscaTemplate
    object topology object.

    :params: path, parsed_params
    :type: string, dictionary
    :return: template
    :raises: Exception

    | parsed_params: dictionary containing the input to change
    | path: local or remote path to the file to parse
    """
    isfile = _isfile_check(path)

    try:
        template = ToscaTemplate(path, parsed_params, isfile)
    except ValidationError as e:
        message = [
            line
            for line in e.message.splitlines()
            if not line.startswith("\t\t")
        ]
        message = "\n".join(message)
        raise Exception(message) from None
    except AttributeError as e:
        logger.error(
            f"error happened: {e}, This might be due to the wrong type in "
            "the TOSCA template, check if all the type exist or that the "
            "import section is correct."
        )
        raise Exception(
            "An error occured while parsing, This might be due to the a "
            "wrong type in the TOSCA template, check if all the types "
            "exist, or that the import section is correct."
        ) from None

    Validator.validation(template)
    _find_other_inputs(template)
    return template


def _isfile_check(path):
    if os.path.isfile(path):
        logger.debug("check if the input file is local")
        return True

    logger.debug("checking if the input is a valid url")
    try:
        toscaparser.utils.urlutils.UrlUtils.validate_url(path)
        return False
    except Exception as e:
        logger.error("the input file doesn't exist or cannot be reached")
        raise Exception("Cannot find input file {}".format(e))


def _find_other_inputs(template):
    resolve_get_inputs(
        template.tpl, _get_input_value, lambda x: x is not None, template
    )
    # Update nodetemplate properties
    for node in template.nodetemplates:
        node._properties = node._create_properties()


def _get_input_value(key, template):
    try:
        return template.parsed_params[key]
    except (KeyError, TypeError):
        logger.debug(f"Input '{key}' not given, using default")

    try:
        return [
            param.default for param in template.inputs if param.name == key
        ][0]
    except IndexError:
        logger.error(f"Input '{key}' has no default")
