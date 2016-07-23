app.controller('SettingsController', function ($scope, mtRoutes, GeneralService) {
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
	
	GeneralService.getIsDeveloperMode().then(function(value) {
		$scope.isDev = value;
	});
});
