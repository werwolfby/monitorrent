/* global angular */
/* global app */
app.controller('TorrentsController', function ($scope, $rootScope, TopicsService, ExecuteService, $mdDialog) {
	$scope.order = "-last_update";
	$scope.orderReverse = true;
	$scope.filter = "";

	$scope.smartFilter = function (value, index, array) {
		function filterValue(param) {
			return value.display_name.toLowerCase().indexOf(param) > -1 ||
			       value.tracker.toLowerCase().indexOf(param) > -1;
		}

		var filter = $scope.filter;
		var filterParams = filter.split(' ').filter(function (e) {return e;}).map(function (e) {return e.toLowerCase();});
		// Filter by all values
		return filterParams.filter(filterValue).length == filterParams.length;
	};

	$scope.smartOrder = function (value) {
		var order = $scope.order;
		if (order.substring(0,1) === "-") {
			order = order.substring(1);
		}
		return value[order] || new Date(0);
	};

	$scope.orderChanged = function () {
		$scope.orderReverse = $scope.order.substring(0,1) === "-";
	};

	function updateTorrents() {
		TopicsService.all().success(function (data) {
			$scope.torrents = data;
		});
	}

	function EditTorrentDialogController($scope, $mdDialog, id) {
		$scope.cancel = function () {
			$mdDialog.cancel();
		};
		$scope.save = function () {
			TopicsService.saveSettings(id, $scope.settings).then(function () {
				$mdDialog.hide();
			});
		};
		TopicsService.getSettings(id).success(function (data) {
			$scope.form = data.form;
			$scope.settings = data.settings;
			$scope.disabled = false;
		});
		$scope.disabled = true;
		$scope.isloading = false;
		$scope.isloaded = false;
	}

	$scope.editTorrent = function (ev, id) {
		$mdDialog.show({
			controller: EditTorrentDialogController,
			templateUrl: 'controllers/torrents/edit-torrent-dialog.html',
			parent: angular.element(document.body),
			targetEvent: ev,
			locals: {
				id: id
			}
		}).then(function () {
			updateTorrents();
		});
	};

    $scope.resetTorrentStatus = function (id) {
        TopicsService.resetStatus(id).success(function (data) {
			updateTorrents();
		});
    };

    $scope.executeTorrent = function (id) {
        ExecuteService.execute([id]);
    };

    $scope.executeTracker = function (tracker) {
        ExecuteService.executeTracker(tracker);
    };

	$scope.deleteTorrent = function (id) {
		TopicsService.delete(id).success(function (data) {
			updateTorrents();
		});
	};

	$scope.$on('mt-torrent-added', function () {
		updateTorrents();
	});

    $rootScope.$on('execute.finished', function () {
        updateTorrents();
    });

	updateTorrents();
});
