<template>
    <div id="app">
        <md-toolbar>
            <h2 class="md-title">
                Monitorrent
                <span class="md-title-caption">v.1.1.2a</span>
            </h2>
            <span style="flex: 1"></span>
            <md-button class="md-icon-button" @click.native="$router.push({name: 'settings'})">
                <md-icon>settings</md-icon>
            </md-button>
            <md-button class="md-icon-button">
                <md-icon>exit_to_app</md-icon>
            </md-button>
        </md-toolbar>

        <div class="mt-content-view">
        <md-whiteframe md-elevation="5">
            <router-view></router-view>
        </md-whiteframe>
        </div>

        <md-snackbar md-position='top right' ref="snackbar" md-duration="4000">
            <span>{{message}}</span>
            <md-button v-if="close" class="md-accent" md-theme="light-blue" @click="$refs.snackbar.close()">Close</md-button>
        </md-snackbar>
    </div>
</template>

<script>
import Vue from 'vue'
import { mapMutations, mapState } from 'vuex'
import VueMaterial from 'vue-material'
import { formatDate, isNull } from './filters'

Vue.use(VueMaterial)

Vue.material.registerTheme('default', {
    primary: 'blue-grey',
    accent: 'deep-purple',
    warn: 'deep-orange',
    background: 'white'
})

Vue.filter('formatDate', formatDate)
Vue.filter('isNull', isNull)

export default {
    name: 'app',
    computed: {
        ...mapState({
            'message': state => state.message,
            'close': state => state.close
        })
    },
    watch: {
        message () {
            if (this.message) {
                this.$refs.snackbar.open()
            }
        }
    },
    mounted () {
        this.$refs.snackbar.$on('close', () => this.clearMessage())
    },
    methods: {
        ...mapMutations({
            'clearMessage': 'clearMessage'
        })
    }
}
</script>

<style>
.md-title-caption {
  font-size: 12px;
  letter-spacing: 0.020em;
}

.mt-content-view {
  margin: auto;
  width: 100%;
  max-width: 1200px;
  box-sizing: border-box;
  padding: 16px;
}

.md-select {
    min-width: 64px !important;
}
</style>
