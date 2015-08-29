/* global app */
/* global angular */
app.controller('AuthenticationController', function ($scope, $http, mtToastService, $mdDialog, disableAuthenticationControllerValue) {
	$scope.isEnabled = false;
	$scope.isEnabledView = false;
	$scope.actionText = function () {
		return $scope.isEnabled ? "Change password" : "Set password";
	};

	var resetInputValues = function () {
		$scope.password = "";
		$scope.oldPassword = "";
		$scope.passwordCheck = "";
		if ($scope.submitPassword) {
			// it might be the case where we set new password
			// and dont have oldPassword field just yet because of ng-if
			if ($scope.submitPassword.oldPassword) {
				$scope.submitPassword.oldPassword.$setUntouched();
			}
			$scope.submitPassword.password.$setUntouched();
		}
	};

	resetInputValues();

	$scope.disableAuthentication = function () {
		if ($scope.isEnabledView) {
			return;
		}

		if (!$scope.isEnabled) {
			$scope.isEnabledView = false;
			return;
		}

		$mdDialog.show({
			controller: disableAuthenticationControllerValue,
			templateUrl: 'controllers/settings/authentication/disable-authentication-dialog.html',
			parent: angular.element(document.body)
		}).then(function () {
			$scope.isEnabled = false;
			resetInputValues();
		}, function () {
			$scope.isEnabledView = true;
		});
	};

	$scope.showErrors = function () {
		if ($scope.isEnabled) {
			$scope.submitPassword.oldPassword.$setTouched();
		} else {
			$scope.submitPassword.password.$setTouched();
		}
	};

	$scope.oldPasswordValidation = {
		valid: function () {
			$scope.submitPassword.oldPassword.$setValidity('wrongPassword', true);
		},
		invalid: function () {
			$scope.submitPassword.oldPassword.$setValidity('wrongPassword', false);
		}
	};

	$scope.setPassword = function () {
		var settings;

		if ($scope.isEnabled) {
			// update password
			settings = {
				'old_password': $scope.oldPassword,
				'new_password': $scope.password
			};

			$http.put('/api/settings/password', settings)
				.success(function (data) {
					mtToastService.show('Password was changed successfully');
				}).error(function (data) {
					$scope.oldPasswordValidation.invalid();
				});
		} else {
			// set new password
			settings = {
				'password': $scope.password,
				'is_authentication_enabled': true
			};
			$http.put('/api/settings/authentication', settings)
				.success(function (data) {
					$scope.isEnabled = true;
					resetInputValues();
					$scope.$emit('authentication.changed');
					mtToastService.show('Authentication settings changed successfully');
				}).error(function (data) {
					mtToastService.show('Something went wrong');
				});
		}
	};

	$http.get('/api/settings/authentication').success(function (data) {
		$scope.isEnabled = data.is_authentication_enabled;
		$scope.isEnabledView = data.is_authentication_enabled;
	});
});
