import Vue from 'vue'
import Router from 'vue-router'
import Topics from 'components/Topics/Topics'
import Settings from 'components/Settings/Settings'

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
        }
    ]
})
