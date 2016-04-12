/* global angular */
app.directive('mtTorrentsExecuteHeader', function ($timeout, ExecuteService) {
    return {
        restrict: 'E',
        scope: {torrents: '='},
        templateUrl: 'directives/mtTorrentsExecuteHeader/mt-torrents-execute-header.html',
        link: function ($scope, element) {
            $scope.executing = null;
            $scope.latest_log_message = null;

            $scope.executeAllClicked = function () {
                ExecuteService.executeAll();
            };

            $scope.executeErrorsClicked = function () {
                ExecuteService.executeErrors();
            };

            var getStatus = function(execute) {
                if ((execute.status == 'failed' && !execute.is_running) || execute.failed > 0) {
                    return ['color-failed'];
                } else if (execute.downloaded > 0) {
                    return ['color-downloaded'];
                }
                return [];
            };

            var updateRelativeExecute = function() {
                $scope.relative_execute = moment($scope.execute.finish_time).fromNow();
            };

            var updateExecuteStatus = function() {
                ExecuteService.logs(0, 1).then(function (data) {
                    if ($scope.executing) {
                        return;
                    }

                    $scope.execute = data.data.data.length > 0 ? data.data.data[0] : null;
                    if ($scope.execute) {
                        $scope.status = getStatus($scope.execute);
                        updateRelativeExecute();
                        if ($scope.latest_log_message) {
                            $scope.execute.id = $scope.latest_log_message.execute_id;
                            $scope.execute.finish_time = $scope.latest_log_message.time;
                        }
                    } else {
                        $scope.no_executes = true;
                    }
                });
            };

            updateExecuteStatus();

            var updateRelativeExecuteHandler = function() {
                if ($scope.executing) {
                    return;
                }
                if ($scope.execute) {
                    updateRelativeExecute();
                }
                $timeout(updateRelativeExecuteHandler, 1000 * 60);
            };

            $timeout(updateRelativeExecuteHandler, 1000 * 60);

            var executeStarted = function () {
                $scope.latest_log_message = null;
                $scope.executing = {status: 'in progress', failed: 0, downloaded: 0};
                $scope.status = getStatus($scope.executing);
            };

            var executeEvents = function (logs) {
                if (logs.length === 0) {
                    return;
                }

                for (var i = 0; i < logs.length; i++) {
                    if (logs[i].level == 'failed') {
                        $scope.executing.failed++;
                        $scope.latest_log_message = logs[i];
                    } else if (logs[i].level == 'downloaded') {
                        $scope.executing.downloaded++;
                        $scope.latest_log_message = logs[i];
                    }
                }
                if ($scope.latest_log_message === null || $scope.latest_log_message.level == 'info') {
                    $scope.latest_log_message = logs[logs.length - 1];
                }
                if (!$scope.execute) {
                    $scope.execute = {};
                }
                $scope.execute.id = $scope.latest_log_message.execute_id;
                $scope.execute.finish_time = $scope.latest_log_message.time;
                $scope.status = getStatus($scope.executing);
            };

            var executeFinished = function () {
                $scope.executing = null;
                updateRelativeExecute();
                updateRelativeExecuteHandler();
                $scope.$emit('execute.finished', true);
            };

            var unsubscribe = ExecuteService.subscribe({started: executeStarted, events: executeEvents, finished: executeFinished});

            $scope.$on('$destroy', function() {
                if (unsubscribe) {
                    unsubscribe();
                }
            });

            $scope.hasErrorTorrents = function () {
                if (!$scope.torrents) {
                    return false;
                }

                var withErrors = $scope.torrents.filter(function (t) {
                    return t.status == 'Error';
                });

                return withErrors.length > 0;
            }
        }
    };
});
