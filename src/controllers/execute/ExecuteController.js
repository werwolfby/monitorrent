app.controller('ExecuteController', function ($scope, $http, $q, mtToastService, ExecuteService) {
    $scope.messages = [];
    var canceller = $q.defer();

    var started = function (message) {
        $scope.messages = [];
    };

    var finished = function (message) {
        $scope.last_execute = message;
    };

    var log = function (message) {
        $scope.messages.push(message);
    };

    var destroyed = false;
    var execute_id = null;
    var log_id = 0;
    
    var processEvents = function (data) {
        var result = data.data;
        if (!result.is_running) {
            executeListener();
            return;
        }
        for (var i = 0; i < result.logs.length; i++) {
            var evt = result.logs[i];
            execute_id = evt.execute_id;
            log_id = evt.id;
            log(evt);
        }
        if (result.logs.length > 0) {
            finished(result.logs[result.logs.length - 1].time);
        }
        if (result.is_running){
            executeDetailsListener();
        }
    };

    var executeListener = function () {
        $http.get('api/execute/logs/current', {timeout: canceller.promise}).then(function (data) {
            if (data.data.is_running) {
                started();
            }
            processEvents(data);
        });
    };
    
    var executeDetailsListener = function () {
        $http.get('/api/execute/logs/' + execute_id + '/details?after=' + log_id, {timeout: canceller.promise}).then(processEvents);
    };

    $scope.execute = function () {
        $scope.messages = [];
        ExecuteService.execute();
    };

    $scope.updateInterval = function () {
        ExecuteService.save($scope.interval);
    };

    ExecuteService.load().then(function(data) {
        $scope.interval = data.data.interval;
        $scope.last_execute = data.data.last_execute;
        executeListener();
    });

    $scope.$on('$destroy', function() {
        canceller.resolve();
    });
});
