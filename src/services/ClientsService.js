app.factory('ClientsService', function ($http, mtToastService) {
    return {
        clients: function () {
            return $http.get('/api/clients');
        },
        save: function (client, data) {
            return $http.put('/api/clients/' + client, data).then(function () {
                mtToastService.show('Credential saved');
            });
        },
        load: function (client) {
            return $http.get('/api/clients/' + client);
        },
        check: function (client) {
            return $http.get('/api/check_client', { params: { client: client } }).then(function () {
                mtToastService.show('Connection successful');
            }, function () {
                mtToastService.show('Connection failed');
            });
        }
    };
});
