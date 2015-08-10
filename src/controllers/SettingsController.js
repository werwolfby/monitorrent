app.controller('SettingsController', function ($scope, $http) {
    $scope.verify_new_password = function () {
    };
    $scope.change_password = {};
    $scope.authentication = {};

    $scope.updatePassword = function () {
        if ($scope.change_password.new_password != $scope.change_password.retry_password) {
            return;
        }
        var settings = {'old_password': $scope.change_password.old_password, 'new_password': $scope.change_password.new_password};
        $http.put('/api/settings/password', settings)
            .success(function (data) {
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
        });
    };
});
