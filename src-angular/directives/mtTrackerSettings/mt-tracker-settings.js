app.directive('mtTrackerSettings', function ($compile, TrackersService) {
    return {
        restrict: 'E',
        templateUrl: 'directives/mtTrackerSettings/mtTrackerSettings.html',
        link: function (scope, element, attributes) {
            TrackersService.trackers().then(function (data) {
                scope.tracker = _.findWhere(data.data, {name: attributes.tracker});
            }).then(function () {
                TrackersService.load(scope.tracker.name).then(function (data) {
                    if (Object.keys(data.data.settings).length > 0) {
                        data.data.settings = angular.extend({}, data.data.settings, {'password': '******'});
                    }
                    scope.tracker.settings = data.data.settings;
                    scope.tracker.can_check = data.data.can_check;
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
