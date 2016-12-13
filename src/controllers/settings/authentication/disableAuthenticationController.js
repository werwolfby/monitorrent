app.controller('disableAuthenticationController', function ($scope, $mdDialog, $http, mtToastService) {
	$scope.passwordValidation = {
		valid: function () {
			$scope.submitPassword.password.$setValidity('wrongPassword', true);
		},
		invalid: function () {
			$scope.submitPassword.password.$setValidity('wrongPassword', false);
		}
	};

	$scope.remove = function () {
		var settings = {
			'password': $scope.password,
			'is_authentication_enabled': false
		};

		$http.put('/api/settings/authentication', settings)
			.success(function (data) {
				$scope.$emit('authentication.changed', false);
				mtToastService.show('Authentication disabled successfully');
				$mdDialog.hide();
			}).error(function (data) {
				$scope.passwordValidation.invalid();
			});
	};

	$scope.close = function () {
		$mdDialog.cancel();
	};
});