app.controller('LogsController', function ($scope, $http, $filter, ExecuteService, mtToastService) {
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

    $scope.updateInterval = function (interval) {
        $http.put('/api/settings/logs', {interval: interval})/*.then(function (data) {
            mtToastService.show('Interval updated');
        })*/;
    };

    function loadNextPage() {
        $scope.executing = true;
        
        if (length > 0 && last_page * PAGE_SIZE >= length)
            return;
        
        ExecuteService.logs(last_page * PAGE_SIZE, PAGE_SIZE).then(
            function (result) {
                for (var i = 0; i < result.data.data.length; i++) {
                    $scope.executes.push(result.data.data[i]);
                }
                
                length = result.data.count;
                $scope.executing = false;
            },
            function() {
                $scope.executing = false;
            }
        );
        
        last_page++;
    }

    $http.get('/api/settings/logs').then(function (data) {
        $scope.interval = data.data.interval;
    });

    $scope.loadNextPage = loadNextPage;
});
