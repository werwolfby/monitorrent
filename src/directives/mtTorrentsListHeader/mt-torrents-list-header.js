/* global angular */
app.directive('mtTorrentsListHeader', function ($mdDialog, TopicsService) {
    return {
        restrict: 'E',
        templateUrl: 'directives/mtTorrentsListHeader/mt-torrents-list-header.html',
        link: function (scope, element) {
            
            
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

            scope.addTorrent = function (ev) {
                $mdDialog.show({
                    controller: AddTorrentDialogController,
                    templateUrl: 'directives/mtTorrentsListHeader/mt-add-torrent-dialog.html',
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
