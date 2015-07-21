import flask
from flask import Flask, redirect
from flask_restful import Resource, Api, abort, reqparse, request
from engine import Logger, EngineRunner
from db import init_db_engine, create_db
from plugin_managers import load_plugins, TrackersManager, ClientsManager

engine = init_db_engine("sqlite:///monitorrent.db", True)
load_plugins()
create_db(engine)

tracker_manager = TrackersManager()
clients_manager = ClientsManager()

engine_runner = EngineRunner(Logger(), tracker_manager, clients_manager)

app = Flask(__name__)
api = Api(app)

class Torrents(Resource):
    post_parser = reqparse.RequestParser()

    def __init__(self):
        super(Torrents, self).__init__()
        self.post_parser.add_argument('url', required=True)

    def get(self):
        return tracker_manager.get_watching_torrents()

    def delete(self, url):
        deleted = tracker_manager.remove_watch(url)
        if not deleted:
            abort(404, message='Torrent \'{}\' doesn\'t exist'.format(url))
        return None, 204

    def post(self):
        args = self.post_parser.parse_args()
        added = tracker_manager.add_watch()
        if not added:
            abort(400, message='Can\'t add torrent: \'{}\''.format(args.url))
        return None, 201

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

class Execute(Resource):
    def get(self):
        return {
            "interval": engine_runner.interval,
            "last_execute": engine_runner.last_execute.isoformat() if engine_runner.last_execute else None
        }

@app.route('/')
def index():
    return redirect('static/index5.html')

@app.route('/api/parse')
def parse_url():
    url = request.args['url']
    name = tracker_manager.parse_url(url)
    if name:
        return name
    abort(400, message='Can\' parse url: \'{}\''.format(url))

@app.route('/api/check_client')
def check_client():
    client = request.args['client']
    return '', 204 if clients_manager.check_connection(client) else 500


api.add_resource(Torrents, '/api/torrents')
api.add_resource(Clients, '/api/clients/<string:client>')
api.add_resource(Execute, '/api/execute')

if __name__ == '__main__':
    app.run(debug=True)
