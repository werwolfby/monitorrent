import Vue from 'vue'
import Vuex from 'vuex'
import topics from './modules/topics'
import execute from './modules/execute'

Vue.use(Vuex)

const options = {
    modules: {
        topics,
        execute
    }
}

export default new Vuex.Store(options)
export { options }
