var app = angular.module('monitorrent', ['ngMaterial', 'ngRoute', 'ngSanitize', 'ngMessages']);

var routes = [
    {href: "/torrents", include: 'views/torrents-partial.html', label: 'Torrents', controller: 'TorrentsController', icon: 'get-app'},
    {href: "/trackers", include: 'views/trackers-partial.html', label: 'Trackers', controller: 'TrackersController', icon: 'settings-input-component'},
    {href: "/clients", include: 'views/clients-partial.html', label: 'Clients', controller: 'ClientsController', icon: 'dns'},
    {href: "/settings", include: 'views/settings-partial.html', label: 'Settings', controller: 'SettingsController', icon: 'settings'},
    {href: "/logs", include: 'views/settings-partial.html', label: 'Logs', controller: 'SettingsController', icon: 'align-left'},
    {href: "/execute", include: 'views/execute-partial.html', label: 'Execute', controller: 'ExecuteController', icon: 'input'},
    {href: "/about", include: 'views/about-partial.html', label: 'About', controller: 'AboutController', icon: 'group'}
];

app.config(function ($routeProvider, $mdThemingProvider) {
    routes.forEach(function(route) {
        $routeProvider.when(route.href, {
            templateUrl: route.include,
            controller: route.controller
        });
    });
    
    $routeProvider.otherwise(routes[0].href);

    $mdThemingProvider.theme('default')
        .primaryPalette('blue-grey')
        .accentPalette('deep-purple');
});

app.controller('AppCtrl', function ($scope, $http, $window, $mdSidenav) {
    $scope.routes = routes;

    $scope.exit = function () {
        $http.post('/api/logout').then(function () {
            $window.location.href = '/login';
        });
    };

    $scope.toggleSidenav = function() {
        $mdSidenav('sidenav').toggle();
    };
    $scope.closeSidenav = function() {
        $mdSidenav('sidenav').close();
    };

    var updateAuthentication = function () {
        $http.get('/api/settings/authentication').success(function (data) {
            $scope.exit_visible = data.is_authentication_enabled;
        });
    };

    $scope.$on('authentication.changed', function () {
        updateAuthentication();
    });

    updateAuthentication();
});
