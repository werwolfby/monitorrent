app.factory('NotifiersService', function ($http, mtToastService) {
    return {
        notifiers: function () {
            return $http.get('/api/notifiers');
        },
        save: function (notifier, data) {
            return $http.put('/api/notifiers/' + notifier, data).then(function () {
                mtToastService.show('Settings saved');
            });
        },
        set_enabled: function (notifier, is_enabled) {
            return $http.put('/api/notifiers/' + notifier + '/enabled', {
                "is_enabled": is_enabled
            }).then(function () {
            });
        },
        load: function (notifier) {
            return $http.get('/api/notifiers/' + notifier);
        },
        check: function (notifier) {
            return $http.get('/api/notifiers/' + notifier + '/check').then(function (data) {
                if (data.data.status) {
                    mtToastService.show('Connection successful');
                } else {
                    mtToastService.show('Connection failed');
                }
            }, function () {
                mtToastService.show('Connection failed');
            });
        }
    };
});
