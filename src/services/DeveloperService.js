app.factory('DeveloperService', function ($http, $q) {
    return {
        get: function () {
            return $http.get('/api/settings/developer').then(function (data){
                return data.data.is_developer_mode;
            });
        },
        put: function (value) {
            return $http.put('/api/settings/developer', {'is_developer_mode': value});
        }
    };
});
