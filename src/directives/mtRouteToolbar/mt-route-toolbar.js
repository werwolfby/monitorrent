/* global app */
app.directive('mtRouteToolbar', function ($route, mtRoutes, $location) {
	return {
        restrict: 'E',
        templateUrl: 'directives/mtRouteToolbar/mt-route-toolbar.html',
		scope: {
			showBack: '='
		},
        link: function (scope, element) {
			scope.headerText = mtRoutes.getRouteByPath($route.current.originalPath).label;

			scope.back = function () {
				$location.path(mtRoutes.prevRoute.get().href);
			};
		}
	};
});
