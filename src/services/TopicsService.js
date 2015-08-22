app.factory('TopicsService', function ($http) {
    var topicsService = {
        all: function () {
            return $http.get("/api/topics");
        },
        add: function(url, settings) {
            return $http.post("/api/topics", {url: url, settings: settings});
        },
        delete: function (id) {
            return $http.delete("/api/topics/" + id);
        },
        parseUrl: function(url) {
            return $http.get("/api/topics/parse", {params: {url: url}});
        },
        getSettings: function (id) {
            return $http.get("/api/topics/" + id);
        },
        saveSettings: function (id, settings) {
            return $http.put("/api/topics/" + id, settings);
        }
    };

    return topicsService;
});
