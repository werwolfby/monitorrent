app.factory('mtToastService', function ($mdToast) {
    return {
        show: function (text) {
            $mdToast.show(
                $mdToast.simple()
                    .content(text)
                    .position('top right')
                    .hideDelay(3000)
            );
        }
    };
});
