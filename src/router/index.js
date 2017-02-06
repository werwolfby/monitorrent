import Vue from 'vue'
import VueMaterial from 'vue-material'
import Router from 'vue-router'
import Root from 'components/Root'

import 'vue-material/dist/vue-material.css'

Vue.use(Router)
Vue.use(VueMaterial)

export default new Router({
  routes: [
    {
      path: '/',
      name: 'Root',
      component: Root
    }
  ]
})
