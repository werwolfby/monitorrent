app.factory('ExecuteService', function ($http) {
    var api_execute_path = '/api/settings/execute';

    executeService = {
        load: function () {
            return $http.get(api_execute_path);
        },
        save: function (interval) {
            return $http.put(api_execute_path, {'interval': interval});
        },
        execute: function () {
            return $http.post('/api/execute/call');
        }
    };

    return executeService;
});
