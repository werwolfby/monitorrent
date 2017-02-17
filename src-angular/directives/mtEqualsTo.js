app.directive('mtEqualsTo', function($compile, $parse) {
    return {
        require: "ngModel",
        scope: {
            otherModelValue: "=mtEqualsTo",
            revert: "=?mtEqualsToRevert"
        },
        link: function(scope, element, attributes, ngModel) {
            
            scope.revert = angular.isDefined(scope.revert) && _.isBoolean(scope.revert) ? scope.revert : false;

            ngModel.$validators.mtEqualsTo = function(modelValue) {
                if(!_.isObject(scope.otherModelValue)) {
                    return true;
                }
                
                if(scope.revert) {
                    return modelValue !== scope.otherModelValue.$viewValue;
                } else {
                    return modelValue === scope.otherModelValue.$viewValue;
                }
                
            };

            scope.$watch("otherModelValue.$viewValue", function() {
                ngModel.$validate();
            });
        }
    };
});
