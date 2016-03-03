app.controller('SettingsController', function ($scope, mtRoutes, DeveloperService) {
	$scope.routes = mtRoutes.routes.settings;
	
	$scope.checkRoute = function(route) {
		if(route.ignore) {
			return false;
		}
		
        if($scope.isDev) {
            return true;
        }
        
        if(route.dev === true) {
            return false;
        }
        
        return true;
    };
	
	DeveloperService.get().then(function(value) {
		$scope.isDev = value;
	});
});
