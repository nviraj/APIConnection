
import flask
from .. import facebook as fb
from ..settings import FB_ACCESS_TOKEN
# from ..exceptions import MissingArgumentException
from flask import jsonify

from time import sleep
from json import dumps
from kafka import KafkaProducer

blueprint = flask.Blueprint("index", __name__)

@blueprint.route("/")
def get_data():
    """
    Returns a list of records.
    """
    provider = flask.request.args.get("provider")
    start = flask.request.args.get("start")
    end = flask.request.args.get("end")
    
    if not provider or not start or not end:
        return jsonify({"error": "Missing parameters", "provider": provider, "start": start, "end": end}), 400
    
    producer = KafkaProducer(bootstrap_servers=['localhost:29092'],
                        value_serializer=lambda x: 
                        dumps(x).encode('utf-8'))
    
    for e in range(1000):
        data = {'number' : e}
        producer.send('numtest', value=data)
        sleep(5)
    
    # if provider == fb:
    #     data = _get_fb_data(start, end)
    # else:
    #     return jsonify({"error": "Not supported"}, 400)
    
    return "The job is done"

def _get_fb_data(start_date, end_date, *args, **kwargs):
    conn = fb.FBConnection(access_token=FB_ACCESS_TOKEN)        
    fields = fb.FBConnection.get_ads_insights_variable_list()

    for acc in conn.accounts:
        data = conn.get_insight_ads_data_for_account(
            acc["id"], start_date, end_date, fields
        )      
        # import pdb; pdb.set_trace()
        return data