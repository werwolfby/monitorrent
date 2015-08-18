app.controller('MainCtrl', function ($scope, $http, $window, $mdSidenav, mtRoutes) {
    $scope.routes = mtRoutes.routes.main;

    $scope.exit = function () {
        $http.post('/api/logout').then(function () {
            $window.location.href = '/login';
        });
    };

    $scope.toggleSidenav = function () {
        $mdSidenav('sidenav').toggle();
    };
    $scope.closeSidenav = function () {
        $mdSidenav('sidenav').close();
    };
    
    $scope.checkItem = function(route) {
        // TODO: add support on backend and update code below
        // var isDev = true; // should be service call
        // if(isDev) {
        //     return true;
        // }
        
        // if(route.dev === true) {
        //     return false;
        // }
        
        return true;
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