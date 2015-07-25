app.factory('ExecuteService', function ($http) {
    var api_execute_path = '/api/execute';

    executeService = {
        load: function () {
            return $http.get(api_execute_path);
        },
        save: function (interval) {
            return $http.put(api_execute_path, {'interval': interval});
        }
    };

    return executeService;
});
