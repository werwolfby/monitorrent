app.controller('MainCtrl', function ($scope, $rootScope, $http, $window, $mdSidenav, mtRoutes, GeneralService) {
    $scope.routes = mtRoutes.routes.main;

    $scope.exit = function () {
        $http.post('/api/logout').then(function () {
            $window.location.href = '/login';
        });
    };

    $http.get('/api/settings/authentication').success(function (data) {
        $scope.exit_visible = data.is_authentication_enabled;
    });

    $rootScope.$on('authentication.changed', function (e, value) {
        $scope.exit_visible = value;
    });
});