app.controller('DeveloperController', function ($scope, DeveloperService) {
    DeveloperService.get().then(function(value) {
		$scope.isDeveloper = value;
	});
	
	$scope.toggleDevMode = function () {
		DeveloperService.put($scope.isDeveloper).then(
			function () {
				$scope.$emit('developer.changed', $scope.isDeveloper);
			}, function () {
				$scope.isDeveloper = !$scope.isDeveloper;
			});
	};
});
