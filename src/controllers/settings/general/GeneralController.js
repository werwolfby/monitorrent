app.controller('GeneralController', function ($scope, GeneralService) {
    GeneralService.getIsDeveloperMode().then(function(value) {
        $scope.isDeveloper = value;
    });

    $scope.proxyEnabled = false;
    $scope.cloudflareChallengeSolverDebug = false;
    $scope.cloudflareChallengeSolverRecordVideo = false;
    $scope.cloudflareChallengeSolverRecordHAR = false;
    $scope.cloudflareChallengeSolverKeepRecords = 3;
    $scope.httpProxyServer = $scope.httpsProxyServer = null;
    $scope.newVersionCheckEnabled = false;
    $scope.includePrerelease = false;
    $scope.checkInterval = 60;

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

    $scope.$watch("newVersionCheckEnabled", function(newValue, oldValue) {
        if (newValue === oldValue) {
            return;
        }
        GeneralService.patchNewVersionCheckerSettings(null, newValue, null);
    });

    $scope.$watch("includePrerelease", function(newValue, oldValue) {
        if (newValue === oldValue) {
            return;
        }
        GeneralService.patchNewVersionCheckerSettings(newValue, null, null);
    });

    $scope.$watch("checkInterval", function(newValue, oldValue) {
        if (newValue === oldValue) {
            return;
        }
        GeneralService.patchNewVersionCheckerSettings(null, null, (+newValue) * 60);
    });

    GeneralService.getNewVersionCheckerSettings().then(function (data) {
        $scope.newVersionCheckEnabled = data.data.enabled;
        $scope.includePrerelease = data.data.include_prerelease;
        $scope.checkInterval = data.data.interval / 60;
    });

    GeneralService.getCloudflareChallengeSolverSettings().then(function (data) {
        $scope.cloudflareChallengeSolverDebug = data.data.debug;
        $scope.cloudflareChallengeSolverRecordVideo = data.data.record_video;
        $scope.cloudflareChallengeSolverRecordHAR = data.data.record_har;
        $scope.cloudflareChallengeSolverKeepRecords = data.data.keep_records;
    });

    $scope.toggleDevMode = function () {
        GeneralService.putIsDeveloperMode($scope.isDeveloper).then(
            function () {},
            function () {
                $scope.isDeveloper = !$scope.isDeveloper;
            });
    };

    $scope.$watch("cloudflareChallengeSolverDebug", function(newValue, oldValue) {
        if (newValue === oldValue) {
            return;
        }
        GeneralService.patchCloudflareChallengeSolverSettings(newValue, null, null, null);
    });

    $scope.$watch("cloudflareChallengeSolverRecordVideo", function(newValue, oldValue) {
        if (newValue === oldValue) {
            return;
        }
        GeneralService.patchCloudflareChallengeSolverSettings(null, newValue, null, null);
    });

    $scope.$watch("cloudflareChallengeSolverRecordHAR", function(newValue, oldValue) {
        if (newValue === oldValue) {
            return;
        }
        GeneralService.patchCloudflareChallengeSolverSettings(null, null, newValue, null);
    });

    $scope.$watch("cloudflareChallengeSolverKeepRecords", function(newValue, oldValue) {
        if (newValue === oldValue) {
            return;
        }
        GeneralService.patchCloudflareChallengeSolverSettings(null, null, null, parseInt(newValue));
    });
});

