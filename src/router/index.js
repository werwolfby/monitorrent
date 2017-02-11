import Vue from 'vue'
import VueMaterial from 'vue-material'
import Router from 'vue-router'
import Topics from 'components/Topics/Topics'

import 'vue-material/dist/vue-material.css'

Vue.use(Router)
Vue.use(VueMaterial)

Vue.material.registerTheme('default', {
  primary: 'blue-grey',
  accent: 'deep-purple',
  warn: 'deep-orange',
  background: 'white'
})

export default new Router({
  routes: [
    {
      path: '/',
      name: 'Topics',
      component: Topics
    }
  ]
})
