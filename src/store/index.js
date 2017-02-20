import Vue from 'vue'
import Vuex from 'vuex'
import topics from './modules/topics'

Vue.use(Vuex)

const options = {
    modules: {
        topics
    }
}

export default new Vuex.Store(options)
export { options }
