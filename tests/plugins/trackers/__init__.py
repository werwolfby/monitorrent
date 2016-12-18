from monitorrent.plugins.trackers import TrackerSettings


class TestTrackerSettings(TrackerSettings):
    def get_requests_kwargs(self):
        result = super(TestTrackerSettings, self).get_requests_kwargs()
        result.pop('timeout')
        result['verify'] = False
        return result
