/* global angular */
app.directive('mtTorrentsListHeader', function ($mdDialog, TopicsService, ClientsService) {
    return {
        restrict: 'E',
        templateUrl: 'directives/mtTorrentsListHeader/mt-torrents-list-header.html',
        link: function ($scope, element) {
            var AddTorrentDialogController = function($scope, $mdDialog) {
                $scope.isLoading = false;
                $scope.isValid = false;
                $scope.url = "";
                $scope.has_download_dir = null;

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

                ClientsService.default_client().then(function (data) {
                    $scope.default_client = data.data.name;
                    $scope.has_download_dir = data.data.fields.indexOf('download_dir') >= 0;
                });
            };

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
        }
    };
});
