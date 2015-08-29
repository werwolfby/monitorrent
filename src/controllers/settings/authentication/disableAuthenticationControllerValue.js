app.value('disableAuthenticationControllerValue', function ($scope, $mdDialog, $http, mtToastService) {
	$scope.passwordValidation = {
		valid: function () {
			$scope.submitPassword.password.$setValidity('wrongPassword', true);
		},
		invalid: function () {
			$scope.submitPassword.password.$setValidity('wrongPassword', false);
		}
	};

	$scope.showErrors = function () {
		$scope.submitPassword.password.$setTouched();
	};

	$scope.remove = function () {
		var settings = {
			'password': $scope.password,
			'is_authentication_enabled': false
		};

		$http.put('/api/settings/authentication', settings)
			.success(function (data) {
				$scope.$emit('authentication.changed');
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