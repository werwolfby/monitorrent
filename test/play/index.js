import 'vue-material/dist/vue-material.css'

import Vue from 'vue'
import Vuex from 'vuex'
import VueMaterial from 'vue-material'
import { formatDate, isNull } from '../../src/filters'

Vue.use(VueMaterial)
Vue.use(Vuex)

Vue.material.registerTheme('default', {
    primary: 'blue-grey',
    accent: 'deep-purple',
    warn: 'deep-orange',
    background: 'white'
})

Vue.filter('formatDate', formatDate)
Vue.filter('isNull', isNull)

const load = requireContext => requireContext.keys().map(requireContext)
load(require.context('./scenarios', true, /.js$/))
