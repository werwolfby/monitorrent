from monitorrent.plugins.trackers import TrackerSettings


class TrackerSettingsMock(TrackerSettings):
    def get_requests_kwargs(self):
        result = super(TrackerSettingsMock, self).get_requests_kwargs()
        result.pop('timeout')
        result['verify'] = False
        return result
