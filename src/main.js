// The Vue build version to load with the `import` command
// (runtime-only or standalone) has been set in webpack.base.conf with an alias.
import Vue from 'vue'
import App from './App'
import router from './router'
import moment from 'moment'
import store from './store'

Vue.filter('formatDate', function (value, format) {
  if (value) {
    return moment(value).format(format || 'DD.MM.YYYY hh:mm:ss')
  }
})

/* eslint-disable no-new */
new Vue({
  el: '#app',
  store,
  router,
  template: '<App/>',
  components: { App }
})
