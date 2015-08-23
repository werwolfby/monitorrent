app.controller('TrackersController', function ($scope, TrackersService, $mdToast) {
    $scope.save = function (client, credentials) {
        TrackersService.save(client, credentials).then(function () {
            $mdToast.show(
                $mdToast.simple()
                    .content('Credential saved')
                    .position('right top')
                    .hideDelay(3000)
            );
        });
    };

    $scope.check = function (client) {
        TrackersService.check(client).then(function (data) {
            var message = data.data.status ? 'Connection successful' : 'Connection failed';
            $mdToast.show(
                $mdToast.simple()
                    .content(message)
                    .position('right top')
                    .hideDelay(3000)
            );
        });
    };

    TrackersService.trackers().then(function (data) {
        $scope.trackers = [];
        data.data.forEach(function (t) {
            var tracker = {name: t.name, form: t.form};
            TrackersService.load(t.name).then(function (data) {
                tracker.settings = angular.extend({}, data.data, {'password': '******'});
            });
            $scope.trackers.push(tracker);
        });
    });
});
