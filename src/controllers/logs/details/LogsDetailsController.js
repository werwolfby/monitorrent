app.controller('LogsDetailsController', function ($scope, $http, $filter, $routeParams) {
  $scope.messages = [];

  $http.get('/api/execute/logs/' + $routeParams.executeId + '/details').then(function (result) {
    $scope.messages = result.data;
  });
});
