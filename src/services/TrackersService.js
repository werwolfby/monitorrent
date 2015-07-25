app.factory('TrackersService', function ($http) {
    return {
        trackers: function () {
            return $http.get('/api/trackers');
        },
        save: function (tracker, data) {
            return $http.put('/api/trackers/' + tracker, data);
        },
        load: function (tracker) {
            return $http.get('/api/trackers/' + tracker);
        },
        check: function (tracker) {
            return $http.get('/api/check_tracker', {params: {tracker: tracker}});
        }
    };
});
