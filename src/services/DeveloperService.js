app.factory('DeveloperService', function ($http, $q, $log) {
    var isDev;
    
    return {
        get: function () {
            var deferred = $q.defer();
            
            if(_.isBoolean(isDev)) {
                deferred.resolve(isDev);
                return deferred.promise;
            }
            
            $http.get('/api/settings/developer').then(function (data){
                isDev = data.data.is_developer_mode;
                deferred.resolve(isDev);
            });
            
            return deferred.promise;
        },
        put: function (value) {
            if(!_.isBoolean(value)) {
                return $q(function(res, rej) {
                    var err = "Wrong dev flag value (should be boolean)";
                    $log.error(err);
                    rej(err);
                });
            }
            
            return $http.put('/api/settings/developer', {'is_developer_mode': value}).then(function() {
                isDev = value;
            });
        }
    };
});
