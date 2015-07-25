var app = angular.module('monitorrent', ['ngMaterial', 'ngRoute', 'ngSanitize']);

var routes = [
    {href: "/torrents", include: 'views/torrents-partial.html', label: 'Torrents', controller: 'TorrentsController'},
    {href: "/trackers", include: 'views/trackers-partial.html', label: 'Trackers', controller: 'TrackersController'},
    {href: "/clients", include: 'views/clients-partial.html', label: 'Clients', controller: 'ClientsController'},
    {href: "/settings", include: 'views/settings-partial.html', label: 'Settings', controller: 'SettingsController'},
    {href: "/logs", include: 'views/settings-partial.html', label: 'Logs', controller: 'SettingsController'},
    {href: "/execute", include: 'views/execute-partial.html', label: 'Execute', controller: 'ExecuteController'},
    {href: "/about", include: 'views/settings-partial.html', label: 'About', controller: 'SettingsController'}
];

app.config(function ($routeProvider) {
    for (var i = 0; i < routes.length; i++) {
        route = routes[i];
        $routeProvider.when(route.href, {
            templateUrl: route.include,
            controller: route.controller
        });
    }
    $routeProvider.otherwise(routes[0].href);
});

app.controller('AppCtrl', function ($scope) {
    $scope.routes = routes;
});
