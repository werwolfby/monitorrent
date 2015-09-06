app.directive('mtTrackerSettings', function ($compile, TrackersService) {
    return {
        restrict: 'E',
        templateUrl: 'directives/mtTrackerSettings/mtTrackerSettings.html',
        link: function (scope, element, attributes) {

            TrackersService.trackers().then(function (data) {
                scope.tracker = _.findWhere(data.data, {name: attributes.tracker});
            }).then(function () {
                TrackersService.load(scope.tracker.name).then(function (data) {
                    if (Object.keys(data.data).length > 0) {
                        data.data = angular.extend({}, data.data, {'password': '******'});
                    }
                    scope.tracker.settings = data.data;
                });
            });

            scope.save = function (client, credentials) {
                TrackersService.save(client, credentials);
            };

            scope.check = function (client) {
                TrackersService.check(client);
            };
        }
    };
});
