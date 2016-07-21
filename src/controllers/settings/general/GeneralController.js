app.controller('GeneralController', function ($scope, GeneralService) {
    GeneralService.getIsDeveloperMode().then(function(value) {
		$scope.isDeveloper = value;
	});

	$scope.proxyEnabled = false;
    $scope.proxyServer0 = "";
	$scope.proxyServer1 = "";

	GeneralService.getProxyEnabled().then(function (data){
	    $scope.proxyEnabled = data.data.enabled;
	});

	$scope.toggleProxyEnabled = function () {
	    GeneralService.putProxyEnabled($scope.proxyEnabled);
	};

	GeneralService.getProxyServer(0).then(function (data){
	    $scope.proxyServer0 = data.data.value;
	});

	GeneralService.getProxyServer(1).then(function (data){
	    $scope.proxyServer1 = data.data.value;
	});

	function proxyServerChanged(id, value) {
	    if (value != "") {
		    GeneralService.putProxyServer(id, value);
        }
        else {
            GeneralService.deleteProxyServer(id);
        }
	};

	$scope.$watch("proxyServer0", function(newValue, oldValue) {
	    proxyServerChanged(0, newValue);
	});

	$scope.$watch("proxyServer1", function(newValue, oldValue) {
		proxyServerChanged(1, newValue);
	});

	$scope.toggleDevMode = function () {
		GeneralService.putIsDeveloperMode($scope.isDeveloper).then(
			function () {},
			function () {
				$scope.isDeveloper = !$scope.isDeveloper;
			});
	};
});

