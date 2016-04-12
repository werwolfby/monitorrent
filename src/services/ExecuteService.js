app.factory('ExecuteService', function ($http, $q, mtToastService) {
    var executeSubscription = function (params) {
        var canceller = $q.defer();

        var execute_id = null;
        var log_id = 0;

        var processEvents = function (logs) {
            if (logs.length > 0) {
                var evt = logs[logs.length - 1];
                execute_id = evt.execute_id;
                log_id = evt.id;
            }
            if (params.events) {
                params.events(logs);
            }
        };

        var executeListener = function () {
            var url = 'api/execute/logs/current';
            $http.get(url, {timeout: canceller.promise}).then(function (data) {
                var result = data.data;
                if (result.is_running && params.started) {
                    params.started();
                }
                processEvents(result.logs);
                if (result.is_running) {
                    executeDetailsListener();
                } else {
                    executeListener();
                }
            });
        };

        var executeDetailsListener = function () {
            $http.get('/api/execute/logs/' + execute_id + '/details?after=' + log_id, {timeout: canceller.promise}).then(function (data) {
                var result = data.data;
                processEvents(result.logs);
                if (result.is_running) {
                    executeDetailsListener();
                } else {
                    if (params.finished) {
                        params.finished();
                    }
                    if (!params.one_time) {
                        executeListener();
                    }
                }
            });
        };

        if (params.execute_id && params.after) {
            execute_id = params.execute_id;
            log_id = params.after;
            executeDetailsListener();
        } else {
            executeListener();
        }

        return function () {
            canceller.resolve();
        };
    };

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
        execute: function (ids) {
            return $http.post('/api/execute/call?ids=' + ids.join(','));
        },
        executeAll: function () {
            return $http.post('/api/execute/call');
        },
        executeErrors: function () {
            return $http.post('/api/execute/call?statuses=error');
        },
        subscribe: executeSubscription,
        logs: function (skip, take) {
            var url = '/api/execute/logs?skip=' + skip + "&take=" + take;
            return $http.get(url);
        }
    };
});
