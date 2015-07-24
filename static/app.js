var app = angular.module('monitorrent', ['ngMaterial', 'ngRoute', 'ngSanitize']);

var routes = [
    {href: "/torrents", include: 'torrents-partial.html', label: 'Torrents', controller: 'TorrentsController'},
    {href: "/clients", include: 'clients-partial.html', label: 'Clients', controller: 'ClientsController'},
    {href: "/settings", include: 'settings-partial.html', label: 'Settings', controller: 'SettingsController'},
    {href: "/logs", include: 'settings-partial.html', label: 'Logs', controller: 'SettingsController'},
    {href: "/execute", include: 'execute-partial.html', label: 'Execute', controller: 'ExecuteController'},
    {href: "/about", include: 'settings-partial.html', label: 'About', controller: 'SettingsController'}
];

app.config(function ($routeProvider) {
    for (var i = 0; i < routes.length; i++) {
        route = routes[i];
        $routeProvider.when(route.href, {
            templateUrl: route.include,
            controller: route.controller
        });
    }
    $routeProvider.otherwise(routes[0].href)
});

app.controller('AppCtrl', function ($scope) {
    $scope.routes = routes;
});

app.controller('TorrentsController', function ($scope, TorrentsService, $mdDialog, $log) {
    function updateTorrents() {
        TorrentsService.all().success(function (data) {
            $scope.torrents = data
        });
    }

    function AddTorrentDialogController($scope, $mdDialog) {
        $scope.cancel = function() {
            $mdDialog.cancel();
        };
        $scope.add = function() {
            TorrentsService.add($scope.url).then(function() {
                $mdDialog.hide();
            });
        };
        $scope.parseUrl = function () {
            $scope.isloading = true;
            $scope.isloaded = false;
            $scope.disabled = true;
            TorrentsService.parseUrl($scope.url).success(function (data) {
                $scope.title = data;
                $scope.isloading = false;
                $scope.isloaded = true;
                $scope.disabled = false;
            }).error(function () {
                $scope.title = "Error";
                $scope.isloading = false;
                $scope.isloaded = true;
                $scope.disabled = true;
            });
        };
        $scope.url = "";
        $scope.disabled = true;
        $scope.isloading = false;
        $scope.isloaded = false;
    }

    $scope.deleteTorrent = function (url) {
        TorrentsService.delete(url).success(function (data) {
            updateTorrents();
        });
    };

    $scope.showAddTorrentDialog = function (ev) {
        $mdDialog.show({
            controller: AddTorrentDialogController,
            templateUrl: 'add-torrent-dialog.html',
            parent: angular.element(document.body),
            targetEvent: ev
        }).then(function() {
            updateTorrents();
        }, function() {
            updateTorrents();
        })
    };

    updateTorrents();
});

app.controller('ClientsController', function ($scope, ClientsService, $mdToast) {
    $scope.credentials = {host: 'localhost', port: 9091};

    $scope.save = function (client) {
        ClientsService.save(client, $scope.credentials).then(function () {
            $mdToast.show(
                $mdToast.simple()
                    .content('Credential saved')
                    .position('right top')
                    .hideDelay(3000)
            )
        });
    };

    $scope.check = function (client) {
        ClientsService.check(client).then(function () {
            $mdToast.show(
                $mdToast.simple()
                    .content('Connection successful')
                    .position('right top')
                    .hideDelay(3000)
            )
        }, function () {
            $mdToast.show(
                $mdToast.simple()
                    .content('Connection failed')
                    .position('right top')
                    .hideDelay(3000)
            )
        });
    };

    ClientsService.load('transmission').then(function (data) {
        $scope.credentials = angular.extend({}, data.data, {'password': '******'});
    })
});

app.controller('SettingsController', function ($scope) {
});

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
                .hideDelay(3000)
        });
    };

    ExecuteService.load().then(function(data) {
        $scope.interval = data.data.interval;
        $scope.last_execute = data.data.last_execute;
    });
});

app.factory('TorrentsService', function ($http) {
    torrentsService = {
        all: function () {
            return $http.get("/api/torrents");
        },
        add: function(url) {
            return $http.post("/api/torrents", {url: url});
        },
        delete: function (url) {
            return $http.delete("/api/torrents", {params: {url: url}});
        },
        parseUrl: function(url) {
            return $http.get("/api/parse", {params: {url: url}});
        }
    };

    return torrentsService;
});

app.factory('ClientsService', function ($http) {
    clientsService = {
        save: function (client, data) {
            return $http.put('/api/clients/' + client, data);
        },
        load: function (client) {
            return $http.get('/api/clients/' + client);
        },
        check: function (client) {
            return $http.get('/api/check_client', {params: {client: client}});
        }
    };

    return clientsService;
});

app.factory('ExecuteService', function ($http) {
    const api_execute_path = '/api/execute';

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