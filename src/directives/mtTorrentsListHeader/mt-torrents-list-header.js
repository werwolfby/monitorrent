/* global angular */
app.directive('mtTorrentsListHeader', function ($mdDialog, TopicsService, ExecuteService) {
    return {
        restrict: 'E',
        templateUrl: 'directives/mtTorrentsListHeader/mt-torrents-list-header.html',
        link: function ($scope, element) {
            var AddTorrentDialogController = function($scope, $mdDialog) {
                $scope.isLoading = false;
                $scope.isValid = false;
                $scope.url = "";

                $scope.cancel = function () {
                    $mdDialog.cancel();
                };

                $scope.add = function () {
                    TopicsService.add($scope.url, $scope.settings).then(function () {
                        $mdDialog.hide();
                    });
                };

                $scope.parseUrl = function () {
                    $scope.isLoading = true;
                    TopicsService.parseUrl($scope.url).success(function (data) {
                        $scope.form = data.form;
                        $scope.settings = data.settings;
                        $scope.isValid = true;
                        $scope.isLoading = false;
                    }).error(function () {
                        $scope.isValid = false;
                        $scope.isLoading = false;
                    });
                };
            };

            function getStatus(execute) {
                if ((execute.status == 'failed' && !execute.is_running) || execute.failed > 0) {
                    return ['color-failed'];
                } else if (execute.downloaded > 0) {
                    return ['color-downloaded'];
                }
                return [];
            }

            function updateExecuteStatus() {
                ExecuteService.logs(0, 1).then(function (data) {
                    $scope.execute = data.data.data[0];
                    $scope.relative_execute = moment($scope.execute.finish_time).fromNow();
                    $scope.status = getStatus($scope.execute);
                    if ($scope.latest_log_message) {
                        $scope.execute.id = $scope.latest_log_message.execute_id;
                        $scope.execute.finish_time = $scope.latest_log_message.time;
                    }
                });
            }

            $scope.executing = null;
            $scope.latest_log_message = null;

            $scope.executeClicked = function () {
                ExecuteService.execute();
            };

            updateExecuteStatus();

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
                if ($scope.execute) {
                    $scope.execute.id = $scope.latest_log_message.execute_id;
                    $scope.execute.finish_time = $scope.latest_log_message.time;
                }
                $scope.status = getStatus($scope.executing);
            };

            var executeFinished = function () {
                $scope.executing = null;
                $scope.relative_execute = moment($scope.execute.finish_time).fromNow();
                $scope.$emit('execute.finished', true);
            };

            var unsubscribe = ExecuteService.subscribe({started: executeStarted, events: executeEvents, finished: executeFinished});

            $scope.addTorrent = function (ev) {
                $mdDialog.show({
                    controller: AddTorrentDialogController,
                    templateUrl: 'directives/mtTorrentsListHeader/mt-add-torrent-dialog.html',
                    parent: angular.element(document.body),
                    targetEvent: ev,
                    locals: {
                        isEdit: false
                    }
                }).then(function () {
                    $scope.$emit('mt-torrent-added');
                });
            };

            $scope.$on('$destroy', function() {
                if (unsubscribe) {
                    unsubscribe();
                }
            });
        }
    };
});
