/* global app */
app.directive('mtRouteToolbar', function ($route, mtRoutes, $location, $window) {
	return {
        restrict: 'E',
        templateUrl: 'directives/mtRouteToolbar/mt-route-toolbar.html',
		scope: {
			showBack: '='
		},
        link: function (scope, element, attributes) {
			scope.headerText = attributes.text || mtRoutes.getRouteByPath($route.current.originalPath).label;

			scope.back = function () {
				// $location.path(mtRoutes.prevRoute.get().href);
				$window.history.back();
			};
		}
	};
});
