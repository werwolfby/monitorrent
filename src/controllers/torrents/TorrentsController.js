/* global angular */
/* global app */
app.controller('TorrentsController', function ($scope, TopicsService, $mdDialog) {
	$scope.order = "-last_update";
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

	$scope.deleteTorrent = function (id) {
		TopicsService.delete(id).success(function (data) {
			updateTorrents();
		});
	};

	$scope.$on('mt-torrent-added', function () {
		updateTorrents();
	});

	updateTorrents();
});
