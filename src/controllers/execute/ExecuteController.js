app.controller('ExecuteController', function ($scope, mtToastService, ExecuteService) {
    $scope.messages = [];

    var started = function (message) {
        $scope.messages = [];
    };

    var finished = function (message) {
        $scope.last_execute = message.finish_time;
    };

    var log = function (message) {
        $scope.messages.push(message);
    };

    var destroyed = false;

    var executeListener = function () {
        oboe('/api/execute/logs')
            .node('!.*', function(evt){
                $scope.$apply(function() {
                    if (evt.event == 'started') {
                        started();
                    } else if (evt.event == 'log') {
                        log(evt.data);
                    } else if (evt.event == 'finished') {
                        finished(evt.data);
                    }
                });
                return oboe.drop;
            })
            .done(function() {
                if (!destroyed) {
                    executeListener();
                }
            });
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
        destroyed = true;
    });
});
