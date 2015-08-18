app.directive('mtSettings', function (mtRoutes) {
	return {
        restrict: 'E',
        templateUrl: 'directives/mtSettings/mt-settings.html',
        link: function (scope, element) {
			scope.routes = mtRoutes.routes.settings;
		}
	};
});