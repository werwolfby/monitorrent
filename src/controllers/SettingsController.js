app.controller('SettingsController', function ($scope, $http) {
    $scope.verify_new_password = function () {
    };

    $scope.updatePassword = function () {
        if ($scope.new_password != $scope.retry_password) {
            return;
        }
        var settings = {'old_password': $scope.old_password, 'new_password': $scope.new_password};
        $http.put('/api/settings/password', settings)
            .success(function (data) {
            });
    };
});
