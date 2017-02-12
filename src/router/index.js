import Vue from 'vue'
import VueMaterial from 'vue-material'
import Router from 'vue-router'
import Topics from 'components/Topics/Topics'
import moment from 'moment'

import 'vue-material/dist/vue-material.css'

Vue.use(Router)
Vue.use(VueMaterial)

Vue.material.registerTheme('default', {
  primary: 'blue-grey',
  accent: 'deep-purple',
  warn: 'deep-orange',
  background: 'white'
})

Vue.filter('formatDate', function (value, format) {
  if (value) {
    return moment(value).format(format || 'DD.MM.YYYY hh:mm:ss')
  }
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
