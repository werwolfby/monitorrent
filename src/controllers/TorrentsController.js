app.controller('TorrentsController', function ($scope, TorrentsService, $mdDialog, $log) {
    function updateTorrents() {
        TorrentsService.all().success(function (data) {
            $scope.torrents = data;
        });
    }

    function AddTorrentDialogController($scope, $mdDialog) {
        $scope.cancel = function() {
            $mdDialog.cancel();
        };
        $scope.add = function() {
            TorrentsService.add($scope.url, $scope.settings).then(function() {
                $mdDialog.hide();
            });
        };
        $scope.parseUrl = function () {
            $scope.isloading = true;
            $scope.isloaded = false;
            $scope.disabled = true;
            TorrentsService.parseUrl($scope.url).success(function (data) {
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

    function EditTorrentDialogController($scope, $mdDialog, isEdit, tracker, id) {
        $scope.cancel = function() {
            $mdDialog.cancel();
        };
        $scope.add = function() {
            TorrentsService.add($scope.url, $scope.settings).then(function() {
                $mdDialog.hide();
            });
        };
        TorrentsService.getSettings(tracker, id).then(function(data) {
            $scope.form = data.form;
            $scope.settings = data.settings;
        });
        $scope.isReadOnly = isEdit;
        $scope.url = "";
        $scope.disabled = true;
        $scope.isloading = false;
        $scope.isloaded = false;
    }

    $scope.editTorrent = function(ev, tracker, id) {
        $mdDialog.show({
            controller: EditTorrentDialogController,
            templateUrl: 'views/edit-torrent-dialog.html',
            parent: angular.element(document.body),
            targetEvent: ev,
            locals: {
                isEdit: true,
                tracker: tracker,
                id: id
            }
        }).then(function() {
            updateTorrents();
        }, function() {
            updateTorrents();
        });
    };

    $scope.deleteTorrent = function (url) {
        TorrentsService.delete(url).success(function (data) {
            updateTorrents();
        });
    };

    $scope.showAddTorrentDialog = function (ev) {
        $mdDialog.show({
            controller: AddTorrentDialogController,
            templateUrl: 'views/add-torrent-dialog.html',
            parent: angular.element(document.body),
            targetEvent: ev,
            locals: {
                isEdit: false
            }
        }).then(function() {
            updateTorrents();
        }, function() {
            updateTorrents();
        });
    };

    updateTorrents();
});
