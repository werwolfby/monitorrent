app.controller('ClientsController', function ($scope, ClientsService, $mdToast) {
    $scope.save = function (client, credentials) {
        ClientsService.save(client, credentials).then(function () {
            $mdToast.show(
                $mdToast.simple()
                    .content('Credential saved')
                    .position('right top')
                    .hideDelay(3000)
            );
        });
    };

    $scope.check = function (client) {
        ClientsService.check(client).then(function (data) {
            var message = data.data.status ? 'Connection successful' : 'Connection failed';
            $mdToast.show(
                $mdToast.simple()
                    .content(message)
                    .position('right top')
                    .hideDelay(3000)
            );
        });
    };

    ClientsService.clients().then(function (data) {
        $scope.clients = [];
        data.data.forEach(function (c) {
            var client = {name: c.name, form: c.form};
            ClientsService.load(c.name).then(function (data) {
                client.settings = angular.extend({}, data.data, {'password': '******'});
            });
            $scope.clients.push(client);
        });
    });

});
