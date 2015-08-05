# coding=utf-8
from gevent import monkey
monkey.patch_all()

import flask
import datetime
from flask import Flask, redirect
from flask.json import JSONEncoder
from flask_restful import Resource, Api, abort, reqparse, request
from engine import Logger, EngineRunner
from db import init_db_engine, create_db, upgrade
from plugin_managers import load_plugins, get_all_plugins, upgrades, TrackersManager, ClientsManager
from flask_socketio import SocketIO, emit

init_db_engine("sqlite:///monitorrent.db", True)
load_plugins()
upgrade(get_all_plugins(), upgrades)
create_db()

tracker_manager = TrackersManager()
clients_manager = ClientsManager()


class MonitorrentJSONEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime.datetime):
            return o.isoformat()
        return super(MonitorrentJSONEncoder, self).default(o)

static_folder = "webapp"
app = Flask(__name__, static_folder=static_folder, static_url_path='')
app.json_encoder = MonitorrentJSONEncoder

app.config['SECRET_KEY'] = 'secret!'
app.config['JSON_AS_ASCII'] = False
app.config['RESTFUL_JSON'] = {'ensure_ascii': False, 'cls': app.json_encoder}
socketio = SocketIO(app)


class EngineWebSocketLogger(Logger):
    def started(self):
        socketio.emit('started', namespace='/execute')

    def finished(self, finish_time, exception):
        args = {
            'finish_time': finish_time.isoformat(),
            'exception': exception.message if exception else None
        }
        socketio.emit('finished', args, namespace='/execute')

    def info(self, message):
        self.emit('info', message)

    def failed(self, message):
        self.emit('failed', message)

    def downloaded(self, message, torrent):
        self.emit('downloaded', message, size=len(torrent))

    def emit(self, level, message, **kwargs):
        data = {'level': level, 'message': message}
        data.update(kwargs)
        socketio.emit('log', data, namespace='/execute')


engine_runner = EngineRunner(EngineWebSocketLogger(), tracker_manager, clients_manager)

class Topics(Resource):
    url_parser = reqparse.RequestParser()

    def __init__(self):
        super(Topics, self).__init__()
        self.url_parser.add_argument('url', required=True)

    def get(self):
        return tracker_manager.get_watching_torrents()

    def post(self):
        json = request.get_json()
        url = json.get('url', None)
        settings = json.get('settings', None)
        added = tracker_manager.add_topic(url, settings)
        if not added:
            abort(400, message='Can\'t add torrent: \'{}\''.format(args.url))
        return None, 201


class Topic(Resource):
    def get(self, id):
        watch = tracker_manager.get_topic(id)
        return watch

    def put(self, id):
        settings = request.get_json()
        updated = tracker_manager.update_watch(id, settings)
        if not updated:
            abort(404, message='Can\'t update torrent {}'.format(id))
        return None, 204

    def delete(self, id):
        deleted = tracker_manager.remove_topic(id)
        if not deleted:
            abort(404, message='Torrent {} doesn\'t exist'.format(id))
        return None, 204

class Clients(Resource):
    def get(self, client):
        result = clients_manager.get_settings(client)
        if not result:
            abort(404, message='Client \'{}\' doesn\'t exist'.format(client))
        return result

    def put(self, client):
        settings = request.get_json()
        clients_manager.set_settings(client, settings)
        return None, 204


class ClientList(Resource):
    def get(self):
        return [{'name': n, 'form': c.form} for n, c in clients_manager.clients.iteritems()]


class Trackers(Resource):
    def get(self, tracker):
        result = tracker_manager.get_settings(tracker)
        if not result:
            abort(404, message='Client \'{}\' doesn\'t exist'.format(tracker))
        return result

    def put(self, tracker):
        settings = request.get_json()
        tracker_manager.set_settings(tracker, settings)
        return None, 204


class TrackerList(Resource):
    def get(self):
        return [{'name': name, 'form': tracker.credentials_form} for name, tracker in tracker_manager.trackers.items()
                if hasattr(tracker, 'get_credentials') and hasattr(tracker, 'get_credentials')]


class Execute(Resource):
    def get(self):
        return {
            "interval": engine_runner.interval,
            "last_execute": engine_runner.last_execute
        }

@socketio.on('execute', namespace='/execute')
def execute():
    engine_runner.execute()

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/api/parse')
def parse_url():
    url = request.args['url']
    # parse_url is separate and internal method,
    # but for this request we need initial settings before add_topic
    title = tracker_manager.prepare_add_topic(url)
    if title:
        return flask.jsonify(**title)
    abort(400, message='Can\' parse url: \'{}\''.format(url))

@app.route('/api/check_client')
def check_client():
    client = request.args['client']
    return '', 204 if clients_manager.check_connection(client) else 500

@app.route('/api/check_tracker')
def check_tracker():
    client = request.args['tracker']
    return '', 204 if tracker_manager.check_connection(client) else 500


@socketio.on_error
def error_handler(e):
    print e


@socketio.on_error_default
def default_error_handler(e):
    print e

api = Api(app)
api.add_resource(Topic, '/api/topics/<int:id>')
api.add_resource(Topics, '/api/topics')
api.add_resource(ClientList, '/api/clients')
api.add_resource(Clients, '/api/clients/<string:client>')
api.add_resource(TrackerList, '/api/trackers')
api.add_resource(Trackers, '/api/trackers/<string:tracker>')
api.add_resource(Execute, '/api/execute')

if __name__ == '__main__':
    #app.run(debug=True)
    socketio.run(app)
