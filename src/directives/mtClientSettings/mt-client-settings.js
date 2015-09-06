app.directive('mtClientSettings', function ($compile, ClientsService) {
    return {
        restrict: 'E',
        templateUrl: 'directives/mtClientSettings/mtClientSettings.html',
        link: function (scope, element, attributes) {

            ClientsService.clients().then(function (data) {
                scope.client = _.findWhere(data.data, { name: attributes.client });
            }).then(function () {
                ClientsService.load(scope.client.name).then(function (data) {
                    if (Object.keys(data.data).length > 0) {
                        data.data = angular.extend({}, data.data, {'password': '******'});
                    }
                    scope.client.settings = data.data;
                });
            });

            scope.save = function (client, credentials) {
                ClientsService.save(client, credentials);
            };

            scope.check = function (client) {
                ClientsService.check(client);
            };
        }
    };
});
