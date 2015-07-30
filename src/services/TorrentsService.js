app.factory('TorrentsService', function ($http) {
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
        }
    };

    return torrentsService;
});
