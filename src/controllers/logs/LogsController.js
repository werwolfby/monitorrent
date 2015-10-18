app.controller('LogsController', function ($scope, $http, $filter) {
  /*$scope.executes = [
    {'message': 'Execute from <i><b>8:50:21</b></i> till <i><b>8:56:37</i></b> (6 minutes 16 seconds)', 'downloaded': 3, 'failed': 0, status: 'finished'},
    {'message': 'Execute from <i><b>8:50:21</b></i> till <i><b>8:56:37</i></b> (6 minutes 16 seconds)', 'downloaded': 0, 'failed': 0, status: 'finished'},
    {'message': 'Execute from <i><b>8:50:21</b></i> till <i><b>8:56:37</i></b> (6 minutes 16 seconds)', 'downloaded': 0, 'failed': 0, status: 'finished'},
    {'message': 'Execute from <i><b>8:50:21</b></i> till <i><b>8:56:37</i></b> (6 minutes 16 seconds)', 'downloaded': 0, 'failed': 1, status: 'finished'},
    {'message': 'Execute from <i><b>8:50:21</b></i> till <i><b>8:56:37</i></b> (6 minutes 16 seconds)', 'downloaded': 0, 'failed': 1, status: 'finished'},
    {'message': 'Execute from <i><b>8:50:21</b></i> till <i><b>8:56:37</i></b> (6 minutes 16 seconds)', 'downloaded': 0, 'failed': 0, status: 'finished'},
    {'message': 'Execute from <i><b>8:50:21</b></i> till <i><b>8:56:37</i></b> (6 minutes 16 seconds)', 'downloaded': 0, 'failed': 0, status: 'failed'},
  ];*/

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
