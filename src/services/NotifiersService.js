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
        set_enabled: function (notifier, enabled) {
            return $http.put('/api/notifiers/' + notifier + '/enabled', {
                "enabled": enabled
            }).then(function () {
            });
        },
        get_notify_on: function() {
            return $http.get('/api/settings/notify-on');
        },
        set_notify_on: function(levels) {
            return $http.put('/api/settings/notify-on', levels);
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
