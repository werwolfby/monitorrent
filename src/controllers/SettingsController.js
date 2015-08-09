app.controller('SettingsController', function ($scope, $http) {
    $scope.verify_new_password = function () {
    };

    $scope.changePassword = function () {
        if ($scope.new_password != $scope.retry_password) {
            return;
        }
        var settings = {'old_password': $scope.old_password, 'new_password': $scope.new_password};
        $http.post('/api/settings/change_password', settings)
            .success(function (data) {
            });
    };
});
