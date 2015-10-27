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
            return $http.get('/api/clients/' + client + '/check').then(function (data) {
                if (data.data.status) {
                    mtToastService.show('Connection successful');
                } else {
                    mtToastService.show('Connection failed');
                }
            }, function () {
                mtToastService.show('Connection failed');
            });
        },
        set_default: function (client) {
            return $http.put('/api/clients/' + client + '/default');
        }
    };
});
