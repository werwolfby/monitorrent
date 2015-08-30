/* global _ */
app.provider('mtRoutes', function MtRoutesProvider() {
  var routes = {
    main: [
      { href: "/torrents", include: 'controllers/torrents/torrents-partial.html', label: 'Torrents', controller: 'TorrentsController', icon: 'get-app' },
      { href: "/settings", include: 'controllers/settings/settings-partial.html', label: 'Settings', controller: 'SettingsController', icon: 'settings' },
      { href: "/logs", include: 'controllers/logs/logs-partial.html', label: 'Logs', controller: 'LogsController', icon: 'align-left', dev: true },
      { href: "/execute", include: 'controllers/execute/execute-partial.html', label: 'Execute', controller: 'ExecuteController', icon: 'input', dev: true },
      { href: "/about", include: 'controllers/about/about-partial.html', label: 'About', controller: 'AboutController', icon: 'group' }
    ],
    settings: [
      { href: "/settings/trackers", include: 'controllers/settings/trackers/trackers-partial.html', label: 'Trackers', controller: 'TrackersController', icon: 'settings-input-component' },
      { href: "/settings/trackers/:tracker", include: 'controllers/settings/trackers/details/details-partial.html', label: 'Tracker settings details', controller: 'TrackerDetailsController', icon: 'settings-input-component', ignore: true },
      { href: "/settings/clients", include: 'controllers/settings/clients/clients-partial.html', label: 'Clients', controller: 'ClientsController', icon: 'dns' },
      { href: "/settings/clients/:client", include: 'controllers/settings/clients/details/details-partial.html', label: 'Clients', controller: 'ClientDetailsController', icon: 'dns', ignore: true },
      { href: "/settings/authentication", include: 'controllers/settings/authentication/authentication-partial.html', label: 'Authentication', controller: 'AuthenticationController', icon: 'security' },
      // { href: "/settings/appearance", include: 'controllers/settings/appearance/appearance-partial.html', label: 'Appearance', controller: 'AppearanceController', icon: 'color-lens' },
      // { href: "/settings/schedule", include: 'controllers/settings/schedule/schedule-partial.html', label: 'Schedule', controller: 'ScheduleController', icon: 'schedule' },
      { href: "/settings/developer", include: 'controllers/settings/developer/developer-partial.html', label: 'Developer', controller: 'DeveloperController', icon: 'code' }
    ]
  };

  var getRouteByPath = function (path) {
    return _.chain(routes)
      .values()
      .reduce(function (a, b) { return a.concat(b); })
      .findWhere({ href: path })
      .value();
  };

  var prevRoute;

  var result = {
    routes: routes,
    getRouteByPath: getRouteByPath,
    prevRoute: {
      get: function () {
        return prevRoute;
      },
      set: function (path) {
        if (path === undefined) {
          return;
        }

        prevRoute = getRouteByPath(path);
      }
    }
  };

  _.extend(this, result);

  this.$get = function mtRoutesFactory() {
    return result;
  };
});