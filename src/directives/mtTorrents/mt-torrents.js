app.directive('mtTorrents', function (TopicsService, $mdDialog) {
    return {
        restrict: 'E',
        templateUrl: 'directives/mtTorrents/mt-torrents.html',
        link: function (scope, element) {
            function updateTorrents() {
                TopicsService.all().success(function (data) {
                    scope.torrents = data;
                });
            }

            function EditTorrentDialogController(scope, $mdDialog, id) {
                scope.cancel = function () {
                    $mdDialog.cancel();
                };
                scope.save = function () {
                    TopicsService.saveSettings(id, scope.settings).then(function () {
                        $mdDialog.hide();
                    });
                };
                TopicsService.getSettings(id).success(function (data) {
                    scope.form = data.form;
                    scope.settings = data.settings;
                    scope.disabled = false;
                });
                scope.disabled = true;
                scope.isloading = false;
                scope.isloaded = false;
            }

            scope.editTorrent = function (ev, id) {
                $mdDialog.show({
                    controller: EditTorrentDialogController,
                    templateUrl: 'views/edit-torrent-dialog.html',
                    parent: angular.element(document.body),
                    targetEvent: ev,
                    locals: {
                        id: id
                    }
                }).then(function () {
                    updateTorrents();
                }, function () {
                    updateTorrents();
                });
            };

            scope.deleteTorrent = function (id) {
                TopicsService.delete(id).success(function (data) {
                    updateTorrents();
                });
            };

            scope.$on('mt-torrent-added', function () {
                updateTorrents();
            });

            updateTorrents();
        }
    };
});
