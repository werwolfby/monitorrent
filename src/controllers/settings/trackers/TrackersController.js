app.controller('TrackersController', function ($scope, TrackersService, mtRoutes, $location) {

    $scope.trackers = [];

    TrackersService.trackers().then(function (data) {
        data.data.forEach(function (tracker) {
            $scope.trackers.push(tracker.name);
        });
    });
    
    $scope.path = $location.path();
    
});
