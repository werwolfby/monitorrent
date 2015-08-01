app.factory('TorrentsService', function ($http, $resource) {
    var torrent = $resource('/api/torrents/:tracker/:id');

    torrentsService = {
        all: function () {
            return $http.get("/api/torrents");
        },
        add: function(url, settings) {
            return $http.post("/api/torrents", {url: url, settings: settings});
        },
        delete: function (url) {
            return $http.delete("/api/torrents", {params: {url: url}});
        },
        parseUrl: function(url) {
            return $http.get("/api/parse", {params: {url: url}});
        },
        getSettings: function (tracker, id) {
            return torrent.get({tracker: tracker, id: id}).$promise;
        }
    };

    return torrentsService;
});
