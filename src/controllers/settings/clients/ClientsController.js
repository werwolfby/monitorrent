app.controller('ClientsController', function ($scope, ClientsService, mtToastService, $location) {
    
    $scope.clients = [];
    
    var setClient = function(client) {
        $scope.default_client = client;
        $scope.default_client_view = client;
    }
    
    setClient(null);

    ClientsService.clients().then(function (data) {
        data.data.forEach(function (client) {
            $scope.clients.push(client.name);
            if (client.is_default) {
                setClient(client.name);
            }
        });
    });

    $scope.is_default = function (client) {
        return client == $scope.default_client;
    };

    $scope.set_default = function () {
        var client = $scope.default_client_view; 
        $scope.default_client_view = $scope.default_client;
        
        ClientsService.set_default(client).then(function(){
            setClient(client);
        });
    };
    
    $scope.path = $location.path();

});
