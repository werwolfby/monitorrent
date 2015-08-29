app.directive('mtDynamicForm', function($compile, $parse) {
    return {
        link: function($scope, element, attrs) {
            var sourceElement = element;

            var createRow = function (data, scopePrefix) {
                var row = angular.element('<div layout="row"></div>');
                if (attrs.layoutPadding !== undefined) {
                    row.attr('layout-padding', '');
                }
                var content = data.content;
                if (!Array.isArray(content)) {
                    content = [content];
                }
                for (var i = 0; i < content.length; i++) {
                    var contentElem = createContent(content[i], scopePrefix);
                    row.append(contentElem);
                }
                return row;
            };

            var createText = function (data, scopePrefix) {
                var inputContainer = angular.element('<md-input-container>')
                    .attr('flex', data.flex);
                var label = angular.element('<label>').html(data.label);
                var modelScript = scopePrefix + '.' + data.model;
                var input = angular.element('<input>')
                    .attr('type', data.type)
                    .attr('ng-model', modelScript);
                if (data.value) {
                    var model = $parse(modelScript);
                    model.assign($scope, data.value);
                }
                return inputContainer.append(label).append(input);
            };

            var createSelect = function (data, scopePrefix) {
                var inputContainer = angular.element('<md-input-container>')
                    .attr('flex', data.flex);
                var label = angular.element('<label>').html(data.label);
                var select = angular.element('<md-select>')
                    .attr('ng-model', scopePrefix + '.' + data.model);
                for (var i = 0; i < data.options.length; i++) {
                    var option = angular.element('<md-option>')
                        .attr('value', data.options[i])
                        .html(data.options[i]);
                    select.append(option);
                }
                return inputContainer.append(label).append(select);
            };

            var contentFactory = {
                'row': createRow,
                'password': createText,
                'text': createText,
                'number': createText,
                'select': createSelect
            };

            var createContent = function (data, scopePrefix) {
                var factory = contentFactory[data.type];
                if (factory) {
                    return factory(data, scopePrefix);
                }
            };

            var createForm = function (rows, scopePrefix) {
                var result = [];
                for (var i = 0; i < rows.length; i++) {
                    var content = createContent(rows[i], scopePrefix);
                    result.push(content);
                }
                return result;
            };

            var update = function() {
                var data = $parse(attrs.data)($scope);
                if (data) {
                    var model = attrs.model;
                    var newElements = createForm(data, model);
                    for (var i = 0; i < newElements.length; i++) {
                        newElements[i] = $compile(newElements[i])($scope);
                    }
                    var newElement = newElements;
                    if (Array.isArray(sourceElement)) {
                        while (sourceElement.length > 1) {
                            sourceElement.pop().remove();
                        }
                        sourceElement = sourceElement.pop();
                    }
                    sourceElement.replaceWith(newElement);
                    sourceElement = newElement;
                }
            };

            $scope.$watch(attrs.data, function(oldValue, newValue){
                update();
            });

            update();
        }
    };
});