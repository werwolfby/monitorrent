app.directive('mtClientSettings', function ($compile, ClientsService) {
    return {
        restrict: 'E',
        templateUrl: 'directives/mtClientSettings/mtClientSettings.html',
        link: function (scope, element, attributes) {

            ClientsService.clients().then(function (data) {
                scope.client = _.findWhere(data.data, { name: attributes.client });
            }).then(function () {
                ClientsService.load(scope.client.name).then(function (data) {
                    scope.client.settings = angular.extend({}, data.data, { 'password': '******' });
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
