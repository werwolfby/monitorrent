app.controller('LogsController', function ($scope, $http, $filter) {
  $scope.executes = [];

  $scope.getExecuteTitle = function (execute) {
    var startTime = new Date(execute.start_time);
    var finishTime = new Date(execute.finish_time);
    var from = $filter('date')(startTime, 'HH:mm:ss');
    var till = $filter('date')(finishTime, 'HH:mm:ss');
    return "Execute from <i><b>" + from + "</b></i> till <i><b>" + till + "</b></i>";
  };

  $http.get('/api/execute/logs?take=10').then(function (result) {
    $scope.executes = result.data.data;
  });
});
