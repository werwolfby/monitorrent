app.directive('mtTorrentsListHeader', function ($mdDialog, TopicsService) {
    return {
        restrict: 'E',
        templateUrl: 'views/mt-torrents-list-header.html',
        link: function (scope, element) {
            function AddTorrentDialogController($scope, $mdDialog) {
                $scope.cancel = function () {
                    $mdDialog.cancel();
                };
                $scope.add = function () {
                    TopicsService.add($scope.url, $scope.settings).then(function () {
                        $mdDialog.hide();
                    });
                };
                $scope.parseUrl = function () {
                    $scope.isloading = true;
                    $scope.isloaded = false;
                    $scope.disabled = true;
                    TopicsService.parseUrl($scope.url).success(function (data) {
                        $scope.form = data.form;
                        $scope.settings = data.settings;
                        $scope.isError = false;
                        $scope.isloading = false;
                        $scope.isloaded = true;
                        $scope.disabled = false;
                    }).error(function () {
                        $scope.title = "Error";
                        $scope.isError = true;
                        $scope.isloading = false;
                        $scope.isloaded = true;
                        $scope.disabled = true;
                    });
                };
                $scope.url = "";
                $scope.disabled = true;
                $scope.isloading = false;
                $scope.isloaded = false;
            }

            scope.addTorrent = function (ev) {
                $mdDialog.show({
                    controller: AddTorrentDialogController,
                    templateUrl: 'views/add-torrent-dialog.html',
                    parent: angular.element(document.body),
                    targetEvent: ev,
                    locals: {
                        isEdit: false
                    }
                }).then(function () {
                    scope.$emit('mt-torrent-added');
                });
            };
        }
    };
});
