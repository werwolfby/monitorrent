app.controller('ExecuteController', function ($scope, $http, $q, mtToastService, ExecuteService) {
    $scope.messages = [];

    var started = function (message) {
        $scope.messages = [];
    };

    var finished = function (message) {
    };

    var log = function (message) {
        $scope.messages.push(message);
    };

    $scope.execute = function () {
        $scope.messages = [];
        ExecuteService.execute();
    };

    $scope.updateInterval = function () {
        ExecuteService.save($scope.interval);
    };

    var executeStarted = started;
    var executeEvents = function (logs) {
        for (var i = 0; i < logs.length; i++) {
            log(logs[i]);
        }
        if (logs.length > 0) {
            $scope.last_execute = logs[logs.length - 1].time;
        }
        $("html, body").animate({ scrollTop: $(document).height() }, "fast");
    };
    var executeFinished = finished;

    var subscription = null;

    ExecuteService.load().then(function(data) {
        $scope.interval = data.data.interval;
        $scope.last_execute = data.data.last_execute;
        subscription = ExecuteService.subscribe({started: executeStarted, events: executeEvents, finished: executeFinished});
    });

    $scope.$on('$destroy', function() {
        if (subscription) {
            subscription();
        }
    });
});
