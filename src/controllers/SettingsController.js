app.controller('SettingsController', function ($scope, $http, $mdToast) {
    $scope.remove_backend_error = function (form, elem) {
        elem.$setValidity('backend', true);
    };
    $scope.change_password = {'backend_messages': {}};
    $scope.authentication = {'backend_messages': {}};

    $scope.updatePassword = function () {
        if ($scope.change_password.new_password != $scope.change_password.retry_password) {
            return;
        }
        var settings = {'old_password': $scope.change_password.old_password, 'new_password': $scope.change_password.new_password};
        $http.put('/api/settings/password', settings)
            .success(function (data) {
                $mdToast.show(
                    $mdToast.simple()
                        .content('Password was changed successfully')
                        .position('right top')
                        .hideDelay(3000)
                );
            }).error(function (data) {
                $scope.change_password.backend_messages[data.param] = data.message;
                $scope.changePassword[data.param].$setValidity('backend', false);
            });
    };

    $http.get('/api/settings/authentication').success(function (data) {
        $scope.authentication.is_authentication_enabled = data.is_authentication_enabled;
    });

    $scope.setAuthentication = function () {
        var settings = {
            'password': $scope.authentication.password,
            'is_authentication_enabled': $scope.authentication.is_authentication_enabled
        };
        $http.put('/api/settings/authentication', settings)
            .success(function (data) {
                $scope.$emit('authentication.changed');
                $mdToast.show(
                    $mdToast.simple()
                        .content('Authentication settings changed successfully')
                        .position('right top')
                        .hideDelay(3000)
                );
        }).error(function (data) {
                $scope.authentication.backend_messages[data.param] = data.message;
                $scope.enableDisableAuthentication[data.param].$setValidity('backend', false);
            });
    };
});
