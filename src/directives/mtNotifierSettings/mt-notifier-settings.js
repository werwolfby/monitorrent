app.directive('mtNotifierSettings', function ($compile, NotifiersService) {
    return {
        restrict: 'E',
        templateUrl: 'directives/mtNotifierSettings/mtNotifierSettings.html',
        link: function (scope, element, attributes) {

            NotifiersService.notifiers().then(function (data) {
                scope.notifier = _.findWhere(data.data, { name: attributes.notifier });
            }).then(function () {
                NotifiersService.load(scope.notifier.name).then(function (data) {
                    if (Object.keys(data.data).length > 0) {
                        data.data = angular.extend({}, data.data, {'password': '******'});
                    }
                    scope.notifier.settings = data.data;
                });
            });

            scope.save = function (notifier, data) {
                NotifiersService.save(notifier, data);
            };

            scope.check = function (notifier) {
                NotifiersService.check(notifier);
            };
        }
    };
});
