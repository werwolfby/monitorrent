app.controller('NotifiersController', function ($scope, NotifiersService, mtToastService, $location) {

    $scope.notifiers = [];

    NotifiersService.notifiers().then(function (data) {
        data.data.forEach(function (notifier) {
            $scope.notifiers.push(notifier);
        });
    });

    $scope.path = $location.path();
    $scope.set_enabled = function(notifier){
        NotifiersService.set_enabled(notifier.name, notifier.enabled);
    };

    $scope.set_notify_on = function (notify, value) {
    };

    $scope.listClicked=function(ev){
        // don't delete this method it is required for multiple checkbox in list item.
        ev.stopPropagation();
    };
});
