from .. import facebook

import flask
blueprint = flask.Blueprint("facebook", __name__)

@blueprint.route("/fb/")
def get_index(form=None):
    """
    Returns a list of records.
    """
    return "fb hello"