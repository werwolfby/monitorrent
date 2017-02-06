import Vue from 'vue'
import VueMaterial from 'vue-material'
import Router from 'vue-router'
import Topics from 'components/Topics'

import 'vue-material/dist/vue-material.css'

Vue.use(Router)
Vue.use(VueMaterial)

export default new Router({
  routes: [
    {
      path: '/',
      name: 'Topics',
      component: Topics
    }
  ]
})
