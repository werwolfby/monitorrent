var app = angular.module('monitorrent', ['ngMaterial', 'ngRoute']);

var routes = [
    {href: "/torrents", include: 'torrents-partial.html', label: 'Torrents', controller: 'TorrentsController'},
    {href: "/clients", include: 'settings-partial.html', label: 'Clients', controller: 'SettingsController'},
    {href: "/settings", include: 'settings-partial.html', label: 'Settings', controller: 'SettingsController'},
    {href: "/logs", include: 'settings-partial.html', label: 'Logs', controller: 'SettingsController'},
    {href: "/execute", include: 'settings-partial.html', label: 'Execute', controller: 'SettingsController'},
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

app.controller('SettingsController', function ($scope) {
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
            return $http.delete("/api/torrents/", {params: {url: url}});
        },
        parseUrl: function(url) {
            return $http.get("/api/parse", {params: {url: url}});
        }
    };

    return torrentsService;
});