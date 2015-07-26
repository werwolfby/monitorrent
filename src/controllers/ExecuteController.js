app.controller('ExecuteController', function ($scope, $mdToast, ExecuteService, socketFactory) {
    var socket = socketFactory.create($scope, '/execute');

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

    $scope.execute = function () {
        $scope.messages = [];
        socket.emit('execute');
    };

    socket.on('started', started);
    socket.on('finished', finished);
    socket.on('log', log);

    $scope.updateInterval = function () {
        ExecuteService.save($scope.interval).then(function (data) {
            $mdToast.simple()
                .content('Interval updated')
                .position('right top')
                .hideDelay(3000);
        });
    };

    ExecuteService.load().then(function(data) {
        $scope.interval = data.data.interval;
        $scope.last_execute = data.data.last_execute;
    });
});
