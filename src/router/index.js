import Vue from 'vue'
import Router from 'vue-router'
import Topics from 'components/Topics/Topics'

import 'vue-material/dist/vue-material.css'

Vue.use(Router)

export default new Router({
    routes: [
        {
            path: '/',
            name: 'Topics',
            component: Topics
        }
    ]
})
