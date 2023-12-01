"""
Replacement for RUSA ACP brevet time calculator
(see https://rusa.org/octime_acp.html)

"""

import requests

import flask
from flask import request
import arrow  # Replacement for datetime, based on moment.js
import acp_times  # Brevet time calculations
#import config

import logging

from pymongo import MongoClient
from flask import Flask, redirect, url_for, request, render_template, jsonify
import os

###
# Globals
###
app = flask.Flask(__name__)
app.debug = True if "DEBUG" not in os.environ else os.environ["DEBUG"]
port_num = True if "PORT" not in os.environ else os.environ["PORT"]
#CONFIG = config.configuration()

###
# Pages
###

# Connect MongoDB
#client = MongoClient("mongodb://" + os.environ['MONGODB_HOSTNAME'], 27017)
#db = client.mydb

API_ADDR = os.environ["API_ADDR"]
API_PORT = os.environ["API_PORT"]
API_URL = f"http://{API_ADDR}:{API_PORT}/api/"

def get_brev():
    lists = requests.get(f"{API_URL}/brevets").json()
    theBrevet = lists[-1]
    return theBrevet["title"], theBrevet["items"]

def insert_brev(title, items):
    _id = requests.post(f"{API_URL}/brevets", json={"title": title, "items": items}).json()
    return _id
    

@app.route("/")
@app.route("/index")
def index():
    app.logger.debug("Main page entry")
    return flask.render_template('calc.html')
#    return flask.render_template('calc.html', items=list(db.myposts.find()))


@app.errorhandler(404)
def page_not_found(error):
    app.logger.debug("Page not found")
    return flask.render_template('404.html'), 404


###############
#
# AJAX request handlers
#   These return JSON, rather than rendering pages.
#
###############
@app.route("/_calc_times")
def _calc_times():
    """
    Calculates open/close times from miles, using rules
    described at https://rusa.org/octime_alg.html.
    Expects one URL-encoded argument, the number of miles.
    """
    app.logger.debug("Got a JSON request")
    km = request.args.get('km', 999, type=float)
    app.logger.debug("km={}".format(km))
    app.logger.debug("request.args: {}".format(request.args))
    brevkm = request.args.get('brevkm', type=float)
    app.logger.debug("Brevets Distance: {}".format(brevkm))
    begin = request.args.get('begin', type=str)
    app.logger.debug("Start time: {}".format(begin))
    # FIXME!
    # Right now, only the current time is passed as the start time
    # and control distance is fixed to 200
    # You should get these from the webpage!
    open_time = acp_times.open_time(km, brevkm, begin).format('YYYY-MM-DDTHH:mm')
    close_time = acp_times.close_time(km, brevkm, begin).format('YYYY-MM-DDTHH:mm')
    result = {"open": open_time, "close": close_time}
    return flask.jsonify(result=result)

"""
@app.route('/submit_data/', methods=['POST', 'GET'])
def submit_data():
    if request.method == 'POST':
        item_doc = {
            'distance': request.form['distance'],
            'begin_date': request.form['begin_date'],
            'km': request.form['km'],
            'miles': request.form['miles'],
            'open': request.form['open'],
            'close': request.form['close']
        }
        db.myposts.insert_one(item_doc)
        return jsonify({"message": "Data submitted successfully"})
    elif request.method == 'GET':
        return jsonify({"message": "GET not supported"})

    return redirect(url_for('index'))
"""

@app.route("/insert", methods=['POST', 'GET'])
def insert():
    try:
        input_json = request.json

        title = input_json["title"]
        items = input_json["items"]

        brevet_id = insert_brev(title, items)

        return flask.jsonify(result={},
                             message="Inserted",
                             status=1,
                             mongo_id=brevet_id)
    except:
        return flask.jsonify(result={},
                             message="Oh no! Server error!",
                             status=0,
                             mongo_id='None')

"""
@app.route('/display/', methods=['GET'])
def display():
    data = list(db.myposts.find())
    return jsonify({"data": data})
"""

@app.route("/fetch", methods=['GET'])
def fetch():
    try:
        title, items = get_brev()
        return flask.jsonify(
            result = {"title": title, "items": items},
            status = 1,
            message="Successfully fetched the brevet")
    except:
        return flask.jsonify(
            result = {},
            status = 0,
            message="Something went wrong, couldn't fetch any lists")
        
        



#############

#app.debug = CONFIG.DEBUG
if app.debug:
    app.logger.setLevel(logging.DEBUG)

if __name__ == "__main__":
#    print("Opening for global access on port {}".format(CONFIG.PORT))
    app.run(port=port_num, host="0.0.0.0")
