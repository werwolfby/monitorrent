app.controller('ClientsController', function ($scope, ClientsService, mtToastService, $location) {
    
    $scope.clients = [];

    ClientsService.clients().then(function (data) {
        data.data.forEach(function (client) {
            $scope.clients.push(client.name);
        });
    });
    
    $scope.path = $location.path();

});
