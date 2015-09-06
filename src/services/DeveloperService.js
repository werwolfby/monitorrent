app.factory('DeveloperService', function ($http, $q) {
    var developerService = {
        get: function () {
            var deferred = $q.defer();
            deferred.resolve(false);
            return deferred.promise;
        },
        put: function () {
            var deferred = $q.defer();
            deferred.resolve();
            return deferred.promise;
        }
    };

    return developerService;
});
