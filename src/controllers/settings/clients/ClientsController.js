app.controller('ClientsController', function ($scope, ClientsService, mtToastService, $location) {
    
    $scope.clients = [];

    $scope.default_client = null;

    ClientsService.clients().then(function (data) {
        data.data.forEach(function (client) {
            $scope.clients.push(client.name);
            if (client.is_default) {
                $scope.default_client = client.name;
            }
        });
    });

    $scope.is_default = function (client) {
        return client == $scope.default_client;
    };

    $scope.set_default = function (client) {
        ClientsService.set_default(client).then(function(){
            $scope.default_client = client;
        });
    };
    
    $scope.path = $location.path();

});
