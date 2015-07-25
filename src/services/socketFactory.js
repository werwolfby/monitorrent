app.factory('socketFactory', function () {
    var asyncAngularify = function ($scope, socket, callback) {
        return callback ? function () {
            var args = arguments;
            $scope.$apply(function () {
                callback.apply(socket, args);
            });
        } : angular.noop;
    };

    var create = function ($scope, host, details) {
        var socket = io.connect('http://' + document.domain + ':' + location.port + '/execute');

        return {
            on: function (eventName, callback) {
                var applyCallback = asyncAngularify($scope, socket, callback);
                $scope.$on('$destroy', function() {
                    socket.removeListener(eventName, applyCallback);
                });
                socket.on(eventName, applyCallback);
            },
            emit: function (eventName, data, callback) {
                var lastIndex = arguments.length - 1;
                var applyCallback = arguments[lastIndex];
                if(typeof applyCallback == 'function') {
                    applyCallback = asyncAngularify($scope, socket, applyCallback);
                    arguments[lastIndex] = applyCallback;
                }
                socket.emit.apply(socket, arguments);
            }
        };
    };

    socketFactory = {
        create: create
    };

    return socketFactory;
});
