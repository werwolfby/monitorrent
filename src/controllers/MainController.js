app.controller('MainCtrl', function ($scope, $rootScope, $http, $window, $mdSidenav, mtRoutes, DeveloperService) {
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
    
    $scope.isDev = false;
    
    DeveloperService.get().then(function(value) {
        $scope.isDev = value;
    });
    
    $scope.checkItem = function(route) {
        if($scope.isDev) {
            return true;
        }
        
        if(route.dev === true) {
            return false;
        }
        
        return true;
    };

    var updateAuthentication = function () {
        $http.get('/api/settings/authentication').success(function (data) {
            $scope.exit_visible = data.is_authentication_enabled;
        });
    };

    updateAuthentication();

    $rootScope.$on('authentication.changed', function (e, value) {
        $scope.exit_visible = value;
    });
    
    $rootScope.$on('developer.changed', function (e, value) {
        $scope.isDev = value;
    });
});