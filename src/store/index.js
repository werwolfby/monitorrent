import Vue from 'vue'
import Vuex from 'vuex'
import topics from './modules/topics'

Vue.use(Vuex)

export default new Vuex.Store({
    modules: {
        topics
    }
})
