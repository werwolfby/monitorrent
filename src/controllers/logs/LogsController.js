app.controller('LogsController', function ($scope, $http, $filter) {
  $scope.executes = [];

  $scope.getExecuteTitle = function (execute) {
    var startTime = new Date(execute.start_time);
    var finishTime = new Date(execute.finish_time);
    var from = $filter('date')(startTime, 'yyyy/MM/dd HH:mm:ss');
    var till = $filter('date')(finishTime, 'yyyy/MM/dd HH:mm:ss');
    return "Execute from <i><b>" + from + "</b></i> till <i><b>" + till + "</b></i>";
  };

  var PAGE_SIZE = 10;
  var last_page = 0;
  var length = 0;

  function loadNextPage() {
    if (length > 0 && last_page * PAGE_SIZE >= length)
      return;
    $http.get('/api/execute/logs?take=' + PAGE_SIZE + "&skip=" + (last_page * PAGE_SIZE)).then(function (result) {
      for (var i = 0; i < result.data.data.length; i++) {
        $scope.executes.push(result.data.data[i]);
      }
      length = result.data.count;
    });
    last_page++;
  }

  $scope.loadNextPage = loadNextPage;
});
