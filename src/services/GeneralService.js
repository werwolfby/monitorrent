app.factory('GeneralService', function ($http, $q, $log) {
    var isDev;
    
    return {
        getIsDeveloperMode: function () {
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
        putIsDeveloperMode: function (value) {
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
        },
        getProxyEnabled: function () {
            return $http.get('/api/settings/proxy/enabled');
        },
        putProxyEnabled: function (value) {
            return $http.put('/api/settings/proxy/enabled', {'enabled': value});
        },
        getProxyServer: function (key) {
            return $http.get('/api/settings/proxy', {params: {key: key}});
        },
        putProxyServer: function (key, value) {
            return $http.put('/api/settings/proxy', {'url': value}, {params: {key: key}});
        },
        deleteProxyServer: function (key) {
            return $http.delete('/api/settings/proxy', {params: {key: key}});
        }
    };
});
