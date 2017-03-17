import Vue from 'vue'
import Router from 'vue-router'
import Topics from 'components/Topics/Topics'
import Settings from 'components/Settings/Settings'
import SettingsGeneral from 'components/Settings/SettingsGeneral'
import SettingsTrackers from 'components/Settings/SettingsTrackers'
import SettingsNotifiers from 'components/Settings/SettingsNotifiers'
import SettingsClients from 'components/Settings/SettingsClients'
import SettingsAuthentication from 'components/Settings/SettingsAuthentication'
import History from 'components/Settings/History'
import About from 'components/Settings/About'

import 'vue-material/dist/vue-material.css'

Vue.use(Router)

export default new Router({
    routes: [
        {
            path: '/',
            name: 'topics',
            component: Topics
        },
        {
            path: '/settings',
            name: 'settings',
            component: Settings
        },
        {
            path: '/settings/general',
            name: 'settings-general',
            component: SettingsGeneral
        },
        {
            path: '/settings/trackers',
            name: 'settings-trackers',
            component: SettingsTrackers
        },
        {
            path: '/settings/notifiers',
            name: 'settings-notifiers',
            component: SettingsNotifiers
        },
        {
            path: '/settings/clients',
            name: 'settings-clients',
            component: SettingsClients
        },
        {
            path: '/settings/authentication',
            name: 'settings-authentication',
            component: SettingsAuthentication
        },
        {
            path: '/history',
            name: 'history',
            component: History
        },
        {
            path: '/about',
            name: 'about',
            component: About
        }
    ]
})
