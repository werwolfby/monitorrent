app.factory('ClientsService', function ($http) {
    return {
        clients: function () {
            return $http.get('/api/clients');
        },
        save: function (client, data) {
            return $http.put('/api/clients/' + client, data);
        },
        load: function (client) {
            return $http.get('/api/clients/' + client);
        },
        check: function (client) {
            return $http.get('/api/clients/' + client + '/check');
        }
    };
});
