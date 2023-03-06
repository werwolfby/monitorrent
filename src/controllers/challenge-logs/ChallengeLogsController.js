app.controller('ChallengeLogsController', function ($scope, $http, $filter, ExecuteService, mtToastService) {
    $scope.logs = [];

    $http.get('/api/challenge-logs').then(function (data) {
        $scope.logs = data.data;
    });
});
