app.controller('NotifiersController', function ($scope, NotifiersService, mtToastService, $location) {

    $scope.notifiers = [];

    NotifiersService.notifiers().then(function (data) {
        data.data.forEach(function (notifier) {
            $scope.notifiers.push(notifier);
        });
    });

    NotifiersService.get_notify_on().then(function (data) {
        var levels = data.data;

        $scope.notify_on_download = levels.indexOf('DOWNLOAD') >= 0;
        $scope.notify_on_error = levels.indexOf('ERROR') >= 0;
        $scope.notify_on_status_changed = levels.indexOf('STATUS_CHANGED') >= 0;

        $scope.levels = levels;
    });

    $scope.path = $location.path();
    $scope.set_enabled = function(notifier){
        NotifiersService.set_enabled(notifier.name, notifier.enabled);
    };

    $scope.set_notify_on = function(field, value) {
        var idx = $scope.levels.indexOf(field);
        if (idx >= 0 && !value) {
            $scope.levels.splice(idx, 1);
        } else {
            $scope.levels.push(field);
        }

        NotifiersService.set_notify_on($scope.levels);
    };

    $scope.listClicked=function(ev){
        // don't delete this method it is required for multiple checkbox in list item.
        ev.stopPropagation();
    };
});
