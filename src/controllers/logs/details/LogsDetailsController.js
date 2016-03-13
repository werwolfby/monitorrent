app.controller('LogsDetailsController', function ($scope, $http, $filter, $routeParams, ExecuteService) {
    $scope.messages = [];

    function events(messages) {
        for (var i = 0; i < messages.length; i++) {
            $scope.messages.push(messages[i]);
        }
    }

    var unsubscribe = null;

    function finished(params) {
        unsubscribe = null;
    }

    $http.get('/api/execute/logs/' + $routeParams.executeId + '/details').then(function (result) {
        $scope.messages = result.data.logs;
        if (result.data.is_running) {
            after = 0;
            // There is small chanse to recive empty log messages in running execute, but we should care about this anyway
            if (result.data.logs.length > 0) {
                after = result.data.logs[result.data.logs.length - 1].id;
            }
            unsubscribe = ExecuteService.subscribe({execute_id: $routeParams.executeId, after: after, one_time: true, events: events, finished: finished});
        }
    });

    $scope.$on('$destroy', function() {
        if (unsubscribe) {
            unsubscribe();
        }
    });
});
