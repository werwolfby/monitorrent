app.controller('GeneralController', function ($scope, GeneralService) {
    GeneralService.getIsDeveloperMode().then(function(value) {
        $scope.isDeveloper = value;
    });

    $scope.proxyEnabled = false;
    $scope.httpProxyServer = $scope.httpsProxyServer = null;

    GeneralService.getProxyEnabled().then(function (data){
        $scope.proxyEnabled = data.data.enabled;
    });

    $scope.toggleProxyEnabled = function () {
        GeneralService.putProxyEnabled($scope.proxyEnabled);
    };

    GeneralService.getProxyServer('http').then(function (data){
        $scope.httpProxyServer = data.data.url;
    });

    GeneralService.getProxyServer('https').then(function (data){
        $scope.httpsProxyServer = data.data.url;
    });

    function proxyServerChanged(id, newValue, oldValue) {
        if (newValue == oldValue) {
            return;
        }
        if (newValue !== "") {
            GeneralService.putProxyServer(id, newValue);
        }
        else {
            GeneralService.deleteProxyServer(id);
        }
    }

    $scope.$watch("httpProxyServer", function(newValue, oldValue) {
        proxyServerChanged('http', newValue, oldValue);
    });

    $scope.$watch("httpsProxyServer", function(newValue, oldValue) {
        proxyServerChanged('https', newValue, oldValue);
    });

    $scope.toggleDevMode = function () {
        GeneralService.putIsDeveloperMode($scope.isDeveloper).then(
            function () {},
            function () {
                $scope.isDeveloper = !$scope.isDeveloper;
            });
    };
});

