app.factory('ExecuteService', function ($http, mtToastService) {
    var api_execute_path = '/api/settings/execute';

    return {
        load: function () {
            return $http.get(api_execute_path);
        },
        save: function (interval) {
            return $http.put(api_execute_path, { 'interval': interval }).then(function (data) {
                mtToastService.show('Interval updated');
            });
        },
        execute: function () {
            return $http.post('/api/execute/call');
        }
    };
});
