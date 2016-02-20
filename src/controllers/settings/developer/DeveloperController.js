app.controller('DeveloperController', function ($scope, DeveloperService) {
    DeveloperService.get().then(function(value) {
		$scope.isDeveloper = value;
	});
	
	$scope.toggleDevMode = function () {
		DeveloperService.put($scope.isDeveloper).then(
			function () {},
			function () {
				$scope.isDeveloper = !$scope.isDeveloper;
			});
	};
});
