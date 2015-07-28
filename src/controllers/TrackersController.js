app.controller('TrackersController', function ($scope, TrackersService, $mdToast, $compile, DynamicForm) {
    $scope.save = function (client, credentials) {
        TrackersService.save(client, credentials).then(function () {
            $mdToast.show(
                $mdToast.simple()
                    .content('Credential saved')
                    .position('right top')
                    .hideDelay(3000)
            );
        });
    };

    $scope.check = function (client) {
        TrackersService.check(client).then(function () {
            $mdToast.show(
                $mdToast.simple()
                    .content('Connection successful')
                    .position('right top')
                    .hideDelay(3000)
            );
        }, function () {
            $mdToast.show(
                $mdToast.simple()
                    .content('Connection failed')
                    .position('right top')
                    .hideDelay(3000)
            );
        });
    };

    TrackersService.trackers().then(function (data) {
        $scope.trackers = [];
        data.data.forEach(function (t) {
            var tracker = {name: t.name};
            TrackersService.load(t.name).then(function (data) {
                tracker.credentials = angular.extend({}, data.data, {'password': '******'});
            });
            $scope.trackers.push(tracker);
        });
    });

    var data = [
        {
            "type": "row",
            "content": [{
                "type": "text",
                "model": "username1",
                "label": "Username",
                "flex": 45
            }, {
                "type": "password",
                "model": "password1",
                "label": "Password",
                "flex": 45
            }, {
                "type": "text",
                "model": "password",
                "label": "Test",
                "flex": 10
            }]
        },{
            "type": "row",
            "content": [{
                "type": "text",
                "model": "username2",
                "label": "Username",
                "flex": 45
            }, {
                "type": "password",
                "model": "password2",
                "label": "Password",
                "flex": 45
            }, {
                "type": "select",
                "model": "quality",
                "label": "Default Quality",
                "options": ["SD", "720p", "1080p"],
                "flex": 10
            }]
        }];

    $scope.testCallback = function() {
        alert($scope.test);
    };

    var elem = angular.element( document.querySelector( '#testtitle' ) );
    var form = DynamicForm($scope, data, 'test');
    elem.append(form);

});
