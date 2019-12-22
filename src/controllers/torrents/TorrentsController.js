/* global angular */
/* global app */
app.controller('TorrentsController', function ($scope, $rootScope, TopicsService, ClientsService, ExecuteService, $mdDialog) {
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
		var orderValue = value[order];
		if (order == "last_update") {
			if (orderValue) {
				orderValue = new Date(orderValue);
			} else {
				orderValue = new Date(32503680000000);
			}
		}
		return orderValue;
	};

	$scope.orderChanged = function () {
		$scope.orderReverse = $scope.order.substring(0,1) === "-";
	};

	function updateTorrents() {
		TopicsService.all().success(function (data) {
			angular.forEach(data, function(value, key) {
				if (value.tracker === 'lostfilm.tv') {
					data[key].thumbnail_url = 'https://static.lostfilm.tv/Images/' + value.external_id + '/Posters/icon.jpg';
				} else {
					data[key].thumbnail_url = 'content/images/' + value.tracker + '.png';
				}
			});
			$scope.torrents = data;
		});
	}

	function EditTorrentDialogController($scope, $mdDialog, id) {
		$scope.has_download_dir = null;
		$scope.cancel = function () {
			$mdDialog.cancel();
		};
		$scope.save = function () {
			if ($scope.settings && $scope.settings.download_dir === $scope.client_download_dir) {
				$scope.settings.download_dir = null;
			}
			
			TopicsService.saveSettings(id, $scope.settings).then(function () {
				$mdDialog.hide();
			});
		};
		ClientsService.default_client().then(function (data) {
			$scope.default_client = data.data.name;
			var download_dir = data.data.fields.download_dir;
			$scope.has_download_dir = download_dir !== null && download_dir !== undefined;
			$scope.client_download_dir = download_dir;
			if (!$scope.settings) {
				$scope.settings = {};
			}
			$scope.settings.download_dir = $scope.settings.download_dir || download_dir;
		});
		TopicsService.getSettings(id).success(function (data) {
			$scope.form = data.form;
			if ($scope.settings) {
				data.settings.download_dir = data.settings.download_dir || $scope.settings.download_dir;
			}
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

    $scope.pauseState = function (id, paused) {
        TopicsService.pauseState(id, paused).success(function (data) {
			updateTorrents();
		});
    };

    $scope.hasNotPaused = function (tracker) {
        return $scope.torrents.filter(function (t) {
            return t.tracker === tracker && !t.paused;
        }).length > 0;
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
